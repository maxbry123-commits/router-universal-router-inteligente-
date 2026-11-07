from common import *
import urllib.request,time
from wiring_check import run as wc
# ops/j9_remirror.py — re-mirror tras el swap de main (S12_final).
# Guia: kernel/GUIDE.md S12_final: {jobs: [j9_remirror, j10_final_audit], gate: [Space==new HEAD, audit PASS]}
#
# D-145 (correccion del reespejo): el Space NO es un espejo del repo.
# Su boot.sh hace `git clone --depth 1 --filter=blob:none --branch main` de GitHub en CADA build:
# el Space ya es un auto-pull de main. El reespejo real = que el Space sirva el main nuevo, y
# para eso basta (1) main publicado y (2) disparar un rebuild del Space.
# El metodo anterior (empujar al Space un arbol derivado del repo) era Peligroso: proxy.py,
# boot.sh, openclaw.sh, Dockerfile y swecode_provider.json viven en SUBCARPETAS del repo, no en
# su raiz -> ese push habria BORRADO 6 ficheros operativos del Space y el router no habria
# arrancado. Ademas el push por git al host de HF falla con "expected 'acknowledgments'" sobre
# HTTP/2; la via fiable es la API de HF (huggingface_hub).
#
# D-146 (blindaje): este job NUNCA muta el indice ni el working tree del clon que recibe:
# solo lee (git ls-files / lectura de ficheros) y usa un indice temporal cuando lo necesita.
# Por eso REUSE_CLONE es seguro aqui (antes D-144 usaba `git rm --cached` sobre el clon vivo
# y dejo 366.077 ficheros fuera del disco: el checkout-index -a -f los recupero).
def main():
    from huggingface_hub import HfApi,CommitOperationAdd
    sp=need("SPACE_REPO");api=HfApi(token=need("HF_TOKEN"))
    reuse=os.environ.get("REUSE_CLONE")
    # D-147: el sha de referencia es el MAIN REMOTO real (fuente de verdad), no el HEAD de un
    # clon de trabajo: asi el gate "Space sirve main" compara contra lo que GitHub publica.
    d=reuse or clone(os.path.join(os.environ.get("WORK_DIR","/workspace/work"),"mirror9"))
    sha=sh(["git","ls-remote","origin","refs/heads/main"],cwd=d,check=False).stdout.split()
    sha=sha[0] if sha else head(d)
    # D-149: el sha de referencia (D-147) queda CONGELADO al inicio del job, pero main SIGUE
    # AVANZANDO mientras el job corre (la tuberia de bundles publica en main cada pocos minutos) y el
    # Space hace auto-pull de main en CADA build: al verificar, el Space puede estar sirviendo un commit
    # de main MAS NUEVO que ese sha congelado, y el gate fallaba aunque el objetivo del job ("el Space
    # sirve main") se cumpliera. Fix: se registra TODOS los HEAD de main observados (el inicial + los
    # que se ven en cada vuelta de la espera) y el gate acepta que el Space sirva cualquiera de ellos.
    # Un Space que siga sirviendo un commit viejo (p.ej. 4722f1dffc, publicado antes del job) NO se
    # acepta: el gate sigue detectando que el Space no se ha actualizado.
    mains={sha}
    # el gate de cableado se ejecuta en modo LECTURA sobre el arbol disponible
    r=wc(d);check("wiring_check_before_remirror",r["ok"],[c["name"] for c in r["checks"] if not c["ok"]])
    if not all(c["ok"] for c in CHECKS):finish(commit=sha)
    # D-145: el Space debe conservar sus ficheros operativos (proxy.py/boot.sh/openclaw.sh/
    # Dockerfile/swecode_provider.json). Si no estan, NO se toca nada: el Space esta roto.
    try:
        _files=api.list_repo_files(sp,repo_type="space")
        _need=("boot.sh","Dockerfile","proxy.py","openclaw.sh","swecode_provider.json")
        check("space_has_operational_files",all(f in _files for f in _need),f"{len(_files)} ficheros en el Space")
    except Exception as _e:
        check("space_has_operational_files",False,f"{type(_e).__name__}: {str(_e)[:160]}")
    # D-145/D-146: disparar el rebuild por la API de HF (nunca por git push).
    _stamp=time.strftime("%Y-%m-%dT%H:%M:%S-00:00")
    try:
        _c=api.create_commit(repo_id=sp,repo_type="space",
                             operations=[CommitOperationAdd(path=".rebuild",content=_stamp)],
                             commit_message=f"remirror {sha[:12]}: rebuild para servir main {sha[:12]}")
        check("remirror_trigger_rebuild",True,str(getattr(_c,"oid",""))[:12])
    except Exception as _e:
        check("remirror_trigger_rebuild",False,f"{type(_e).__name__}: {str(_e)[:200]}")
        finish(commit=sha)
    hu=os.environ.get("HEALTH_URL");wait=int(os.environ.get("WAIT_S","1800"));t0=time.time();seen=None;stage=None
    while time.time()-t0<wait:
        try:stage=str(api.get_space_runtime(sp).stage)
        except Exception as _e:stage=f"ERR {type(_e).__name__}"
        # D-149: cada vuelta registra el HEAD actual de main (main puede avanzar durante la espera).
        _m=sh(["git","ls-remote","origin","refs/heads/main"],cwd=d,check=False).stdout.split()
        if _m:mains.add(_m[0])
        if "RUNNING" in stage and hu:
            try:
                seen=json.loads(urllib.request.urlopen(hu,timeout=15).read()).get("commit")
                if seen and any(str(m).startswith(str(seen)[:12]) for m in mains):break
            except Exception:pass
        time.sleep(20)
    check("space_RUNNING","RUNNING" in str(stage),stage)
    check("health_commit_equals_new_HEAD",bool(seen) and any(str(m).startswith(str(seen)[:12]) for m in mains),
          f"seen={seen} main={sha[:12]} heads_vistos={len(mains)}")
    finish({"space":sp,"head":sha,"remirror":True},commit=sha)
if __name__=="__main__":run(main)
