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
    # D-108: el Space NO es un espejo del repo. Misma allowlist operativa que j7_mirror
    # (D-86): el push es por protocolo git (upload_folder choca con el limite de 20.000
    # ficheros del repo del Space) y solo suben los ficheros PROPIOS del Space.
    SPACE_ALLOWLIST={"Dockerfile","boot.sh","proxy.py","openclaw.sh",
                     "swecode_provider.json","README.md",".gitattributes",".gitignore",".rebuild"}
    sh(["git","-C",d,"read-tree",sha])
    _pf=os.path.join(d,".excl_paths")
    with open(_pf,"wb") as fh:
        for t in sh(["git","-C",d,"ls-files","-z"],check=False).stdout.split("\0"):
            if t and t not in SPACE_ALLOWLIST: fh.write(t.encode()+b"\0")
    sh(["git","-C",d,"rm","-r","--cached","--ignore-unmatch","--pathspec-from-file="+_pf,"--pathspec-file-nul"],check=False)
    _tree=sh(["git","-C",d,"write-tree"],check=False).stdout.strip()
    _new=sh(["git","-C",d,"-c","user.name=kernel-mirror","-c","user.email=mirror@local","commit-tree",_tree,"-m",f"remirror {sha[:12]}"],check=False).stdout.strip()
    _env=dict(os.environ);_env["HF_TOKEN"]=need("HF_TOKEN")
    _cred=["-c","credential.helper=","-c","credential.helper=!f() { echo username=x-access-token; echo password=$HF_TOKEN; }; f"]
    _r=sh(["git","-C",d]+_cred+["push",f"https://huggingface.co/spaces/{sp}",f"{_new}:main"],env=_env,check=False)
    check("remirror_push_git",_r.returncode==0,(_r.stdout+_r.stderr)[-300:])
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
