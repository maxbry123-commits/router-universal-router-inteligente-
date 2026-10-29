"""Cola CIT-50 autónoma: SQLite transaccional, DAG, permisos, recibos, bitácora.
No contiene el LOOP ni el Watchdog: son módulos SEPARADOS.
Python 3.10+, solo biblioteca estándar.
"""
from __future__ import annotations
import asyncio
import hashlib
import json
import re
import sqlite3
import time
import uuid
from pathlib import Path

RE_ID = re.compile(r'^[a-zA-Z0-9_-]{1,80}$')
TERMINAL = {'succeeded','failed','skipped','cancelled','needs_reconciliation'}
VALID_TYPES = {'model','validation','ricardo','handoff','delay'}

class QueueError(ValueError):
    def __init__(self, message, status=422):
        super().__init__(message)
        self.status = status

def dump(x):
    return json.dumps(x, ensure_ascii=False, separators=(',', ':'), sort_keys=True)

def valid_id(value, field='id'):
    if not isinstance(value, str) or not RE_ID.fullmatch(value):
        raise QueueError(f'{field} inválido')
    return value

def checked_tasks(items):
    if not isinstance(items,list) or not 1 <= len(items) <= 50:
        raise QueueError('Se requieren entre 1 y 50 tareas')
    ids=set(); result=[]
    for i,t in enumerate(items):
        if not isinstance(t,dict):raise QueueError('Tarea no es un objeto')
        tid=valid_id(t.get('id', ''),'task_id')
        if tid in ids:raise QueueError('ID duplicado')
        ids.add(tid)
        kind=t.get('type','model')
        if kind not in VALID_TYPES:raise QueueError('Tipo no autorizado')
        title=t.get('title','');prompt=t.get('prompt','')
        if not isinstance(title,str) or not 1<=len(title)<=150:raise QueueError('Título inválido')
        if not isinstance(prompt,str) or len(prompt)>24000:raise QueueError('Prompt inválido')
        if kind=='model' and not prompt.strip():raise QueueError('Prompt obligatorio')
        deps=t.get('depends_on',[])
        if not isinstance(deps,list) or len(deps)!=len(set(map(str,deps))) or any(not isinstance(d,str) for d in deps):
            raise QueueError('Dependencias inválidas')
        attachments=t.get('attachments',[])
        if not isinstance(attachments,list) or len(attachments)>20 or any(not isinstance(a,str) or not RE_ID.fullmatch(a) for a in attachments):
            raise QueueError('Anclajes: solo IDs existentes, nunca URLs')
        skills=t.get('skills',[])
        if not isinstance(skills,list) or len(skills)>20 or any(not isinstance(x,str) or not re.fullmatch(r'[a-zA-Z0-9_-]{1,80}',x) for x in skills):
            raise QueueError('IDs de reglas/skills inválidos')
        if kind=='ricardo' and (not isinstance(t.get('ops'),dict) or not isinstance(t['ops'].get('ops'),list)):
            raise QueueError('Ricardo requiere meta+ops JSON')
        acc=t.get('acceptance',{})
        if not isinstance(acc,dict) or set(acc)-{'contains','min_chars'}:raise QueueError('acceptance inválido')
        if 'min_chars' in acc and (type(acc['min_chars'])!=int or not 1<=acc['min_chars']<=32000):
            raise QueueError('min_chars inválido')
        if 'contains' in acc and (not isinstance(acc['contains'],str) or not 1<=len(acc['contains'])<=300):
            raise QueueError('contains inválido')
        if kind=='validation' and not deps:raise QueueError('validation requiere dependencias')
        if kind=='delay' and (type(t.get('seconds'))!=int or not 1<=t['seconds']<=86400):
            raise QueueError('seconds fuera de rango')
        result.append({'id':tid,'position':i+1,'title':title,'type':kind,
            'prompt':prompt,'depends_on':deps,'attachments':attachments,
            'model':t.get('model'), 'priority':max(1,min(10,int(t.get('priority',5)))),
            'requires_approval':kind=='ricardo' or bool(t.get('requires_approval',False)),
            'ops':t.get('ops'), 'seconds':t.get('seconds'), 'skills':skills,
            'acceptance':acc})
    positions={t['id']:t for t in result}
    visiting=set();seen=set()
    def visit(i):
        if i in visiting:raise QueueError('DAG con ciclo')
        if i in seen:return
        visiting.add(i)
        for d in positions[i]['depends_on']:
            if d not in positions:raise QueueError('Dependencia inexistente '+str(d))
            visit(d)
        visiting.remove(i);seen.add(i)
    for tid in ids:visit(tid)
    return result

