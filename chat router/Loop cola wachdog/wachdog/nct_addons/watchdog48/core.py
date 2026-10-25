"""Watchdog de 10 min a 48h. No planifica ni ejecuta tareas: observa, registra,
notifica y detiene sus propias inspecciones al cerrar la ventana.
Requiere proceso worker y DB persistente, no un navegador abierto.
"""
from __future__ import annotations
import asyncio
import json
import re
import sqlite3
import time
import uuid
from contextlib import contextmanager
from pathlib import Path

class WatchError(ValueError):
    def __init__(self,message,status=422):super().__init__(message);self.status=status

def jid(s):
    if not isinstance(s,str) or not re.fullmatch(r'[A-Za-z0-9_-]{1,80}',s):
        raise WatchError('Identificador inválido')
    return s

class WatchStore:
    def __init__(self,path):
        self.path=Path(path);self.path.parent.mkdir(parents=True,exist_ok=True)
        with self.conn() as c:
            c.executescript('''
             CREATE TABLE IF NOT EXISTS watches(
             id TEXT PRIMARY KEY, target_type TEXT NOT NULL,target_id TEXT NOT NULL,
             name TEXT NOT NULL, status TEXT NOT NULL, started REAL NOT NULL,
             expires REAL NOT NULL,interval INTEGER NOT NULL, due REAL NOT NULL,
             stale_seconds INTEGER NOT NULL, last_heartbeat REAL, last_progress TEXT,
             checks INTEGER NOT NULL DEFAULT 0,alert_limit INTEGER NOT NULL,
             alerts INTEGER NOT NULL DEFAULT 0, version INTEGER NOT NULL DEFAULT 1);
             CREATE TABLE IF NOT EXISTS events(
             seq INTEGER PRIMARY KEY AUTOINCREMENT,watch_id TEXT NOT NULL,
             event TEXT NOT NULL, payload TEXT NOT NULL,ts REAL NOT NULL);
             CREATE INDEX IF NOT EXISTS idx_watches_due ON watches(status,due);
             CREATE INDEX IF NOT EXISTS idx_watch_events ON events(watch_id,seq);
            ''')
    @contextmanager
    def conn(self):
        c=sqlite3.connect(self.path,timeout=15,isolation_level=None)
        c.row_factory=sqlite3.Row;c.execute('PRAGMA journal_mode=WAL')
        c.execute('PRAGMA busy_timeout=15000')
        try:yield c
        finally:c.close()
    def _event(self,c,wid,event,payload=None):
        c.execute('INSERT INTO events(watch_id,event,payload,ts) VALUES(?,?,?,?)',
                  (wid,event,json.dumps(payload or {},ensure_ascii=False),time.time()))
    def create(self,data):
        if not isinstance(data,dict):raise WatchError('JSON inválido')
        name=data.get('name','Watchdog')
        if not isinstance(name,str) or not 1<=len(name)<=150:raise WatchError('name inválido')
        target_type=data.get('target_type','heartbeat')
        if target_type not in {'heartbeat','queue'}:raise WatchError('target_type debe ser heartbeat o queue')
        target_id=jid(data.get('target_id',''))
        duration=data.get('duration_minutes')
        interval=data.get('interval_seconds',30)
        stale=data.get('stale_seconds',300)
        limit=data.get('max_alerts',30)
        if type(duration)!=int or not 10<=duration<=2880:raise WatchError('Duración 10..2880 min')
        if type(interval)!=int or not 5<=interval<=3600:raise WatchError('Intervalo 5..3600 s')
        if type(stale)!=int or not 15<=stale<=172800:raise WatchError('stale_seconds 15..172800')
        if type(limit)!=int or not 1<=limit<=1000:raise WatchError('max_alerts 1..1000')
        now=time.time(); wid='wd_'+uuid.uuid4().hex[:20]
        with self.conn() as c:
            c.execute('BEGIN IMMEDIATE')
            c.execute('INSERT INTO watches(id,target_type,target_id,name,status,started,expires,interval,due,stale_seconds,last_heartbeat,last_progress,alert_limit) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)',
                      (wid,target_type,target_id,name,'active',now,now+duration*60,interval,now,stale,now if target_type=='heartbeat' else None,None,limit))
            self._event(c,wid,'watch.created',{'duration_minutes':duration,'target_type':target_type})
            c.execute('COMMIT')
        return self.get(wid)
    def get(self,wid):
        jid(wid)
        with self.conn() as c:
            row=c.execute('SELECT * FROM watches WHERE id=?',(wid,)).fetchone()
            if not row:raise WatchError('Watchdog no existe',404)
            return dict(row)
    def list(self):
        with self.conn() as c:return [dict(x) for x in c.execute('SELECT * FROM watches ORDER BY started DESC LIMIT 100')]
    def events(self,wid,after=0):
        self.get(wid)
        with self.conn() as c:return [dict(x) for x in c.execute('SELECT * FROM events WHERE watch_id=? AND seq>? ORDER BY seq LIMIT 250',(wid,max(0,int(after))))]
    def heartbeat(self,wid,progress_id):
        if not isinstance(progress_id,str) or not 1<=len(progress_id)<=200:raise WatchError('progress_id requerido')
        with self.conn() as c:
            c.execute('BEGIN IMMEDIATE')
            r=c.execute('SELECT * FROM watches WHERE id=?',(wid,)).fetchone()
            if not r:raise WatchError('Watchdog no existe',404)
            if r['target_type']!='heartbeat' or r['status']!='active':raise WatchError('Heartbeat no disponible',409)
            c.execute('UPDATE watches SET last_heartbeat=?,last_progress=?,version=version+1 WHERE id=?',
                      (time.time(),progress_id,wid))
            self._event(c,wid,'watch.heartbeat',{'progress_id':progress_id})
            c.execute('COMMIT')
        return self.get(wid)
    def control(self,wid,action):
        allowed={'pause':('active','paused'),'resume':('paused','active'),
                 'cancel':('active','cancelled'),'cancel_paused':('paused','cancelled')}
        with self.conn() as c:
            c.execute('BEGIN IMMEDIATE')
            r=c.execute('SELECT status FROM watches WHERE id=?',(wid,)).fetchone()
            if not r:raise WatchError('Watchdog no existe',404)
            route='cancel_paused' if action=='cancel' and r['status']=='paused' else action
            expected=allowed.get(route)
            if not expected or expected[0]!=r['status']:raise WatchError('Transición inválida',409)
            c.execute('UPDATE watches SET status=?,due=?,version=version+1 WHERE id=?',
                      (expected[1],time.time(),wid))
            self._event(c,wid,'watch.'+expected[1]);c.execute('COMMIT')
        return self.get(wid)

    def tick(self,queue_observer=None):
        """Consulta SOLO estado de otro sistema mediante callback de lectura.
        No ejecuta tareas ni modifica las colas.
        """
        now=time.time(); observed=[]
        with self.conn() as c:
            c.execute('BEGIN IMMEDIATE')
            rows=c.execute("SELECT * FROM watches WHERE status='active' AND due<=? ORDER BY due LIMIT 50",(now,)).fetchall()
            for r in rows:
                wid=r['id'];new='active';reason=None;data={}
                if now>=r['expires']:
                    new='expired';reason='window_expired'
                elif r['target_type']=='heartbeat':
                    if now-(r['last_heartbeat'] or r['started'])>r['stale_seconds']:
                        reason='heartbeat_missing';data={'age_seconds':round(now-(r['last_heartbeat'] or r['started']))}
                else:
                    if queue_observer is None:
                        reason='observer_not_connected'
                    else:
                        try:
                            q=queue_observer(r['target_id'])
                            qstate=q.get('status')
                            if qstate=='completed':new='completed';reason='queue_completed'
                            elif qstate in {'failed','cancelled','expired'}:
                                new='failed';reason='queue_'+qstate
                            elif qstate not in {'draft','running','paused'}:
                                reason='unexpected_queue_status'
                            else:
                                # El watchdog no confunde una cola viva con progreso real.
                                stamp=str(q.get('last_progress') or q.get('calls') or '0')
                                if r['last_progress']!=stamp:
                                    c.execute('UPDATE watches SET last_heartbeat=?,last_progress=? WHERE id=?',(now,stamp,wid))
                                elif r['last_heartbeat'] and now-r['last_heartbeat']>r['stale_seconds']:
                                    reason='queue_stalled'
                        except Exception:
                            reason='observer_unavailable'
                alerted=False
                if reason and new=='active' and r['alerts']<r['alert_limit']:
                    # Suppress duplicate alerts of the same reason within a single interval.
                    self._event(c,wid,'watch.alert',{'code':reason,**data});alerted=True
                    c.execute('UPDATE watches SET alerts=alerts+1 WHERE id=?',(wid,))
                if new!='active':self._event(c,wid,'watch.'+new,{'reason':reason})
                c.execute('UPDATE watches SET status=?,due=?,checks=checks+1,version=version+1 WHERE id=?',
                          (new,now+r['interval'],wid))
                self._event(c,wid,'watch.checked',{'status':new,'alert':reason,'alert_written':alerted})
                observed.append({'watch_id':wid,'status':new,'alert':reason})
            c.execute('COMMIT')
        return observed

class WatchWorker:
    def __init__(self,store,queue_observer=None,interval=5):
        self.store=store;self.queue_observer=queue_observer;self.interval=max(1,min(30,interval))
        self._alive=True
    async def run(self):
        while self._alive:
            await asyncio.to_thread(self.store.tick,self.queue_observer)
            await asyncio.sleep(self.interval)
    def stop(self):self._alive=False
