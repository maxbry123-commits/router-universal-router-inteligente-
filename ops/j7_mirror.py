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
        "chat-router/otros/Prueba/**","chat-router/motores/motores/descarga-copia/**",
        # D-58: el limite del endpoint de HF es de 20.000 ficheros por repo y el espejo
        # llegaba a 20.008. kernel/ y ops/ son el utillaje de despliegue (no runtime del
        # Space): excluirlos deja el espejo en 19.961 ficheros y 31 de margen.
        "kernel/**","ops/**",
        # D-62: `router-mvp/router-componentes/` son 14.602 ficheros de bibliotecas de terceros
        # vendorizadas (fastapi, cryptography, pydantic, pyyaml, huggingface_hub, MCP SDKs...).
        # El Space instala sus dependencias por pip: no las necesita en runtime y son las que
        # hacen que el espejo (20.775) rebase el limite de 20.000 ficheros del repo del Space.
        "router-mvp/router-componentes/**"]
    if os.environ.get("MIRROR_BASELINE")=="1":
        # D-16/D-20: modo baseline read-only que exige el DAG en S4_approval.if_missing.
        # D-20: la env se llama MIRROR_BASELINE y no BASELINE porque wiring_check usa BASELINE como RUTA del baseline.
        # ("j7 on main as read-only baseline, mirror skipped"): calcula lo que se mirroriaria
        # y el estado del Space, SIN subir nada. El mirror real queda para j9_remirror.
        n=0;sz=0;pfx=[p[:-3] for p in IGN if p.endswith("/**")]
        # D-19: os.scandir cachea el stat del propio recorrido (os.walk+getsize = 12+ min)
        for root,dirs,files in os.walk(d):
            dirs[:]=[x for x in dirs if x not in(".git","_quarantine","node_modules","__pycache__")]
            with os.scandir(root) as it:
                for e in it:
                    if not e.is_file(follow_symlinks=False):continue
                    rel=os.path.relpath(e.path,d).replace(os.sep,"/")
                    if any(rel.startswith(p) for p in pfx):continue
                    n+=1;sz+=e.stat(follow_symlinks=False).st_size
        stage=str(api.get_space_runtime(sp).stage)
        check("baseline_only_no_upload",True,f"{n} ficheros, {sz/1e6:.1f} MB (sin subir)")
        check("space_RUNNING","RUNNING" in stage,stage)
        finish({"space":sp,"head":sha,"baseline":True,"files":n,"bytes":sz},commit=sha)
    # D-56: el push del mirror se hace por protocolo git al repo del Space.
    # `upload_folder` usa el endpoint de commits de HF, que RECHAZA el push cuando el
    # repo tendria mas de ~10.000 ficheros ("Your push was rejected because it contains
    # too many files ... 20008 files"); el mirror son 20.008 ficheros -> FAIL.
    # Por git si se aceptan (limite del servidor HF: ~100k ficheros / 10 GB por push).
    # Antes se preservan los ficheros propios del Space (Dockerfile, boot.sh, proxy.py...):
    # el push es de arbol completo y los borraria.
    import base64
    from huggingface_hub import hf_hub_download
    # D-63: NO se baja el repo entero del Space con snapshot_download: el repo del Space ya
    # contenia la copia anterior del espejo (19.998 ficheros) y bajarla entera tardaba horas y
    # hacia que el push volviera a rebasar el limite de 20.000. Solo se recuperan los ficheros
    # PROPIOS del Space (los que no estan en la rama): Dockerfile, boot.sh, proxy.py, etc.
    space_files=api.list_repo_files(sp,repo_type="space")
    branch_files=set(sh(["git","ls-tree","-r","--name-only","HEAD"],cwd=d).stdout.split())
    own=[f for f in space_files if f not in branch_files]
    for rel in own:
        src=hf_hub_download(repo_id=sp,filename=rel,repo_type="space",token=need("HF_TOKEN"))
        dst=os.path.join(d,rel)
        os.makedirs(os.path.dirname(dst),exist_ok=True)
        shutil.copy2(src,dst)
    check("space_own_files_preserved",True,f"{len(own)} ficheros propios del Space: {own[:8]}")
    sh(["git","-C",d,"checkout","-B",f"mirror/{sha[:12]}"])
    sh(["git","-C",d,"add","-A"])          # D-71: primero se anade todo...
    for pat in IGN:
        pfx=pat[:-3] if pat.endswith("/**") else None
        if pfx:
            sh(["git","-C",d,"rm","-r","--cached","--ignore-unmatch",pfx],check=False)
        else:
            sh(["git","-C",d,"rm","-r","--cached","--ignore-unmatch",pat],check=False)
    # D-69: el .gitattributes del Space marca como LFS muchas extensiones (*.bin, *.gz, *.tar,
    # *.pt, *.npy, *.parquet, saved_model/**...). El hook lfs-check del servidor rechaza el push
    # si esos punteros LFS llegan sin sus objetos en el almacen LFS del Space. Por eso se
    # excluyen del espejo los ficheros que casan con los patrones LFS del propio Space.
    lfs_pats=[]
    ga=os.path.join(d,".gitattributes")
    if os.path.exists(ga):
        for line in open(ga,errors="ignore"):
            line=line.strip()
            if line and not line.startswith("#") and "filter=lfs" in line:
                pat=line.split()[0]
                if pat not in lfs_pats: lfs_pats.append(pat)
    for pat in lfs_pats:
        sh(["git","-C",d,"rm","-r","--cached","--ignore-unmatch",pat],check=False)
    check("lfs_patterns_excluded",True,f"{len(lfs_pats)} patrones LFS del Space excluidos: {lfs_pats[:6]}")
    n_tree=len(sh(["git","-C",d,"ls-files"],check=False).stdout.split())
    check("mirror_tree_size",n_tree<20000,f"{n_tree} ficheros en el arbol del push (limite 20000)")
    sh(["git","-C",d,"-c","user.name=kernel-mirror","-c","user.email=mirror@local",
        "commit","-q","-m",f"mirror {sha[:12]} (j7_mirror D-56)"],check=False)
    # D-67: HF ignora la cabecera `http.<url>.extraheader` en el PUSH (la API responde 200 pero
    # git sigue pidiendo usuario: "could not read Username for 'https://huggingface.co'").
    # La via que si funciona es el AYUDANTE DE CREDENCIALES: el token se lee del entorno dentro
    # del propio helper, de modo que no aparece ni en argv ni en la URL ni en el log.
    tok=need("HF_TOKEN")
    env2=dict(os.environ);env2["HF_TOKEN"]=tok
    helper=("!f() { echo username=x-access-token; echo password=$HF_TOKEN; }; f")
    r=sh(["git","-C",d,"-c","credential.helper=",
          "-c",f"credential.helper={helper}",
          "push","-f","https://huggingface.co/spaces/"+sp,"HEAD:main"],env=env2,check=False)
    check("mirror_push_git",r.returncode==0,(r.stdout+r.stderr)[-400:])
    if r.returncode!=0:
        finish({"space":sp,"head":sha,"push_error":(r.stdout+r.stderr)[-400:]},commit=sha)
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
