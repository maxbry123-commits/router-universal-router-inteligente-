import json,time,urllib.request,sys,uuid
B='https://riu-jev-bridge.vercel.app/plugins/puente_chat/call'
def post(p,b,to=30):
    r=urllib.request.Request(B+p,json.dumps(b).encode(),{'Content-Type':'application/json'})
    with urllib.request.urlopen(r,timeout=to) as x: return json.load(x)
def ask(msg,fq='2',fast=False,model='nv-nemotron-super',limit=400):
    ses='web-gbx-'+uuid.uuid4().hex[:10]
    body={'model':model,'messages':[{'role':'user','content':msg}],'max_tokens':0,'fast_reply':fast,'sesion':ses}
    if fq: body.update({'plugin':'fichas_qwen','ficha_qwen':fq,'modelo':'','task_type':'chat'})
    else: body['model']='ask-consil-factory'
    t=time.time(); e=post('/chat_async',body); res=e.get('result') or {}
    pid=res.get('proceso_id')
    while res.get('estado')=='procesando':
        if time.time()-t>limit: return {'error':'TIMEOUT','ses':ses,'s':time.time()-t}
        time.sleep(1)
        try: res=post('/resultado',{'proceso_id':pid},20).get('result') or {}
        except Exception as x: res={'estado':'procesando'}
    txt=((res.get('choices') or [{}])[0].get('message') or {}).get('content') or res.get('reply') or ''
    return {'ses':ses,'pid':pid,'s':round(time.time()-t,3),'txt':txt,'error':res.get('error'),'path':res.get('execution_path'),'traza':[(t.get('nodo'),t.get('modelo'),t.get('ok')) for t in (res.get('traza') or [])]}
if __name__=='__main__':
    r=ask(sys.argv[1],sys.argv[2] if len(sys.argv)>2 else '2',len(sys.argv)>3 and sys.argv[3]=='fast')
    print(json.dumps(r,ensure_ascii=False)[:3000])