class QueueStore:
    """Single-host SQLite WAL. Guardar archivo DB en volumen persistente."""
    def __init__(self,path):
        self.path=Path(path)
        self.path.parent.mkdir(parents=True,exist_ok=True)
        with self.db() as c:
            c.executescript('''
             CREATE TABLE IF NOT EXISTS queues(
              id TEXT PRIMARY KEY, chat_id TEXT NOT NULL, title TEXT NOT NULL,
              mode TEXT NOT NULL, state TEXT NOT NULL, revision INTEGER NOT NULL, max_calls INTEGER NOT NULL,
              calls INTEGER NOT NULL DEFAULT 0, deadline REAL, created REAL NOT NULL);
             CREATE TABLE IF NOT EXISTS tasks(
              queue_id TEXT NOT NULL, id TEXT NOT NULL, position INTEGER NOT NULL,
              details TEXT NOT NULL, state TEXT NOT NULL, approved INTEGER NOT NULL DEFAULT 0,
              attempts INTEGER NOT NULL DEFAULT 0, due REAL NOT NULL DEFAULT 0,
              lease REAL, output TEXT, receipt_id TEXT,
              PRIMARY KEY(queue_id,id));
             CREATE TABLE IF NOT EXISTS events(
              seq INTEGER PRIMARY KEY AUTOINCREMENT, queue_id TEXT, task_id TEXT,
              event TEXT NOT NULL, data TEXT NOT NULL, at REAL NOT NULL);
             CREATE INDEX IF NOT EXISTS idx_cit50 ON tasks(queue_id,state,due);
            ''')

    from contextlib import contextmanager
    @contextmanager
    def db(self):
        c=sqlite3.connect(self.path, timeout=15,isolation_level=None)
        c.row_factory=sqlite3.Row
        try:
            c.execute('PRAGMA journal_mode=WAL')
            c.execute('PRAGMA busy_timeout=15000')
            yield c
        finally:c.close()

    def ev(self,c,qid,event,data=None,tid=None):
        c.execute('INSERT INTO events(queue_id,task_id,event,data,at) VALUES(?,?,?,?,?)',
                  (qid,tid,event,dump(data or {}),time.time()))

    def create(self,body):
        if not isinstance(body,dict):raise QueueError('JSON inválido')
        tasks=checked_tasks(body.get('tasks',[]))
        chat_id=valid_id(body.get('chat_id','web-general'),'chat_id')
        title=body.get('title','Cola de tareas')
        if not isinstance(title,str) or not 1<=len(title)<=150:raise QueueError('title inválido')
        max_calls=body.get('max_model_calls',80)
        if type(max_calls)!=int or not 1<=max_calls<=1000:raise QueueError('Límite llamadas incorrecto')
        mode=body.get('mode','sequential')
        if mode not in {'sequential','dag'}:raise QueueError('mode inválido')
        qid='cit_'+uuid.uuid4().hex[:20]
        with self.db() as c:
            c.execute('BEGIN IMMEDIATE')
            c.execute('INSERT INTO queues VALUES(?,?,?,?,?,?,?,?,?,?)',
                (qid,chat_id,title,mode,'draft',1,max_calls,0,None,time.time()))
            for t in tasks:
                c.execute('INSERT INTO tasks(queue_id,id,position,details,state) VALUES(?,?,?,?,?)',
                          (qid,t['id'],t['position'],dump(t),'pending'))
            self.ev(c,qid,'queue.created',{'tasks':len(tasks)})
            c.execute('COMMIT')
        return self.get(qid)

    def get(self,qid):
        valid_id(qid)
        with self.db() as c:
            q=c.execute('SELECT * FROM queues WHERE id=?',(qid,)).fetchone()
            if not q:raise QueueError('Cola desconocida',404)
            ts=c.execute('SELECT * FROM tasks WHERE queue_id=? ORDER BY position,id',(qid,)).fetchall()
            return {'queue_id':qid,'chat_id':q['chat_id'],'title':q['title'],
                'status':q['state'],'mode':q['mode'],'revision':q['revision'],'calls':q['calls'],'max_calls':q['max_calls'],
                'deadline':q['deadline'],'tasks':[{**json.loads(t['details']),
                'status':t['state'],'attempts':t['attempts'],'approved':bool(t['approved']),
                'output':json.loads(t['output']) if t['output'] else None,
                'receipt_id':t['receipt_id']} for t in ts]}

    def list(self,chat_id=None):
        if chat_id:valid_id(chat_id,'chat_id')
        with self.db() as c:
            sql='SELECT id,chat_id,title,mode,state,revision,calls FROM queues'
            args=()
            if chat_id:sql+=' WHERE chat_id=?';args=(chat_id,)
            return [dict(r) for r in c.execute(sql+' ORDER BY created DESC LIMIT 100',args)]

    def add_task(self,qid,task,revision):
        data=self.get(qid)
        return self.replace_draft(qid,{'tasks':data['tasks']+[task]},revision)

    def edit_task(self,qid,task_id,updates,revision):
        data=self.get(qid)
        if not isinstance(updates,dict) or set(updates)&{'id','status','approved','output','receipt_id','attempts'}:
            raise QueueError('Intento de modificar estado/ID')
        found=False
        for t in data['tasks']:
            if t['id']==task_id:t.update(updates);found=True
        if not found:raise QueueError('Tarea no existe',404)
        return self.replace_draft(qid,{'tasks':data['tasks']},revision)

    def remove_task(self,qid,task_id,revision):
        data=self.get(qid)
        new=[t for t in data['tasks'] if t['id']!=task_id]
        if len(new)==len(data['tasks']):raise QueueError('Tarea no existe',404)
        return self.replace_draft(qid,{'tasks':new},revision)

    def reorder(self,qid,order,revision):
        data=self.get(qid)
        if not isinstance(order,list):raise QueueError('Orden inválido')
        lookup={t['id']:t for t in data['tasks']}
        if len(order)!=len(lookup) or len(set(order))!=len(order) or set(order)!=set(lookup):
            raise QueueError('Orden incompleto o duplicado')
        return self.replace_draft(qid,{'tasks':[lookup[k] for k in order]},revision)

    def events(self,qid,after=0):
        self.get(qid)
        with self.db() as c:
            return [dict(x) for x in c.execute('SELECT * FROM events WHERE queue_id=? AND seq>? ORDER BY seq LIMIT 250',(qid,max(0,int(after)))).fetchall()]

    def start(self,qid,seconds=3600):
        if type(seconds)!=int or not 60<=seconds<=172800:raise QueueError('Duración 60..172800 s')
        with self.db() as c:
            c.execute('BEGIN IMMEDIATE')
            q=c.execute('SELECT state FROM queues WHERE id=?',(qid,)).fetchone()
            if not q:raise QueueError('Cola desconocida',404)
            if q['state']!='draft':raise QueueError('Solo se inicia borrador',409)
            c.execute('UPDATE queues SET state=?,deadline=? WHERE id=?',('running',time.time()+seconds,qid))
            self.ev(c,qid,'queue.started')
            c.execute('COMMIT')
        return self.get(qid)

    def control(self,qid,action):
        transitions={'pause':{'running':'paused'},'resume':{'paused':'running'},
                     'cancel':{'running':'cancelled','paused':'cancelled'}}
        if action not in transitions:raise QueueError('Acción incorrecta')
        with self.db() as c:
            c.execute('BEGIN IMMEDIATE')
            q=c.execute('SELECT state FROM queues WHERE id=?',(qid,)).fetchone()
            if not q:raise QueueError('Cola desconocida',404)
            nxt=transitions[action].get(q['state'])
            if not nxt:raise QueueError('Transición inválida',409)
            c.execute('UPDATE queues SET state=? WHERE id=?',(nxt,qid));self.ev(c,qid,'queue.'+nxt)
            c.execute('COMMIT')
        return self.get(qid)

    def replace_draft(self,qid,body,revision):
        """Replace/edit/reorder all pending tasks atomically, with revision CAS."""
        ts=checked_tasks(body.get('tasks',[]))
        with self.db() as c:
            c.execute('BEGIN IMMEDIATE')
            row=c.execute('SELECT state,revision FROM queues WHERE id=?',(qid,)).fetchone()
            if not row:raise QueueError('Cola desconocida',404)
            if row['state']!='draft' or row['revision']!=revision:raise QueueError('Edición conflictiva',409)
            c.execute('DELETE FROM tasks WHERE queue_id=?',(qid,))
            for t in ts:
                c.execute('INSERT INTO tasks(queue_id,id,position,details,state) VALUES(?,?,?,?,?)',
                          (qid,t['id'],t['position'],dump(t),'pending'))
            c.execute('UPDATE queues SET revision=revision+1 WHERE id=?',(qid,))
            self.ev(c,qid,'queue.draft_replaced',{'tasks':len(ts),'revision':revision+1})
            c.execute('COMMIT')
        return self.get(qid)

    def approve(self,qid,tid):
        with self.db() as c:
            c.execute('BEGIN IMMEDIATE')
            t=c.execute('SELECT state,details FROM tasks WHERE queue_id=? AND id=?',(qid,tid)).fetchone()
            if not t:raise QueueError('Tarea desconocida',404)
            if t['state']!='pending' or not json.loads(t['details'])['requires_approval']:
                raise QueueError('Aprobación no aplicable',409)
            c.execute('UPDATE tasks SET approved=1 WHERE queue_id=? AND id=?',(qid,tid))
            self.ev(c,qid,'approval.granted',{},tid);c.execute('COMMIT')
        return self.get(qid)

    def count_call(self,qid):
        with self.db() as c:
            c.execute('BEGIN IMMEDIATE')
            n=c.execute('UPDATE queues SET calls=calls+1 WHERE id=? AND state=? AND calls<max_calls',
                        (qid,'running')).rowcount
            if n!=1:c.execute('ROLLBACK');raise QueueError('Presupuesto o estado bloqueado',429)
            c.execute('COMMIT')

    def claim(self):
        """Un solo worker lógico; no repetir acciones inciertas tras reinicio."""
        with self.db() as c:
            c.execute('BEGIN IMMEDIATE')
            now=time.time()
            for q in c.execute("SELECT * FROM queues WHERE state='running' ORDER BY created").fetchall():
                qid=q['id']
                if q['deadline'] and q['deadline']<now:
                    c.execute("UPDATE queues SET state='expired' WHERE id=?",(qid,));self.ev(c,qid,'queue.expired');continue
                ts=c.execute('SELECT * FROM tasks WHERE queue_id=? ORDER BY position,id',(qid,)).fetchall()
                running=[x for x in ts if x['state']=='running']
                for t in running:
                    if (t['lease'] or 0)<now:
                        c.execute("UPDATE tasks SET state='needs_reconciliation',lease=NULL WHERE queue_id=? AND id=?",(qid,t['id']))
                        self.ev(c,qid,'task.lease_expired',{'side_effect_may_have_occurred':True},t['id'])
                if running:continue
                done={t['id'] for t in ts if t['state']=='succeeded'}
                failed={t['id'] for t in ts if t['state'] in {'failed','needs_reconciliation','skipped'}}
                candidates=ts if q['mode']=='sequential' else sorted(ts,key=lambda x:(json.loads(x['details'])['priority'],x['position']))
                for t in candidates:
                    if t['state']!='pending':continue
                    item=json.loads(t['details'])
                    if any(d in failed for d in item['depends_on']):
                        c.execute("UPDATE tasks SET state='skipped' WHERE queue_id=? AND id=?",(qid,t['id']))
                        self.ev(c,qid,'task.skipped',{'because':'failed_dependency'},t['id']);continue
                    if not set(item['depends_on']).issubset(done) or t['due']>now:continue
                    if item['requires_approval'] and not t['approved']:continue
                    if any(x['position']<t['position'] and x['state']!='succeeded' for x in ts) and q['mode']=='sequential':
                        continue
                    # serial per queue: exactly one claim
                    n=c.execute("UPDATE tasks SET state='running',lease=?,attempts=attempts+1 WHERE queue_id=? AND id=? AND state='pending'",
                                (now+300,qid,t['id'])).rowcount
                    if n!=1:continue
                    self.ev(c,qid,'task.started',{'attempts':t['attempts']+1},t['id'])
                    c.execute('COMMIT')
                    qdata=self.get(qid);task=next(x for x in qdata['tasks'] if x['id']==t['id'])
                    return qdata,task
                cur=[r['state'] for r in c.execute('SELECT state FROM tasks WHERE queue_id=?',(qid,)).fetchall()]
                if cur and all(x in TERMINAL for x in cur):
                    nxt='completed' if all(x=='succeeded' for x in cur) else 'failed'
                    c.execute('UPDATE queues SET state=? WHERE id=?',(nxt,qid));self.ev(c,qid,'queue.'+nxt)
            c.execute('COMMIT');return None

    def complete(self,qid,tid,payload,*,ok=True,retry=False,delay=0):
        data=dump(payload)
        if len(data)>100000:raise QueueError('Resultado demasiado grande')
        with self.db() as c:
            c.execute('BEGIN IMMEDIATE')
            q=c.execute('SELECT state FROM queues WHERE id=?',(qid,)).fetchone()
            t=c.execute('SELECT state FROM tasks WHERE queue_id=? AND id=?',(qid,tid)).fetchone()
            if not q or not t or t['state']!='running':c.execute('ROLLBACK');return False
            state='pending' if retry else 'succeeded' if ok else 'failed'
            if q['state'] in {'cancelled','expired'}:state='cancelled'
            receipt=hashlib.sha256((qid+tid+data).encode()).hexdigest()
            c.execute('UPDATE tasks SET state=?,output=?,receipt_id=?,lease=NULL,due=? WHERE queue_id=? AND id=?',
                      (state,data,receipt,time.time()+delay if retry else 0,qid,tid))
            self.ev(c,qid,'task.'+state,{'receipt_id':receipt,'verification':payload.get('verification','NO_VERIFICADO')},tid)
            if state=='failed':
                c.execute("UPDATE queues SET state='failed' WHERE id=?",(qid,));self.ev(c,qid,'queue.failed',{'task_id':tid})
            c.execute('COMMIT')
        return True

