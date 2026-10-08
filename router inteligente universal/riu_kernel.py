"""HF-only Router recovery. Keeps the existing Router and plugins; no models in this supervisor."""
import os,json,time,io,tarfile,pathlib,sys,base64,gzip,urllib.request,urllib.error,urllib.parse,subprocess
from huggingface_hub import HfApi,HfFileSystem
NS="COMAND-CENTER-1"
BASE="buckets/"+NS+"/yaiwes-memoria-storage/router-inteligente-universal"
FLAG="router inteligente universal/LIVE_URL.json"
REPO="maxbry123-commits/router-universal-router-inteligente-"
def fs(): return HfFileSystem(token=os.environ["HF_TOKEN"],skip_instance_cache=True)
def read(rel):
    try:return json.loads(fs().cat_file(BASE+"/"+rel))
    except Exception:return {}
def write(rel,d):fs().pipe_file(BASE+"/"+rel,json.dumps(d,ensure_ascii=False).encode())
def request(method,url,key=None,data=None):
    headers={"User-Agent":"yaiwes-kernel","Content-Type":"application/json"}
    if key:headers["Authorization"]="Bearer "+key
    req=urllib.request.Request(url,data=json.dumps(data).encode() if data is not None else None,headers=headers,method=method)
    with urllib.request.urlopen(req,timeout=30) as r:return json.load(r)
def publish(reg):
    write("control/router-current.json",reg)
    apiurl="https://api.github.com/repos/"+REPO+"/contents/"+urllib.parse.quote(FLAG,safe="/")
    key=os.environ["GITHUB_PERSONAL_ACCESS_TOKEN"]
    old={}
    try:old=request("GET",apiurl+"?ref=main",key)
    except urllib.error.HTTPError as e:
        if e.code!=404:raise
    value={"LIVE_URL":reg["url"],"job_id":reg["job_id"],"flavor":reg["flavor"],"updated":time.time(),"auth":"X-API-Key","harnessUrl":reg["url"]+"/plugins/puente_chat/call"}
    data={"message":"Update active HF Router address [skip ci]","branch":"main","content":base64.b64encode(json.dumps(value,indent=2).encode()).decode()}
    if old.get("sha"):data["sha"]=old["sha"]
    request("PUT",apiurl,key,data)
def healthy(url):
    try:
        request("GET",url+"/health")
        return True
    except Exception:return False
def hydrate():
    tar=tarfile.open(fileobj=io.BytesIO(fs().cat_file(BASE+"/codigo/router-bundle.tar.gz")),mode="r:gz")
    tar.extractall("/tmp/kernel-bank",filter="data")
    sys.path.insert(0,"/tmp/kernel-bank/router inteligente universal/Banco de claves")
    from secret_bank.vault import Vault
    p=pathlib.Path("/tmp/kernel-vault.db")
    p.write_bytes(gzip.decompress(base64.b64decode(fs().cat_file(BASE+"/banco/vault.db.gz.b64"))))
    v=Vault(p).unlock(os.environ["RIU_VAULT_PASSPHRASE"])
    os.environ["HF_TOKEN"]=v.get_secret("huggingface/token-1-new")
    os.environ["HF_CONTROL_JOBS_TOKEN"]=os.environ["HF_TOKEN"]
    os.environ["GITHUB_PERSONAL_ACCESS_TOKEN"]=v.get_secret("github/director-full")
    os.environ["RIU_ROUTER_API_KEY"]=v.get_secret("router/runtime-admin-32gb")
    os.environ["RIU_DIRECTOR_KEY_HASH"]=v.get_secret("router/runtime-director-hash")
    keys={}
    for r in v.list():
        if r["enabled"] and r["provider"]=="router" and "hash" not in r["account"]:
            try:keys[v.get_secret(r["credential_ref"])]= "chat-ui" if "chat-ui" in r["account"] else r["account"]
            except Exception:pass
    os.environ["RIU_AGENT_API_KEYS"]=json.dumps(keys)
    os.environ["RIU_AGENT_API_KEYS_2"]="{}"
    os.environ["RIU_PUBLIC_CHAT_KEY"]=v.get_secret("router/chat-ui-director")
def command():
    return ["bash","-lc","set -e\npip install -q huggingface_hub cryptography httpx 'uvicorn[standard]' fastapi pydantic psutil mcp beautifulsoup4\npython - <<'PY'\nimport os,io,tarfile\nfrom huggingface_hub import HfFileSystem\nf=HfFileSystem(token=os.environ['HF_TOKEN'])\nb='buckets/COMAND-CENTER-1/yaiwes-memoria-storage/router-inteligente-universal'\ntarfile.open(fileobj=io.BytesIO(f.cat_file(b+'/codigo/router-bundle.tar.gz')),mode='r:gz').extractall('/app',filter='data')\nimport base64,gzip\nvp,vs=os.environ.get('RIU_VAULT_PATH'),os.environ.get('RIU_VAULT_SOURCE')\nif vp and vs:\n    os.makedirs(os.path.dirname(vp),exist_ok=True)\n    open(vp,'wb').write(gzip.decompress(base64.b64decode(f.cat_file(vs))))\nPY\ncd '/app/router inteligente universal'\npython riu_kernel.py --watch &\nexec uvicorn public_chat_app:app --host 0.0.0.0 --port 8000 --timeout-keep-alive 120"]
