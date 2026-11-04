from common import *
import urllib.request,time
from wiring_check import run as wc
def main():
    from huggingface_hub import HfApi
    sp=need("SPACE_REPO");api=HfApi(token=need("HF_TOKEN"))
    d=clone("/tmp/s");sha=head(d)
    r=wc(d);check("wiring_check_before_mirror",r["ok"],[c["name"] for c in r["checks"] if not c["ok"]])
    if not all(c["ok"] for c in CHECKS):finish(commit=sha)
    IGN=[".git/**","_quarantine/**","**/node_modules/**","**/__pycache__/**",
        # D-06: fuera del espejo el codigo de terceros vendorizado (315.949 ficheros, 84% del repo).
        "chat-router/agentes/agentes-listos/**","chat-router/agentes/frameworks/**","chat-router/agentes/investigacion/**",
        "chat-router/chatbot/componentes/**","chat-router/memoria/componentes/**","chat-router/otros/descartados/**",
        "chat-router/otros/Prueba/**","chat-router/motores/motores/descarga-copia/**"]
    if os.environ.get("BASELINE")=="1":
        # D-16: modo baseline read-only que exige el DAG en S4_approval.if_missing
        # ("j7 on main as read-only baseline, mirror skipped"): calcula lo que se mirroriaria
        # y el estado del Space, SIN subir nada. El mirror real queda para j9_remirror.
        n=0;sz=0;pfx=[p[:-3] for p in IGN if p.endswith("/**")]
        for root,dirs,files in os.walk(d):
            dirs[:]=[x for x in dirs if x not in(".git","_quarantine","node_modules","__pycache__")]
            for f in files:
                fp=os.path.join(root,f);rel=os.path.relpath(fp,d).replace(os.sep,"/")
                if any(rel.startswith(p) for p in pfx):continue
                n+=1;sz+=os.path.getsize(fp)
        stage=str(api.get_space_runtime(sp).stage)
        check("baseline_only_no_upload",True,f"{n} ficheros, {sz/1e6:.1f} MB (sin subir)")
        check("space_RUNNING","RUNNING" in stage,stage)
        finish({"space":sp,"head":sha,"baseline":True,"files":n,"bytes":sz},commit=sha)
    api.upload_folder(folder_path=d,repo_id=sp,repo_type="space",commit_message=f"mirror {sha[:12]}",
        ignore_patterns=IGN)
    hu=os.environ.get("HEALTH_URL");wait=int(os.environ.get("WAIT_S","600"));t0=time.time();seen=None;stage=None
    while time.time()-t0<wait:
        stage=str(api.get_space_runtime(sp).stage)
        if "RUNNING" in stage and hu:
            try:
                seen=json.loads(urllib.request.urlopen(hu,timeout=15).read()).get("commit")
                if seen and sha.startswith(seen[:12]):break
            except Exception:pass
        time.sleep(20)
    check("space_RUNNING","RUNNING" in str(stage),stage)
    check("health_url_set",bool(hu),"add GET /health -> {commit} (kernel R4)")
    check("health_commit_equals_HEAD",bool(seen) and sha.startswith(seen[:12]),f"seen={seen} head={sha[:12]}")
    finish({"space":sp,"head":sha},commit=sha)
if __name__=="__main__":run(main)