class QueueWorker:
    """Tareas son unidades breves; callbacks establecidos por el host, no por la IA."""
    def __init__(self,store:QueueStore, model_call, ricardo_call=None, interval=1):
        self.store=store;self.model_call=model_call;self.ricardo_call=ricardo_call
        self.interval=interval;self.running=False

    async def step(self):
        claimed=await asyncio.to_thread(self.store.claim)
        if not claimed:return False
        q,t=claimed;tid=t['id'];qid=q['queue_id']
        try:
            if t['type']=='model':
                await asyncio.to_thread(self.store.count_call,qid)
                value=await asyncio.wait_for(self.model_call(q,t),timeout=240)
                if not isinstance(value,dict) or not isinstance(value.get('texto'),str) or not value.get('texto'):
                    raise QueueError('Modelo no entregó texto comprobable')
                if value.get('finish_reason') in {'length','content_filter'}:
                    raise QueueError('Respuesta incompleta')
                acceptance=t.get('acceptance') or {}
                if not acceptance:raise QueueError('Falta acceptance verificable para texto del modelo')
                if set(acceptance)-{'min_chars','contains'}:raise QueueError('Acceptance desconocido')
                if len(value['texto'])<int(acceptance.get('min_chars',1)):raise QueueError('Respuesta inferior al mínimo')
                if 'contains' in acceptance and str(acceptance['contains']) not in value['texto']:
                    raise QueueError('Texto obligatorio no encontrado')
                result={'texto':value['texto'][:32000], 'finish_reason':value.get('finish_reason'),
                        'verification':'PASS', 'checks':['text_shape','explicit_acceptance'],
                        'execution':'existing_chat', 'semantic_correctness':'NO_VERIFICADO'}
            elif t['type']=='ricardo':
                if not t['approved'] or self.ricardo_call is None:raise QueueError('Ricardo sin aprobación/ejecutor')
                result=await asyncio.wait_for(self.ricardo_call(q,t),timeout=240)
                if not isinstance(result,dict) or result.get('verified') is not True:
                    raise QueueError('Motor Ricardo no verificó resultado')
                result={**result,'verification':'PASS'}
            elif t['type']=='delay':
                if t['attempts']==1:
                    await asyncio.to_thread(self.store.complete,qid,tid,{'reason':'delay'},ok=False,retry=True,delay=t['seconds'])
                    return True
                result={'elapsed':True,'verification':'PASS'}
            elif t['type']=='validation':
                dep=[x for x in q['tasks'] if x['id'] in t['depends_on']]
                if not dep or not all(x['status']=='succeeded' and x['receipt_id'] for x in dep):
                    raise QueueError('Faltan recibos reales de dependencias')
                result={'verified_dependencies':[x['receipt_id'] for x in dep], 'verification':'PASS'}
            elif t['type']=='handoff':
                result={'prior_receipts':{x['id']:x['receipt_id'] for x in q['tasks'] if x['receipt_id']},
                        'verification':'PASS'}
            else:raise QueueError('Tipo no implementado')
            await asyncio.to_thread(self.store.complete,qid,tid,result)
        except asyncio.CancelledError:raise
        except Exception as e:
            await asyncio.to_thread(self.store.complete,qid,tid,
                {'reason':str(e)[:160] if isinstance(e,QueueError) else type(e).__name__,
                 'verification':'FAIL'},ok=False)
        return True

    async def run(self):
        self.running=True
        while self.running:
            try:
                if not await self.step():await asyncio.sleep(self.interval)
            except asyncio.CancelledError:raise
            except Exception:await asyncio.sleep(self.interval)

    def stop(self):self.running=False
