from common import *
import yaml,pathlib
from j2_graph import build
from wiring_check import run as wc, es_tercero
def main():
    plan=json.load(open(dl("j4_plan","plan.json")))
    d=clone(os.path.join(os.environ.get("WORK_DIR","/workspace/work"),"a"));root=pathlib.Path(d)   # G2: scratch en WORK_DIR (NAS)
    # G4: NO hay bloque `approvals` ni firma humana (autonomy.human_signature=NOT_REQUIRED).
    # El gate es el SHA256 del plan publicado en el Dataset: si el plan cambio, el job no corre.
    ker=yaml.safe_load((root/"kernel/KERNEL.yaml").read_text())
    if not check("plan_sha256_matches",ker.get("plan_sha256")==plan["plan_sha256"],f"kernel={str(ker.get('plan_sha256'))[:12]} plan={str(plan['plan_sha256'])[:12]}"):
        finish({"flag":"PLAN_CHANGED"})
    # D-26: cache del conjunto "before" indexado por el sha del commit. El build del grafo
    # (~10 min sobre 374.205 ficheros) es determinista: cachear no altera el resultado.
    sha0=head(d);cf=pathlib.Path(os.path.join(os.environ.get("WORK_DIR","/workspace/work"),"before_unresolved.json"))
    if cf.exists() and json.loads(cf.read_text()).get("sha")==sha0:
        before={tuple(x) for x in json.loads(cf.read_text())["u"]};check("before_cached",True,f"cache hit {sha0[:12]}")
    else:
        before={tuple(u) for u in build(d)["unresolved"] if not u[0].startswith("_quarantine/")}
        cf.write_text(json.dumps({"sha":sha0,"u":[list(x) for x in before]}));check("before_cached",True,f"computed {sha0[:12]}")
    tag=f"pre-reorg-{RUN_ID}";br=f"reorg/{RUN_ID}"
    # D-33: el job es REEJECUTABLE. tag/branch/movimientos/commit ya hechos no pueden fallar:
    #   - tag: si existe se reapunta al HEAD (es el punto de rollback) y se re-pushea con --force
    #   - branch: checkout -B (no -b) para reutilizar la rama existente
    #   - git mv: si el path ya no existe (movido en una ejecucion previa) se ignora
    #   - commit: --allow-empty para que una reejecucion sin cambios no rompa la cadena
    # D-48: la tag ya existe en remoto (reejecucion) -> el push se hace SIEMPRE con --force:
    # sin el, el push se rechaza ("already exists") y el job muere con rc=1.
    if sh(["git","rev-parse","-q","--verify",f"refs/tags/{tag}"],cwd=d,check=False).stdout.strip():
        sh(["git","tag","-f",tag],cwd=d)
    else:
        sh(["git","tag",tag],cwd=d)
    sh(["git","push","origin","--force",tag],cwd=d)
    sh(["git","checkout","-B",br],cwd=d)
    for p in plan["quarantine"]:
        dst=root/"_quarantine"/p;dst.parent.mkdir(parents=True,exist_ok=True)
        sh(["git","mv",p,str(dst.relative_to(root))],cwd=d,check=False)
    for p in plan["untrack"]:sh(["git","rm","-r","--cached","-q","--ignore-unmatch",p],cwd=d)
    gi=root/".gitignore";old=gi.read_text() if gi.exists() else ""
    gi.write_text(old+"".join(f"\n{p}/" for p in plan["untrack"] if p+"/" not in old));sh(["git","add",".gitignore"],cwd=d)
    g_after=build(d)  # D-39: un solo build; su resultado se reutiliza en wiring_check
    after={tuple(u) for u in g_after["unresolved"] if not u[0].startswith("_quarantine/")}
    # D-25: las referencias nuevas que deja el untrack de los 37 directorios build/ estan en el
    # codigo de TERCEROS vendorizado (misma regla que D-18): se INFORMAN; solo el codigo propio bloquea.
    new_all=sorted(after-before);new_own=[u for u in new_all if not es_tercero(u[0])]
    check("no_new_unresolved_vs_before",not new_own,f"{len(new_all)} de terceros (informativo), {len(new_own)} propios: {new_own[:3]}")
    check("third_party_unresolved_reported",True,f"{len(new_all)} referencias nuevas en codigo de terceros")
    # D-24: la guia declara el gate entrypoints_exist en S5_j5 pero su codigo no lo implementaba.
    eps=(yaml.safe_load((root/"kernel/KERNEL.yaml").read_text()).get("entrypoints") or [])
    miss=[p for p in eps if not (root/p).exists()]
    check("entrypoints_exist",not miss,miss[:5])
    r=wc(d,g_after);check("wiring_check",r["ok"],[c["name"] for c in r["checks"] if not c["ok"]])
    tc=os.environ.get("TEST_CMD")
    if tc:
        # D-36: el Space RIU se redespliega cada ~60 s (autosync) -> /health devuelve 503 durante
        # el redesplie. Se reintenta hasta 5 veces (30 s) antes de dar el gate por fallido.
        rc=1
        for _try in range(5):
            rc=subprocess.run(tc,shell=True,cwd=d).returncode
            if rc==0: break
            time.sleep(30)
        check("TEST_CMD_rc0",rc==0,tc)
    else:check("TEST_CMD_set",False,"set TEST_CMD (real backend start + smoke)")
    if not all(c["ok"] for c in CHECKS):finish({"rollback":f"git checkout main; branch {br} discarded; tag {tag}"})
    sh(["git","-c","user.name=kernel-bot","-c","user.email=bot@local","commit","--allow-empty","-qm",f"reorg {RUN_ID}: quarantine {len(plan['quarantine'])}, untrack {len(plan['untrack'])}"],cwd=d)
    sh(["git","push","origin",br],cwd=d)
    check("branch_pushed",True,br)
    finish({"branch":br,"tag":tag,"rollback":f"git push origin HEAD:main from tag {tag} (never automatic)"},commit=head(d))
if __name__=="__main__":run(main)
