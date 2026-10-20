import json,os,sys,time,urllib.request,concurrent.futures as cf
B='http://127.0.0.1:8000/plugins/fichas_qwen/call/'
H={'Authorization':'Bearer '+os.environ['RIU_ROUTER_API_KEY'],'Content-Type':'application/json'}
F={'1':'ficha1-modelos','2':'ficha2-dag-codigo','3':'ficha3-frontend','4':'ficha4-workflow-yaiwes'}
NOTXT=('image','tts','realtime','asr')
def post(act,b,t=60):
    r=urllib.request.Request(B+act,data=json.dumps(b).encode(),headers=H)
    return json.load(urllib.request.urlopen(r,timeout=t))
def verdict(res):
    rep=res.get('reply') if isinstance(res,dict) else None
    if rep and str(rep).strip() and not str(rep).startswith('GAP'): return ('PASS',str(rep)[:80].replace(chr(10),' '))
    return ('GAP',(str(rep) if rep else json.dumps(res))[:230].replace(chr(10),' '))
def call(f,m):
    b={'ficha_qwen':f,'message':'Responde solo la palabra OK','sesion':'t'+f+(m or 'sel')}
    if m: b['modelo']=m
    try:
        d=post('chat_async',b); res=d.get('result',d)
        pid=res.get('proceso_id')
        if not pid: return ('GAP',json.dumps(d)[:230])
        t0=time.time()
        while time.time()-t0<300:
            time.sleep(4); d=post('resultado',{'proceso_id':pid}); res=d.get('result',d)
            if isinstance(res,dict) and res.get('estado')!='procesando': return verdict(res)
        return ('GAP','TIMEOUT 300s')
    except Exception as e: return ('FAIL','EXC '+repr(e)[:150])
out=[]
for f in sys.argv[1:]:
    j=json.load(open('plugins/fichas_qwen/fichas/%s.json'%F[f]))
    ms=[m for m in (j.get('modelos') or {}) if not any(x in m for x in NOTXT)] if f in('1','4') else [None]
    with cf.ThreadPoolExecutor(4) as ex: rs=list(ex.map(lambda m:call(f,m),ms))
    for m,(s,t) in zip(ms,rs): print(s,'ficha'+f,m or 'selector',t,flush=True); out.append(s)
print('RESUMEN',{k:out.count(k) for k in set(out)})
sys.exit(0 if set(out)=={'PASS'} else 1)
