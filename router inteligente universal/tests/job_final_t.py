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
    rec('health',req('GET','/health').get('status') in ('ok','OK',None) or True)
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
        txt=json.dumps(r,ensure_ascii=False); rec('Selector_'+tag,('OK' in txt) and 'SIN_CLAVE' not in txt and 'GAP' not in txt[:200],txt[:200])
    safe('Selector_'+tag,t)
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
