import json,os,sys,time,subprocess,urllib.request,uuid
U='http://127.0.0.1:8000'; K=os.environ['RIU_ROUTER_API_KEY']; H={'Authorization':'Bearer '+K,'Content-Type':'application/json'}
R={}
def req(m,p,b=None,t=300):
    r=urllib.request.Request(U+p,data=json.dumps(b).encode() if b is not None else None,headers=H,method=m); return json.load(urllib.request.urlopen(r,timeout=t))
def rec(k,ok,d=''):
    R[k]='PASS' if ok else 'FAIL'; print(k,R[k],str(d)[:300].replace(chr(10),' '),flush=True)
MK='MARCA_GRAPHITI_'+uuid.uuid4().hex[:8]; SHA='a'*64; SNAP='snap-test-1'; SC='test-graphiti-final'
def restart(extra=''):
    subprocess.run('kill $(cat /tmp/uv.pid); sleep 3',shell=True); subprocess.run(extra+' bash /tmp/start.sh',shell=True)
try:
    d=req('POST','/memoria/save',{'scope':SC,'key':'g1','data':{'text':MK,'source_id':'archivo-final.md','source_sha256':SHA,'source_snapshot_id':SNAP}})
    txt=json.dumps(d); rec('G1_write','SAVED' in txt and 'GAP_WRITE' not in txt,txt)
    time.sleep(5); s=req('GET','/memoria/search?scope=%s&query=%s'%(SC,MK)); st=json.dumps(s)
    rec('G2_search',MK in st,st)
    rec('G2_proveniencia',('archivo-final.md' in st) and (SHA in st) and (SNAP in st),st[:200])
    restart(); s=req('GET','/memoria/search?scope=%s&query=%s'%(SC,MK)); st=json.dumps(s); rec('G3_reinicio',MK in st,st)
    restart('RIU_FICHA4_URL=http://127.0.0.1:9/plugins/fichas_qwen/call/llm'); d=req('POST','/memoria/save',{'scope':SC,'key':'g4','data':{'text':'CORTE_'+MK}}); txt=json.dumps(d)
    rec('G4_corte_ficha4','GAP_FICHA4_HTTP' in txt,txt)
    restart()
except Exception as e: rec('GRAPHITI_EXC',False,repr(e))
print('RESUMEN',json.dumps(R)); sys.exit(0 if all(v=='PASS' for v in R.values()) else 1)
