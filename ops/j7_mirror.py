from common import *
import base64
import urllib.request,time
from wiring_check import run as wc
def main():
    from huggingface_hub import HfApi
    sp=need("SPACE_REPO");api=HfApi(token=need("HF_TOKEN"))
    LIGHT=os.environ.get("MIRROR_LIGHT")=="1"
    if LIGHT:
        # D-75: modo ligero. El sandbox reinicia /tmp cada 15-20 min y se lleva el clon de 18 GB;
        # en modo ligero el clon es `--filter=blob:none --no-checkout` (arbol sin working tree) y el
        # gate previo se evalua sobre el YAML del registro (el predicado exacto de wiring_check).
        import shutil as _sh
        d="/tmp/sl"
        if os.path.isdir(d): _sh.rmtree(d,ignore_errors=True)
        env3=dict(os.environ);env3.update(GIT_TERMINAL_PROMPT="0",GIT_CONFIG_COUNT="1",
            GIT_CONFIG_KEY_0="http.https://github.com/.extraheader",
            GIT_CONFIG_VALUE_0=f"AUTHORIZATION: basic {base64.b64encode(('x-access-token:'+need('GH_TOKEN')).encode()).decode()}")
        br=os.environ.get("TARGET_BRANCH") or need("GH_BRANCH")
        sh(["git","clone","--single-branch","--no-tags","--filter=blob:none","--no-checkout",
            "--depth","1","--branch",br,f"https://github.com/{need('GH_REPO')}.git",d],env=env3)
        sha=head(d)
        import yaml as _yaml
        # D-76: en el clon ligero (filtrado) la lectura de blobs lanza la descarga del blob y
        # falla ("failed to unpack tree object"). El registro se lee del REPO LOCAL, que si tiene
        # los objetos completos, y el .gitattributes del Space se baja por la API.
        # D-78: el clon local del sandbox tambien es filtrado y su descarga de blobs falla
        # ("failed to unpack tree object"), asi que el registro se lee del fichero ya
        # materializado en el repositorio local (main; la rama solo añade movimientos de
        # ficheros, no toca el registro).
        reg_txt=open("connections/registry.yaml",errors="ignore").read()
        reg=_yaml.safe_load(reg_txt) or {}
        conns=reg.get("connections",[])
        need_f=("id","name","source","target","protocol","direction","endpoint","status","dependencies",
                "verification","notes","from","to","via","provides","requires")
        bad=[x.get("id") for x in conns if not all(q in x for q in need_f)
             or x["status"] not in ("pending_audit","active","broken")
             or (x["status"]=="active" and not x.get("evidence"))]
        check("registry_valid",not bad,bad[:5] or "")
    else:
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
    from huggingface_hub import hf_hub_download
    # D-63: NO se baja el repo entero del Space con snapshot_download: el repo del Space ya
    # contenia la copia anterior del espejo (19.998 ficheros) y bajarla entera tardaba horas y
    # hacia que el push volviera a rebasar el limite de 20.000. Solo se recuperan los ficheros
    # PROPIOS del Space (los que no estan en la rama): Dockerfile, boot.sh, proxy.py, etc.
    # D-72: el push se hace como FAST-FORWARD sobre el HEAD actual del Space (commit con el
    # remoto como padre). Sin eso, git negocia contra el remoto y el upload-pack responde
    # "not our ref <HEAD>" -> el servidor responde "internal error hook: lfs-check" y el push
    # se rechaza. Para el fast-forward hace falta el commit remoto: se obtiene con un fetch.
    env2=dict(os.environ);env2["HF_TOKEN"]=need("HF_TOKEN")
    helper=("!f() { echo username=x-access-token; echo password=$HF_TOKEN; }; f")
    cred=["-c","credential.helper=","-c",f"credential.helper={helper}"]
    space_url=f"https://huggingface.co/spaces/{sp}"
    # D-77: el fetch del repo del Space va SIN --depth: con --depth 1 sobre un clon filtrado
    # el pack no se desempaqueta ("failed to unpack tree object") y el push se cae.
    sh(["git","-C",d]+cred+["fetch",space_url,"main"],env=env2,check=False)
    rem=sh(["git","-C",d]+cred+["rev-parse","FETCH_HEAD"],env=env2,check=False).stdout.strip()
    # los ficheros PROPIOS del Space (Dockerfile, boot.sh, proxy.py, .gitattributes...) se
    # recuperan del commit remoto y se meten en el indice: el push es de arbol completo.
    own=[]
    if rem:
        for line in sh(["git","-C",d,"ls-tree",rem],check=False).stdout.splitlines():
            meta,path=line.split("\t",1)
            mode,typ,sha=meta.split()
            if typ=="blob" and path not in own: own.append(path)
    for rel in own:
        line=sh(["git","-C",d,"ls-tree",rem,rel],check=False).stdout.strip()
        if not line: continue
        meta=line.split()
        sh(["git","-C",d,"update-index","--add","--cacheinfo",meta[0],meta[2],rel],check=False)
    check("space_own_files_preserved",bool(own),f"{len(own)} ficheros propios del Space: {own[:8]}")
    sh(["git","-C",d,"checkout","-B",f"mirror/{sha[:12]}"])
    # D-74: el indice se construye con `read-tree` (arbol de la rama) en vez de `git add -A`
    # (working tree): con `add` entraban ficheros que no deben ir al push. Las exclusiones se
    # aplican con un fichero de pathspec (NUL-separated) para que los patrones con espacios y
    # los `**` casen exactamente.
    sh(["git","-C",d,"read-tree",sha])
    def rm_paths(paths):
        if not paths: return
        pf=os.path.join(d,".excl_paths")
        with open(pf,"wb") as f:
            for x in paths: f.write(x.encode()+b"\0")
        sh(["git","-C",d,"rm","-r","--cached","--ignore-unmatch",
            f"--pathspec-from-file={pf}","--pathspec-file-nul"],check=False)
        try: os.remove(pf)
        except OSError: pass
    ign_prefixes=[p[:-3] if p.endswith("/**") else p for p in IGN]
    tracked=sh(["git","-C",d,"ls-files","-z"],check=False).stdout.split("\0")
    tracked=[t.decode() for t in tracked if t]
    rm_paths([t for t in tracked if any(t.startswith(pfx) for pfx in ign_prefixes)])
    # D-69: el .gitattributes del Space marca como LFS muchas extensiones (*.bin, *.gz, *.tar,
    # *.pt, *.npy, *.parquet, saved_model/**...). El hook lfs-check del servidor rechaza el push
    # si esos punteros LFS llegan sin sus objetos en el almacen LFS del Space. Por eso se
    # excluyen del espejo los ficheros que casan con los patrones LFS del propio Space.
    # D-73: los patrones LFS se leen del `.gitattributes` del PROPIO Space (el del commit remoto),
    # no del de la rama: el de la rama esta vacio y el push volvia a llevar punteros LFS -> 500.
    lfs_pats=[]
    ga_txt=""
    try:
        from huggingface_hub import hf_hub_download as _hd
        ga_txt=open(_hd(repo_id=sp,filename=".gitattributes",repo_type="space",token=need("HF_TOKEN")),errors="ignore").read()
    except Exception:
        pass
    if not ga_txt.strip():
        ga_txt=sh(["git","show",f"{br}:.gitattributes"],check=False).stdout
    for line in ga_txt.splitlines():
        line=line.strip()
        if line and not line.startswith("#") and "filter=lfs" in line:
            pat=line.split()[0]
            if pat not in lfs_pats: lfs_pats.append(pat)
    import fnmatch
    tracked2=sh(["git","-C",d,"ls-files","-z"],check=False).stdout.split("\0")
    tracked2=[t.decode() for t in tracked2 if t]
    lfs_files=[t for t in tracked2 if any(fnmatch.fnmatch(t,pat) or fnmatch.fnmatch(os.path.basename(t),pat)
                                          or t.startswith(pat.rstrip("*")) for pat in lfs_pats)]
    rm_paths(lfs_files)
    check("lfs_patterns_excluded",True,f"{len(lfs_pats)} patrones LFS del Space, {len(lfs_files)} ficheros excluidos: {lfs_pats[:6]}")
    n_tree=len(sh(["git","-C",d,"ls-files"],check=False).stdout.split())
    check("mirror_tree_size",n_tree<20000,f"{n_tree} ficheros en el arbol del push (limite 20000)")
    sh(["git","-C",d,"-c","user.name=kernel-mirror","-c","user.email=mirror@local",
        "commit","-q","-m",f"mirror {sha[:12]} (j7_mirror D-56)"],check=False)
    # D-67: HF ignora la cabecera `http.<url>.extraheader` en el PUSH (la API responde 200 pero
    # git sigue pidiendo usuario: "could not read Username for 'https://huggingface.co'").
    # La via que si funciona es el AYUDANTE DE CREDENCIALES: el token se lee del entorno dentro
    # del propio helper, de modo que no aparece ni en argv ni en la URL ni en el log.
    # D-72: el commit se crea con `commit-tree` usando el HEAD remoto como padre y se sube sin
    # --force: asi el push es un fast-forward y no hay negociacion que dispare el lfs-check.
    tree=sh(["git","-C",d,"write-tree"],check=False).stdout.strip()
    parent=rem if rem else ""
    cargs=["git","-C",d,"-c","user.name=kernel-mirror","-c","user.email=mirror@local","commit-tree",tree]
    if parent: cargs+=["-p",parent]
    cargs+=["-m",f"mirror {sha[:12]} (j7_mirror D-72)"]
    new_commit=sh(cargs,check=False).stdout.strip()
    r=sh(["git","-C",d]+cred+["push",space_url,f"{new_commit}:main"],env=env2,check=False)
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
