from common import *
import yaml,pathlib
from j2_graph import build
from wiring_check import run as wc
def main():
    plan=json.load(open(dl("j4_plan","plan.json")))
    d=clone("/tmp/a");root=pathlib.Path(d)
    ap=yaml.safe_load((root/"kernel/KERNEL.yaml").read_text())["approvals"]["J5_apply"]
    if not check("approval_matches_plan",ap.get("approved") is True and ap.get("plan_sha256")==plan["plan_sha256"],"approval missing or plan changed"):
        finish({"flag":"APPROVAL_REQUIRED"})
    before={tuple(u) for u in build(d)["unresolved"]}
    tag=f"pre-reorg-{RUN_ID}";br=f"reorg/{RUN_ID}"
    sh(["git","tag",tag],cwd=d);sh(["git","push","origin",tag],cwd=d)
    sh(["git","checkout","-b",br],cwd=d)
    for p in plan["quarantine"]:
        dst=root/"_quarantine"/p;dst.parent.mkdir(parents=True,exist_ok=True);sh(["git","mv",p,str(dst.relative_to(root))],cwd=d)
    for p in plan["untrack"]:sh(["git","rm","-r","--cached","-q","--ignore-unmatch",p],cwd=d)
    gi=root/".gitignore";old=gi.read_text() if gi.exists() else ""
    gi.write_text(old+"".join(f"\n{p}/" for p in plan["untrack"] if p+"/" not in old));sh(["git","add",".gitignore"],cwd=d)
    after={tuple(u) for u in build(d)["unresolved"] if not u[0].startswith("_quarantine/")}
    check("no_new_unresolved_vs_before",after<=before,sorted(after-before)[:5])
    # D-24: la guia declara el gate entrypoints_exist en S5_j5 pero su codigo no lo implementaba.
    eps=(yaml.safe_load((root/"kernel/KERNEL.yaml").read_text()).get("entrypoints") or [])
    miss=[p for p in eps if not (root/p).exists()]
    check("entrypoints_exist",not miss,miss[:5])
    r=wc(d);check("wiring_check",r["ok"],[c["name"] for c in r["checks"] if not c["ok"]])
    tc=os.environ.get("TEST_CMD")
    if tc:check("TEST_CMD_rc0",subprocess.run(tc,shell=True,cwd=d).returncode==0,tc)
    else:check("TEST_CMD_set",False,"set TEST_CMD (real backend start + smoke)")
    if not all(c["ok"] for c in CHECKS):finish({"rollback":f"git checkout main; branch {br} discarded; tag {tag}"})
    sh(["git","-c","user.name=kernel-bot","-c","user.email=bot@local","commit","-qm",f"reorg {RUN_ID}: quarantine {len(plan['quarantine'])}, untrack {len(plan['untrack'])}"],cwd=d)
    sh(["git","push","origin",br],cwd=d)
    check("branch_pushed",True,br)
    finish({"branch":br,"tag":tag,"rollback":f"git push origin HEAD:main from tag {tag} (never automatic)"},commit=head(d))
if __name__=="__main__":run(main)
