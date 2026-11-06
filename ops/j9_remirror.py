from common import *
import urllib.request,time
from wiring_check import run as wc
# ops/j9_remirror.py — re-mirror tras el swap de main (S12_final).
# Guia: kernel/GUIDE.md S12_final: {jobs: [j9_remirror, j10_final_audit], gate: [Space==new HEAD, audit PASS]}
# D-23: la guia DECLARA este job en el mapa de jobs y en S12 pero NO incluye su codigo.
# Se implementa aqui siguiendo el patron exacto de ops/j7_mirror.py (mismo helper, mismos gates),
# sin modo baseline: este job sube de verdad el HEAD nuevo al Space y verifica Space==new HEAD.
def main():
    from huggingface_hub import HfApi
    sp=need("SPACE_REPO");api=HfApi(token=need("HF_TOKEN"))
    d=clone(os.path.join(os.environ.get("WORK_DIR","/workspace/work"),"mirror9"));sha=head(d)   # G2: scratch en WORK_DIR (NAS)
    r=wc(d);check("wiring_check_before_remirror",r["ok"],[c["name"] for c in r["checks"] if not c["ok"]])
    if not all(c["ok"] for c in CHECKS):finish(commit=sha)
    IGN=[".git/**","_quarantine/**","**/node_modules/**","**/__pycache__/**",
        "chat-router/agentes/agentes-listos/**","chat-router/agentes/frameworks/**","chat-router/agentes/investigacion/**",
        "chat-router/chatbot/componentes/**","chat-router/memoria/componentes/**","chat-router/otros/descartados/**",
        "chat-router/otros/Prueba/**","chat-router/motores/motores/descarga-copia/**"]
    api.upload_folder(folder_path=d,repo_id=sp,repo_type="space",commit_message=f"remirror {sha[:12]}",ignore_patterns=IGN)
    hu=os.environ.get("HEALTH_URL");wait=int(os.environ.get("WAIT_S","900"));t0=time.time();seen=None;stage=None
    while time.time()-t0<wait:
        stage=str(api.get_space_runtime(sp).stage)
        if "RUNNING" in stage and hu:
            try:
                seen=json.loads(urllib.request.urlopen(hu,timeout=15).read()).get("commit")
                if seen and sha.startswith(seen[:12]):break
            except Exception:pass
        time.sleep(20)
    check("space_RUNNING","RUNNING" in str(stage),stage)
    check("health_commit_equals_new_HEAD",bool(seen) and sha.startswith(seen[:12]),f"seen={seen} head={sha[:12]}")
    finish({"space":sp,"head":sha,"remirror":True},commit=sha)
if __name__=="__main__":run(main)
