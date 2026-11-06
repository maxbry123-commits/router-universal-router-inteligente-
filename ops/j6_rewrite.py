from common import *
import yaml,pathlib,shutil
from wiring_check import run as wc
def main():
    from huggingface_hub import HfApi
    plan=json.load(open(dl("j4_plan","plan.json")))
    for j in("j5_apply","j8_audit"):check(f"{j}_PASS",json.load(open(dl(j,"result.json")))["status"]=="PASS")
    if not all(c["ok"] for c in CHECKS):finish({"flag":"PRECONDITION"})
    # D-107: dos etapas. STAGE=prepare crea, verifica y publica el bundle de rollback
    # (~7,5 GiB: el pack del repo tiene 7,53 GiB) sin reescribir nada. STAGE=rewrite
    # purga, comprueba y publica la rama limpia. STAGE=all (por defecto) hace las dos.
    # Motivo: la subida del bundle es lenta y no debe comerse el techo del job.
    stage=os.environ.get("STAGE","all").lower()
    reuse=os.environ.get("REUSE_CLONE","").strip()
    if reuse and os.path.isdir(os.path.join(reuse,".git")):
        # D-106: el reescritor (filter-repo) CAMBIA el historial, asi que NUNCA debe tocar el
        # clon de trabajo compartido: se hace una COPIA local dentro de WORK_DIR.
        # D-109: la copia usa --shared (alternates): NO copia los 7,53 GiB de objetos (medido:
        # `git clone --local` tardaba 21 min y todavia copiaba; --shared es inmediato). Los
        # objetos NUEVOS de la reescritura se escriben en la copia y el push los lleva al
        # servidor; el clon original queda intacto y es el segundo copy del rollback.
        d=os.path.join(os.environ.get("WORK_DIR","/workspace/work"),"rw")
        # D-113: si el clon ya esta materializado (checkout completo de 338.007 ficheros, ~45 min)
        # se REUTILIZA en vez de volver a clonar. El bundle ya creado comparte los mismos
        # objetos; solo hay que reescribir el historial en esa copia.
        if os.path.isdir(os.path.join(d,".git")):
            sh(["git","-C",d,"fetch","--all","--tags","--prune"],check=False)
            sh(["git","-C",d,"checkout","--force",os.environ.get("TARGET_BRANCH") or need("GH_BRANCH")],cwd=d,check=False)
        else:
            shutil.rmtree(d,ignore_errors=True)
            sh(["git","clone","--shared",reuse,d])
        sh(["git","checkout","--force",os.environ.get("TARGET_BRANCH") or need("GH_BRANCH")],cwd=d)
    else:
        d=clone(os.path.join(os.environ.get("WORK_DIR","/workspace/work"),"m"),depth=0,branch=os.environ.get("TARGET_BRANCH") or need("GH_BRANCH"))
    # G4: sin aprobaciones ni firma. Gate = SHA256 del plan del Dataset.
    ker=yaml.safe_load((pathlib.Path(d)/"kernel/KERNEL.yaml").read_text())
    if not check("plan_sha256_matches",ker.get("plan_sha256")==plan["plan_sha256"],f"kernel={str(ker.get('plan_sha256'))[:12]} plan={str(plan['plan_sha256'])[:12]}"):finish({"flag":"PLAN_CHANGED"})
    # Ancla de rollback: la etiqueta de seguridad que NO se toca (la copia local reescribe
    # sus propias etiquetas, pero el bundle conserva el estado original y el servidor
    # conserva la etiqueta original porque aqui solo se publica la rama limpia).
    anchor=sh(["git","rev-parse","refs/tags/pre-reorg-20261104-kernel01"],cwd=d,check=False).stdout.strip()
    b=os.environ.get("BUNDLE_PATH") or os.path.join(os.environ.get("WORK_DIR","/workspace/work"),"backup.bundle")
    if stage in("all","prepare"):
        # El bundle se crea ANTES de reescribir: es el estado original (rama + etiqueta).
        sh(["git","bundle","create",b,"--all"],cwd=d)
        check("bundle_verified",sh(["git","bundle","verify",b],cwd=d,check=False).returncode==0)
        # D-34: huggingface_hub >= 2.x exige `path=` (con `path_or_fileobj=` lanza TypeError y el
        # bundle de rollback nunca se publica: fue lo que mato el job heredado 6aebc8980e0338d1bb804a42).
        # D-113: la firma real de huggingface_hub 2.x es upload_file(path_or_fileobj=...) con
        # keywords; `path=` no existe (TypeError: unexpected keyword argument 'path'). Se
        # intenta `path_or_fileobj` y, si la version no lo tiene, `path`. El token va SOLO en
        # la cabecera de la API (nunca en argv ni en la URL del fichero).
        api=HfApi(token=need("HF_TOKEN"))
        try:
            api.upload_file(path_or_fileobj=b,path_in_repo=f"backups/{RUN_ID}.bundle",repo_id=need("DATASET_REPO"),repo_type="dataset")
        except TypeError:
            api.upload_file(path=b,path_in_repo=f"backups/{RUN_ID}.bundle",repo_id=need("DATASET_REPO"),repo_type="dataset")
        check("bundle_uploaded",True)
        (OUT/"bundle_manifest.json").write_text(json.dumps({"bundle":b,"bytes":os.path.getsize(b),"sha256":sha256(b),"rollback_anchor":anchor},indent=1))
        if stage=="prepare":
            finish({"stage":"prepare","bundle_bytes":os.path.getsize(b),"bundle_sha256":sha256(b),"rollback_anchor":anchor})
    # --- etapa de reescritura ---
    check("bundle_verified",os.path.exists(b) and sh(["git","bundle","verify",b],cwd=d,check=False).returncode==0)
    pf=pathlib.Path(os.path.join(os.environ.get("WORK_DIR","/workspace/work"),"purge.txt"));pf.write_text("\n".join(plan["purge_paths"]))
    # D-116: `git filter-repo` BORRA el remoto `origin` al reescribir (por seguridad: evita
    # empujar el historial reescrito al remoto original). Por eso el push siguiente fallaba
    # con "fatal: 'origin' does not appear to be a git repository". Aqui se re-crea el remoto
    # con la URL LIMPIA (el token viaja solo en la cabecera extraheader del entorno).
    # Ademas, si la reescritura YA se aplico en esta copia (.git/filter-repo/already_ran) no se
    # repite: el job es idempotente y no gasta una reescritura completa de 338.007 ficheros.
    ya_reescrito=os.path.exists(os.path.join(d,".git","filter-repo","already_ran"))
    if ya_reescrito:
        check("rewrite_already_applied",True,"filter-repo ya_ran en esta copia: no se reescribe otra vez")
    else:
        sh(["git","filter-repo","--force","--invert-paths","--paths-from-file",str(pf)],cwd=d)
    sh(["git","remote","remove","origin"],cwd=d,check=False)
    sh(["git","remote","add","origin",f"https://github.com/{need('GH_REPO')}.git"],cwd=d,check=False)
    check("origin_ready",sh(["git","remote","get-url","origin"],cwd=d,check=False).returncode==0,
          sh(["git","remote","get-url","origin"],cwd=d,check=False).stdout.strip())
    # D-109: el check mira el HISTORIAL QUE SE PUBLICA (HEAD), no "--all": con --all el gate
    # seria imposible de satisfacer (las otras ramas y la etiqueta de seguridad DEBEN conservar
    # los 37 directorios purgados: son el punto de rollback). Lo que tiene que estar limpio es
    # la rama que se publica como main-clean.
    left=[p for p in plan["purge_paths"] if sh(["git","log","--oneline","-1","--",p],cwd=d).stdout.strip()]
    check("purged_absent_from_history",not left,left[:5])
    r=wc(d);check("wiring_check",r["ok"],[c["name"] for c in r["checks"] if not c["ok"]])
    if not all(c["ok"] for c in CHECKS):finish()
    sh(["git","push","origin","HEAD:refs/heads/main-clean","--force"],cwd=d);check("pushed_main-clean",True)
    kh=head(d);sz=sh(["git","count-objects","-vH"],cwd=d).stdout
    shutil.rmtree(d,ignore_errors=True)   # D-106/G3: la copia de reescritura se borra siempre
    finish({"size":sz,"stage":"rewrite","rollback_anchor":anchor,"swap_manual":"despues del swap con candado: git push --force-with-lease origin main-clean:main","note":"all commit hashes change; re-run j9_remirror; rotate any token that ever lived in history"},commit=kh)
if __name__=="__main__":run(main)
