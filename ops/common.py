import os,sys,json,time,base64,hashlib,pathlib,subprocess,traceback,shutil
RUN_ID=os.environ.get("RUN_ID",time.strftime("%Y%m%d-%H%M%S"))
JOB=os.environ.get("JOB_NAME") or pathlib.Path(sys.argv[0]).stem
OUT=pathlib.Path(os.environ.get("OUT_DIR",f"/tmp/out/{JOB}"));OUT.mkdir(parents=True,exist_ok=True)
CHECKS=[]
def redact(s):
    t=os.environ.get("GH_TOKEN");return s.replace(t,"***") if t and s else (s or "")
def genv():  # token only in process env: never in URL, argv, remote config or logs
    e=dict(os.environ);t=e.get("GH_TOKEN")
    if t:
        b=base64.b64encode(f"x-access-token:{t}".encode()).decode()
        e.update(GIT_TERMINAL_PROMPT="0",GIT_CONFIG_COUNT="1",
                 GIT_CONFIG_KEY_0="http.https://github.com/.extraheader",
                 GIT_CONFIG_VALUE_0=f"AUTHORIZATION: basic {b}")
    return e
def sh(cmd,cwd=None,check=True,timeout=None):
    r=subprocess.run(cmd,cwd=cwd,env=genv(),capture_output=True,text=True,timeout=timeout)
    if check and r.returncode:raise RuntimeError(f"{' '.join(cmd[:3])} rc={r.returncode} {redact(r.stderr)[-400:]}")
    return r
def check(name,ok,detail=""):
    CHECKS.append({"name":name,"ok":bool(ok),"detail":str(detail)[:300]});return bool(ok)
def need(k):
    v=os.environ.get(k)
    if not v:raise RuntimeError(f"missing env {k}")
    return v
def clone(dest,depth=1,since=None,blobless=False,branch=None):
    repo=need("GH_REPO");br=branch or os.environ.get("TARGET_BRANCH") or need("GH_BRANCH")
    c=["git","clone","--single-branch","--no-tags","--branch",br]
    if since:c+=["--shallow-since",since]
    elif depth:c+=["--depth",str(depth)]
    if blobless:c+=["--filter=blob:none"]
    # D-13 (rutas §20: 1 existing_code + 8 smaller_scope): clon idempotente.
    # Si el destino ya es un repo git se reutiliza (fetch + reset); si existe y no es
    # repo es scratch y se regenera. Evita el rc=128 "destination path already exists"
    # que tumbaba j4_plan.
    if os.path.isdir(os.path.join(dest,".git")):
        sh(["git","-C",dest,"fetch","--depth","1","--no-tags","origin",br],check=False)
        sh(["git","-C",dest,"checkout","-B",br,"FETCH_HEAD"],check=False)
        sh(["git","-C",dest,"reset","--hard","FETCH_HEAD"],check=False)
        return dest
    if os.path.exists(dest):
        shutil.rmtree(dest,ignore_errors=True)
    sh(c+[f"https://github.com/{repo}.git",dest]);return dest
def sha256(p):
    h=hashlib.sha256()
    with open(p,"rb") as f:
        for b in iter(lambda:f.read(1<<20),b""):h.update(b)
    return h.hexdigest()
def head(d):return sh(["git","rev-parse","HEAD"],cwd=d).stdout.strip()
def dl(job,name):  # artifact of an earlier job, same RUN_ID
    from huggingface_hub import hf_hub_download
    return hf_hub_download(repo_id=need("DATASET_REPO"),repo_type="dataset",filename=f"{RUN_ID}/{job}/{name}",token=os.environ.get("HF_TOKEN"))
def finish(extra=None,commit=None):
    status="PASS" if CHECKS and all(c["ok"] for c in CHECKS) else "FAIL"
    res={"job":JOB,"run_id":RUN_ID,"status":status,"commit":commit,"ts":time.strftime("%FT%TZ",time.gmtime()),"checks":CHECKS,**(extra or {})}
    (OUT/"result.json").write_text(json.dumps(res,indent=1))
    try:
        r=os.environ.get("DATASET_REPO");t=os.environ.get("HF_TOKEN")
        if r and t:
            from huggingface_hub import HfApi
            HfApi(token=t).upload_folder(folder_path=str(OUT),repo_id=r,repo_type="dataset",path_in_repo=f"{RUN_ID}/{JOB}")
    except Exception as e:print("upload_failed",redact(str(e)))
    print(json.dumps({"job":JOB,"status":status,"failed":[c["name"] for c in CHECKS if not c["ok"]]}))
    sys.exit(0 if status=="PASS" else 1)
def run(main):
    try:main()
    except Exception as e:
        check("exception",False,redact(str(e)));print(redact(traceback.format_exc())[-800:]);finish()
    finish()
