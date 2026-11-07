import os, sys, json, subprocess, pathlib
if os.environ.get("OWNER_GATE")!="APPROVE_N5": sys.exit("N5: owner_gate no aprobado")
OUT=pathlib.Path("out/N5"); OUT.mkdir(parents=True,exist_ok=True)
if (OUT/"ff.json").exists(): sys.exit("N5: output exists, abort")
def sh(a): return subprocess.run(a,capture_output=True,text=True)
res={"checks":[]}
mc=sh(["git","ls-remote","origin","refs/heads/main-clean"]).stdout.split()[0]
m=sh(["git","ls-remote","origin","refs/heads/main"]).stdout.split()[0]
anc=sh(["git","merge-base","--is-ancestor",mc,m]).returncode==0
res["checks"].append({"name":"main_clean_le_main","ok":anc,"detail":f"main-clean={mc[:12]} main={m[:12]}"})
res["checks"].append({"name":"lease_read","ok":bool(mc and m),"detail":f"lease={mc[:12]}"})
# D-152 (centinela G5): ABORTAR si la ancestria falla. El motor original hacia el push
# destructivo aunque su propio check fallase (main-clean divergente).
if not anc:
    res["ok"]=False
    (OUT/"ff.json").write_text(json.dumps(res,indent=2)); sys.exit(1)
p=sh(["git","push","origin",f"{m}:refs/heads/main-clean",f"--force-with-lease=refs/heads/main-clean:{mc}"])
res["checks"].append({"name":"ff_rc0","ok":p.returncode==0,"detail":(p.stdout+p.stderr)[-200:]})
res["checks"].append({"name":"main_after_equals_main_clean","ok":sh(["git","ls-remote","origin","refs/heads/main-clean"]).stdout.split()[0]==m})
res["ok"]=all(c["ok"] for c in res["checks"])
(OUT/"ff.json").write_text(json.dumps(res,indent=2))
sys.exit(0 if res["ok"] else 1)