def launch():
    hydrate()
    secret_names=["HF_TOKEN","HF_CONTROL_JOBS_TOKEN","GITHUB_PERSONAL_ACCESS_TOKEN","RIU_VAULT_PASSPHRASE","RIU_ROUTER_API_KEY","RIU_AGENT_API_KEYS","RIU_AGENT_API_KEYS_2","RIU_DIRECTOR_KEY_HASH","RIU_PUBLIC_CHAT_KEY"]
    env={"HF_BUCKET_ID":NS+"/yaiwes-memoria-storage","RIU_DATA_DIR":"/tmp/riu-data","RIU_VAULT_PATH":"/tmp/riu-data/riu_vault.db","RIU_VAULT_SOURCE":BASE+"/banco/vault.db.gz.b64","RIU_VAULT_PROVIDERS_SOURCE":BASE+"/banco/providers.json","RIU_AUTOSYNC_SECONDS":"60","RIU_CHAT_ALLOW_PROVIDER_LIVE":"1","RIU_G2_GROQ_MODEL":"qwen/qwen3.8-27b","RIU_CODE_BUNDLE":BASE+"/codigo/router-bundle.tar.gz","RIU_ROOT":"router-inteligente-universal","RIU_FLAVOR":"cpu-basic","RIU_JOB_ROLE":"main","HF_AUTOSCALE_MAX_WORKERS":"1","HF_HUB_DISABLE_PROGRESS_BARS":"1","RIU_CORS_ORIGINS":"*"}
    last=None
    for ttl,secs in LIFETIMES:  # cpu-basic only; 48h was used by the earlier launcher, 24h is the proven fallback
        try:
            j=HfApi(token=os.environ["HF_TOKEN"]).run_job(image="python:3.12",command=command(),flavor="cpu-basic",timeout=ttl,expose=[8000],expose_public=[8000],env=env,secrets={k:os.environ[k] for k in secret_names if os.environ.get(k)},namespace=NS,labels={"name":"yaiwes-router-16gb"})
            return {"job_id":j.id,"url":"https://"+j.id+"--8000.hf.jobs","flavor":"cpu-basic","started":time.time(),"timeout_s":secs}
        except Exception as exc:
            last=exc; print("KERNEL_LAUNCH_TTL_REJECTED",ttl,type(exc).__name__,flush=True)
    raise RuntimeError("LAUNCH_FAILED:"+type(last).__name__)
# --- Sentinela del Router (2026-10-08): candado, 3 strikes, banco abierto y chat real antes de cambiar ---
LIFETIMES=(("48h",172800),("24h",86400))
STRIKES=int(os.getenv("RIU_KERNEL_STRIKES") or "3")      # fallos de /health seguidos antes de relanzar
LOCK_TTL=1500                                           # un solo supervisor a la vez (watcher del Job o schedule HF)
RENEW_HOUR_UTC=int(os.getenv("RIU_RENEW_HOUR_UTC") or "9")  # 04:00 COT
CHAT_MODELS=[m for m in (os.getenv("RIU_SENTINEL_MODELS") or "groq-qwen-3-8,nv-nemotron-super").split(",") if m]
ME=(os.getenv("JOB_ID") or "schedule")+":"+str(os.getpid())
def http(method,url,data=None,headers=None,timeout=30):
    h={"User-Agent":"yaiwes-kernel","Content-Type":"application/json",**(headers or {})}
    req=urllib.request.Request(url,data=json.dumps(data).encode() if data is not None else None,headers=h,method=method)
    try:
        with urllib.request.urlopen(req,timeout=timeout) as r:return r.status,json.load(r)
    except urllib.error.HTTPError as e:return e.code,{}
    except Exception:return 0,{}
def lock():
    cur=read("control/kernel-lock.json")
    if cur.get("owner") not in (None,ME) and cur.get("until",0)>time.time():return False
    write("control/kernel-lock.json",{"owner":ME,"until":time.time()+LOCK_TTL})
    time.sleep(2)
    return read("control/kernel-lock.json").get("owner")==ME  # el bucket no tiene CAS: releer confirma quien gano
def keep_lock():
    if read("control/kernel-lock.json").get("owner")==ME:write("control/kernel-lock.json",{"owner":ME,"until":time.time()+LOCK_TTL})
def unlock_lock():
    if read("control/kernel-lock.json").get("owner")==ME:write("control/kernel-lock.json",{"owner":None,"until":0})
