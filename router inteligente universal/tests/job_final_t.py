import json,os,sys,time,subprocess,shutil,urllib.request,uuid
U='http://127.0.0.1:8000'; K=os.environ['RIU_ROUTER_API_KEY']
H={'Authorization':'Bearer '+K,'Content-Type':'application/json'}
R={}
def req(m,p,b=None,t=120):
    r=urllib.request.Request(U+p,data=json.dumps(b).encode() if b is not None else None,headers=H,method=m)
    return json.load(urllib.request.urlopen(r,timeout=t))
def rec(k,ok,d=''):
    R[k]='PASS' if ok else 'FAIL'; print(k,R[k],str(d)[:200].replace('\n',' '),flush=True)
def safe(k,f):
    try: f()
    except Exception as e: rec(k,False,'EXC '+repr(e))
# P6 preflight
def pre():
    h=req('GET','/health'); rec('health',isinstance(h,dict) and h.get('status') in ('ok','OK'),h)
    s=req('GET','/chat/storage'); h=s.get('hf_bucket',{}); rec('storage_cfg',s.get('data_dir')=='/data' and h.get('configured') and h.get('write_token'),{'data_dir':s.get('data_dir'),'bucket':h.get('configured'),'wt':h.get('write_token')})
    m=req('GET','/memoria/health'); rec('memoria_health','CONNECTED' in json.dumps(m).upper() or m.get('status') in ('OK','ok'),m)
safe('preflight',pre)
# P7/P8 fichas (team-qwen = ficha 1 con modelo del selector)
for name,args in (('Ficha1+TeamQwen',['1']),('Ficha4',['4']),('Ficha2y3',['2','3'])):
    p=subprocess.run([sys.executable,'tests/job_fichas_hf.py']+args,capture_output=True,text=True,timeout=1500)
    out=p.stdout[-1500:]; print(name,out,flush=True)
    rec(name,p.returncode==0 and 'GOVERNANCE_NO_PERSISTIDO' not in out,out[-200:])

def proceso(plugin,act,b):
    d=req('POST','/plugins/%s/call/%s'%(plugin,act),b); res=d.get('result',d); pid=res.get('proceso_id')
    if not pid: return res
    t0=time.time()
    while time.time()-t0<240:
        time.sleep(4); r=req('POST','/plugins/%s/call/resultado'%plugin,{'proceso_id':pid}); r=r.get('result',r)
        if isinstance(r,dict) and r.get('estado')!='procesando': return r
    return {'error':'TIMEOUT'}
for tag,fid in (('Nvidia','nv-glm-5-3'),('Groq','groq-qwen-3-8')):
    def t(tag=tag,fid=fid):
        r=proceso('puente_chat','chat_async',{'message':'Responde solo la palabra OK','ficha':fid,'model':fid,'provider':'nvidia' if tag=='Nvidia' else 'groq','sesion':'ng'+tag,'max_tokens':20})
        txt=json.dumps(r,ensure_ascii=False); c=((r.get('choices') or [{}])[0].get('message') or {}).get('content') if isinstance(r,dict) else None; rec('Selector_'+tag,bool(c or r.get('reply')) and 'SIN_CLAVE' not in txt and not r.get('error'),txt[:200])
    safe('Selector_'+tag,t)

# P10/P11 Constitucion + anclaje por HTTP (misma ruta que el chat: fichas_qwen/chat_async con gobernanza+constitucion+anclados)
import base64,glob
def subir(nombre,texto,ses):
    return req('POST','/plugins/puente_chat/call/subir',{'nombre':nombre,'datos_b64':base64.b64encode(texto.encode()).decode(),'tipo':'text/markdown','sesion':ses})
def en_indices(marca):
    n=0
    for d in ('/data/indices/graphiti','/data/indices/graphify'):
        for f in glob.glob(d+'/**/*',recursive=True):
            try:
                if os.path.isfile(f) and marca.encode() in open(f,'rb').read(): n+=1
            except Exception: pass
    return n
def chat_q(ses,extra):
    b={'message':'Responde solo la palabra OK','ficha_qwen':'1','modelo':'ficha-qwen38flash','sesion':ses}; b.update(extra)
    return proceso('fichas_qwen','chat_async',b)
MC='CM'+uuid.uuid4().hex[:10]; MA='AM'+uuid.uuid4().hex[:10]; SES='sf'+uuid.uuid4().hex[:6]
def const():
    subir('const-test.md','# Constitucion de prueba\nMARCA '+MC,SES)
    r=chat_q(SES,{'gobernanza':{'enabled':True},'constitucion':{'texto':'Regla de prueba '+MC,'anclados':['const-test.md']}})
    txt=json.dumps(r,ensure_ascii=False); bad=any(e in txt for e in ('CONSTITUTION_INVALID','GOVERNANCE_NO_PERSISTIDO','CONSTITUTION_CHANGED'))
    rec('Constitution_http',(not bad) and bool(r.get('reply') or r.get('estado')) ,txt[:200])
    time.sleep(15); rec('Constitution_no_en_graphiti_graphify',en_indices(MC)==0,'archivos con marca=%d'%en_indices(MC))
safe('Constitution_http',const)
def ancla():
    subir('anc-test.md','# Plan\nEl Harness usa puente_chat. MARCA '+MA,SES)
    chat_q(SES,{}); time.sleep(10); rec('Anchor_sin_anclar_no_graphiti',en_indices(MA)==0,'archivos con marca=%d'%en_indices(MA))
    r=chat_q(SES,{'anclados':['anc-test.md']}); time.sleep(40)
    n=en_indices(MA); rec('Anchor_Graphiti_indexa',n>0,'archivos con marca=%d | %s'%(n,json.dumps(r,ensure_ascii=False)[:120]))
safe('Anchor_Graphiti',ancla)
# P12 memoria
mk='MK'+uuid.uuid4().hex[:10]
def mem():
    req('POST','/memoria/save',{'scope':'final:test','key':'marker','data':{'v':mk}})
    rec('memoria_load',mk in json.dumps(req('GET','/memoria/load?scope=final:test&key=marker')))
    rec('memoria_search',mk in json.dumps(req('GET','/memoria/search?scope=final:test&query='+mk)))
safe('memoria',mem)
def sync():
    d=req('POST','/chat/storage/sync',{},t=900); print('sync',json.dumps(d)[:300]); rec('storage_sync',not d.get('error') and d.get('ok',True) is not False,d)
safe('storage_sync',sync)
# cold restore
def cold():
    subprocess.run('kill $(cat /tmp/uv.pid); sleep 3',shell=True)
    for p in ('/data/riu_chat.sqlite3','/data/docs','/data/indices/graphiti','/data/indices/graphify'):
        shutil.rmtree(p,ignore_errors=True) if os.path.isdir(p) else (os.path.exists(p) and os.remove(p))
    subprocess.run('bash /tmp/start.sh',shell=True)
    req('GET','/chat/storage',t=900)
    rec('cold_restore',mk in json.dumps(req('GET','/memoria/load?scope=final:test&key=marker')))
safe('cold_restore',cold)
print('RESUMEN',json.dumps(R))
sys.exit(0 if all(v=='PASS' for v in R.values()) else 1)
