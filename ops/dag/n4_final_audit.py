import os, sys, json, pathlib
if os.environ.get("OWNER_GATE")!="APPROVE_N4": sys.exit("N4: owner_gate no aprobado")
OUT=pathlib.Path("out/N4"); OUT.mkdir(parents=True,exist_ok=True)
if (OUT/"final_audit.json").exists(): sys.exit("N4: output exists, abort")
# delega en el job existente, no reinventa
r=os.system("python ops/j10_final_audit.py")
(OUT/"final_audit.json").write_text(json.dumps({"ok":r==0,"rc":r},indent=2))
sys.exit(0 if r==0 else 1)
