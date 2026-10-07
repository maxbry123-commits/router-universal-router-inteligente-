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
    return ["bash","-lc","set -e\npip install -q huggingface_hub cryptography httpx 'uvicorn[standard]' fastapi pydantic psutil mcp beautifulsoup4\npython - <<'PY'\nimport os,io,tarfile\nfrom huggingface_hub import HfFileSystem\nf=HfFileSystem(token=os.environ['HF_TOKEN'])\nb='buckets/COMAND-CENTER-1/yaiwes-memoria-storage/router-inteligente-universal'\ntarfile.open(fileobj=io.BytesIO(f.cat_file(b+'/codigo/router-bundle.tar.gz')),mode='r:gz').extractall('/app',filter='data')\nPY\ncd '/app/router inteligente universal'\npython riu_kernel.py --watch &\nexec uvicorn public_chat_app:app --host 0.0.0.0 --port 8000 --timeout-keep-alive 120"]
def launch():
    hydrate()
    secret_names=["HF_TOKEN","HF_CONTROL_JOBS_TOKEN","GITHUB_PERSONAL_ACCESS_TOKEN","RIU_VAULT_PASSPHRASE","RIU_ROUTER_API_KEY","RIU_AGENT_API_KEYS","RIU_AGENT_API_KEYS_2","RIU_DIRECTOR_KEY_HASH","RIU_PUBLIC_CHAT_KEY"]
    env={"HF_BUCKET_ID":NS+"/yaiwes-memoria-storage","RIU_DATA_DIR":"/tmp/riu-data","RIU_VAULT_PATH":"/tmp/riu-data/riu_vault.db","RIU_VAULT_SOURCE":BASE+"/banco/vault.db.gz.b64","RIU_VAULT_PROVIDERS_SOURCE":BASE+"/banco/providers.json","RIU_AUTOSYNC_SECONDS":"60","RIU_CHAT_ALLOW_PROVIDER_LIVE":"1","RIU_G2_GROQ_MODEL":"qwen/qwen3.8-27b","RIU_CODE_BUNDLE":BASE+"/codigo/router-bundle.tar.gz","RIU_ROOT":"router-inteligente-universal","RIU_FLAVOR":"cpu-basic","RIU_JOB_ROLE":"main","HF_AUTOSCALE_MAX_WORKERS":"1","HF_HUB_DISABLE_PROGRESS_BARS":"1","RIU_CORS_ORIGINS":"*"}
    j=HfApi(token=os.environ["HF_TOKEN"]).run_job(image="python:3.12",command=command(),flavor="cpu-basic",timeout="24h",expose=[8000],expose_public=[8000],env=env,secrets={k:os.environ[k] for k in secret_names},namespace=NS,labels={"name":"yaiwes-router-16gb"})
    return {"job_id":j.id,"url":"https://"+j.id+"--8000.hf.jobs","flavor":"cpu-basic","started":time.time(),"timeout_s":86400}
def tick(force=False):
    reg=read("control/router-current.json")
    if not force and reg.get("url") and healthy(reg["url"]) and reg.get("flavor")=="cpu-basic" and reg.get("started",0)+reg.get("timeout_s",0)-time.time()>1200:
        print(json.dumps({"status":"HEALTHY","job_id":reg.get("job_id")}),flush=True);return
    old=reg
    if old.get("url") and healthy(old["url"]):
        hydrate()
        try:
            req=urllib.request.Request(old["url"]+"/chat/storage/sync",data=b"{}",headers={"X-API-Key":os.environ["RIU_ROUTER_API_KEY"],"Content-Type":"application/json"},method="POST")
            urllib.request.urlopen(req,timeout=20).close()
        except Exception: pass
    new=launch();write("control/recovery-16gb.json",new)
    deadline=time.time()+600
    while time.time()<deadline:
        if healthy(new["url"]):
            publish(new)
            # Sync the predecessor's memory before ending its temporary process.
            if old.get("job_id") and old["job_id"]!=new["job_id"]:
                try:
                    req=urllib.request.Request(old["url"]+"/chat/storage/sync",data=b"{}",headers={"X-API-Key":os.environ["RIU_ROUTER_API_KEY"],"Authorization":"Bearer "+os.environ["HF_TOKEN"],"Content-Type":"application/json"},method="POST")
                    urllib.request.urlopen(req,timeout=20).close()
                except Exception:pass
                HfApi(token=os.environ["HF_TOKEN"]).cancel_job(job_id=old["job_id"],namespace=NS)
            print(json.dumps({"status":"SWITCHED",**new}),flush=True);return
        time.sleep(10)
    HfApi(token=os.environ["HF_TOKEN"]).cancel_job(job_id=new["job_id"],namespace=NS)
    raise RuntimeError("SUCCESSOR_UNHEALTHY_PREDECESSOR_PRESERVED")
if __name__=="__main__":
    if "--watch" in sys.argv:
        # Renewal stays in the same 16 GB job; the new job takes over only when healthy.
        time.sleep(120)
        while True:
            try: tick()
            except Exception as exc: print("KERNEL_RETRY",type(exc).__name__,flush=True)
            time.sleep(60)
    else:
        tick("--force" in sys.argv)