def bank_ok(url):
    s,d=http("GET",url+"/chat/providers")
    return s==200 and any(p.get("configured") for p in d.get("providers",[]) if p.get("id") in ("groq","nvidia"))
def reopen_bank(url):
    """Motor de re-apertura: abre el banco del Router con la contrasena del entorno (nunca se imprime)."""
    if not os.environ.get("RIU_ROUTER_API_KEY"):
        try:hydrate()  # la API key del Router sale del banco, como en launch()
        except Exception:return False
    pw,key=os.environ.get("RIU_VAULT_PASSPHRASE"),os.environ.get("RIU_ROUTER_API_KEY")
    if not pw or not key:return False
    s,_=http("POST",url+"/vault/unlock",{"passphrase":pw},{"X-API-Key":key})
    return s==200 and bank_ok(url)
def chat_ok(url):
    base=url+"/plugins/puente_chat/call/"
    for model in CHAT_MODELS:
        s,d=http("POST",base+"chat_async",{"model":model,"messages":[{"role":"user","content":"Responde solamente OK"}],"max_tokens":16,"sesion":"kernel-sentinela"})
        pid=(d.get("result") or {}).get("proceso_id")
        end=time.time()+120
        while pid and time.time()<end:
            s,d=http("POST",base+"resultado",{"proceso_id":pid})
            r=d.get("result") or {}
            if r.get("estado")=="procesando":time.sleep(2);continue
            ch=r.get("choices") or []
            if ch and str((ch[0].get("message") or {}).get("content") or "").strip():return True
            break
    return False
def ready(url):
    """Sucesor listo = health + banco abierto (re-abre si hace falta) + chat real con texto."""
    return healthy(url) and (bank_ok(url) or reopen_bank(url)) and chat_ok(url)
def renewal_due(reg):
    left=reg.get("started",0)+reg.get("timeout_s",0)-time.time()
    at_hour=time.gmtime().tm_hour==RENEW_HOUR_UTC and time.time()-reg.get("started",0)>12*3600
    return left<1200 or at_hour
def tick(force=False):
    if not lock():
        print(json.dumps({"status":"LOCKED_BY_OTHER_SUPERVISOR"}),flush=True);return
    try:_tick(force)
    finally:unlock_lock()
def _tick(force):
    reg=read("control/router-current.json")
    alive=bool(reg.get("url")) and healthy(reg["url"])
    if alive:
        write("control/strikes.json",{"n":0})
        if not bank_ok(reg["url"]):
            print(json.dumps({"status":"BANK_REOPEN","ok":reopen_bank(reg["url"])}),flush=True)
        if not force and reg.get("flavor")=="cpu-basic" and not renewal_due(reg):
            print(json.dumps({"status":"HEALTHY","job_id":reg.get("job_id")}),flush=True);return
    elif reg.get("url") and not force:
        n=read("control/strikes.json").get("n",0)+1
        write("control/strikes.json",{"n":n})
        if n<STRIKES:
            print(json.dumps({"status":"STRIKE","n":n,"job_id":reg.get("job_id")}),flush=True);return
    old=reg
    if alive:
        hydrate()
        http("POST",old["url"]+"/chat/storage/sync",{},{"X-API-Key":os.environ.get("RIU_ROUTER_API_KEY","")},20)
    else:
        hydrate()
    new=launch();write("control/recovery-16gb.json",new)
    deadline=time.time()+900
    while time.time()<deadline:
        if healthy(new["url"]):
            if ready(new["url"]):
                publish(new)
                write("control/strikes.json",{"n":0})
                if old.get("job_id") and old["job_id"]!=new["job_id"]:
                    if alive:http("POST",old["url"]+"/chat/storage/sync",{},{"X-API-Key":os.environ.get("RIU_ROUTER_API_KEY","")},20)
                    unlock_lock()  # el watcher puede vivir dentro del Job viejo: soltar el candado antes de cancelarlo
                    try:HfApi(token=os.environ["HF_TOKEN"]).cancel_job(job_id=old["job_id"],namespace=NS)
                    except Exception as exc:print("KERNEL_CANCEL_OLD_FAILED",type(exc).__name__,flush=True)
                print(json.dumps({"status":"SWITCHED",**new}),flush=True);return
        keep_lock();time.sleep(15)
    HfApi(token=os.environ["HF_TOKEN"]).cancel_job(job_id=new["job_id"],namespace=NS)
    raise RuntimeError("SUCCESSOR_NOT_READY_PREDECESSOR_PRESERVED")
if __name__=="__main__":
    if "--watch" in sys.argv:
        # Motor 1: watcher dentro del Job. Motor 2: schedule HF (riu_kernel.py sin --watch). El candado evita duplicados.
        time.sleep(120)
        while True:
            try: tick()
            except Exception as exc: print("KERNEL_RETRY",type(exc).__name__,flush=True)
            time.sleep(60)
    else:
        tick("--force" in sys.argv)
