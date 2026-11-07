import os, sys, json, hashlib, subprocess, pathlib
IB = pathlib.Path("input_block_verbatim.yaml")
DSL = pathlib.Path("dag.json")
OUT = pathlib.Path("out/N0"); OUT.mkdir(parents=True, exist_ok=True)
if (OUT/"validate.json").exists():
    sys.exit("N0: output exists, abort (no_overwrite)")
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
ib_sha = sha(IB)
dsl = json.loads(DSL.read_text())
res = {"input_block_sha256": ib_sha, "checks": []}
res["checks"].append({"name":"input_block_sha256_ok","ok":len(ib_sha)==64})
res["checks"].append({"name":"dsl_schema_ok","ok":dsl.get("dsl_version")=="1.0" and "nodes" in dsl})
# leer shas remotos reales
def ls(ref):
    r = subprocess.run(["git","ls-remote","origin",ref],capture_output=True,text=True)
    return r.stdout.split()[0] if r.stdout.strip() else ""
res["remote"] = {"main": ls("refs/heads/main"), "main_clean": ls("refs/heads/main-clean")}
res["checks"].append({"name":"remote_shas_read","ok":bool(res["remote"]["main"])})
dsl["input_block_sha256"] = ib_sha
DSL.write_text(json.dumps(dsl, indent=2))  # solo rellena el placeholder
res["ok"] = all(c["ok"] for c in res["checks"])
(OUT/"validate.json").write_text(json.dumps(res, indent=2))
sys.exit(0 if res["ok"] else 1)
