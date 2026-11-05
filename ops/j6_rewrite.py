from common import *
import yaml,pathlib
from wiring_check import run as wc
def main():
    from huggingface_hub import HfApi
    plan=json.load(open(dl("j4_plan","plan.json")))
    for j in("j5_apply","j8_audit"):check(f"{j}_PASS",json.load(open(dl(j,"result.json")))["status"]=="PASS")
    if not all(c["ok"] for c in CHECKS):finish({"flag":"PRECONDITION"})
    d=clone("/tmp/m",depth=0,branch=os.environ.get("TARGET_BRANCH") or need("GH_BRANCH"))
    ap=yaml.safe_load((pathlib.Path(d)/"kernel/KERNEL.yaml").read_text())["approvals"]["J6_rewrite"]
    if not check("approval_matches_plan",ap.get("approved") is True and ap.get("plan_sha256")==plan["plan_sha256"]):finish({"flag":"APPROVAL_REQUIRED"})
    b="/tmp/backup.bundle";sh(["git","bundle","create",b,"--all"],cwd=d)
    check("bundle_verified",sh(["git","bundle","verify",b],cwd=d,check=False).returncode==0)
    # D-34: huggingface_hub >= 2.x exige `path=` (con `path_or_fileobj=` lanza TypeError y el
    # bundle de rollback nunca se publica: fue lo que mato el job heredado 6aebc8980e0338d1bb804a42).
    HfApi(token=need("HF_TOKEN")).upload_file(path=b,path_in_repo=f"backups/{RUN_ID}.bundle",repo_id=need("DATASET_REPO"),repo_type="dataset")
    check("bundle_uploaded",True)
    if not all(c["ok"] for c in CHECKS):finish()
    pf=pathlib.Path("/tmp/purge.txt");pf.write_text("\n".join(plan["purge_paths"]))
    sh(["git","filter-repo","--force","--invert-paths","--paths-from-file",str(pf)],cwd=d)
    # D-34: `git remote add` falla (rc=128) si origin ya existe: se usa set-url (idempotente).
    sh(["git","remote","set-url","origin",f"https://github.com/{need('GH_REPO')}.git"],cwd=d,check=False)
    left=[p for p in plan["purge_paths"] if sh(["git","log","--all","--oneline","-1","--",p],cwd=d).stdout.strip()]
    check("purged_absent_from_history",not left,left[:5])
    r=wc(d);check("wiring_check",r["ok"],[c["name"] for c in r["checks"] if not c["ok"]])
    if not all(c["ok"] for c in CHECKS):finish()
    sh(["git","push","origin","HEAD:refs/heads/main-clean","--force"],cwd=d);check("pushed_main-clean",True)
    sz=sh(["git","count-objects","-vH"],cwd=d).stdout
    finish({"size":sz,"swap_manual":"after approvals.merge_main: git push --force-with-lease origin main-clean:main","note":"all commit hashes change; re-run j9_remirror; rotate any token that ever lived in history"},commit=head(d))
if __name__=="__main__":run(main)
