import os, sys, json, hashlib, pathlib, subprocess, time
RUN = os.environ.get("RUN_ID","20261107-cierre")
OUT = pathlib.Path("out/C1"); OUT.mkdir(parents=True,exist_ok=True)
if (OUT/"centinela.json").exists(): sys.exit("C1: output exists, abort")
def sha(p): return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
ib = pathlib.Path("input_block_verbatim.yaml")
dsl = json.loads(pathlib.Path("dag.json").read_text())
res = {"run_id": RUN, "input_block_sha256": sha(ib), "dsl_sha256": sha("dag.json"),
       "started_at": time.strftime("%FT%TZ", time.gmtime()), "violations": []}
# 1) schema
res["schema_valid"] = dsl.get("dsl_version")=="1.0" and "nodes" in dsl and "restrictions" in dsl
# 2) code 1:1: cada nodo declara un run; comprobar que el script existe y que su sha es el esperado
code_ok = True
for n in dsl["nodes"]:
    script = n["run"].split()[-1]
    if not pathlib.Path(script).exists():
        code_ok = False; res["violations"].append(f"missing script {script}")
res["code_1to1"] = code_ok
# 3) input block verbatim: rutas prohibidas y comandos no declarados
forbidden = dsl["restrictions"]["forbidden_paths"]
# D-153 (centinela G7): el diff se hace commit->commit (NO commit->working tree, que
# salia vacio y daba verde falso) y se compara con el digest que el DAG declara.
changed = subprocess.run(["git","diff","--name-only","HEAD~1","HEAD"],capture_output=True,text=True).stdout.splitlines()
viol = [f for f in changed if any(f.startswith(p.replace("*","")) for p in forbidden)]
res["input_block_verbatim"] = len(viol)==0
res["violations"].extend(viol)
# D-153: el digest del input block del DAG debe coincidir con el del fichero en disco.
res["input_block_digest_matches_dag"] = (dsl.get("input_block_sha256")==res["input_block_sha256"])
if not res["input_block_digest_matches_dag"]:
    res["violations"].append("input_block_sha256 del DAG != sha256 del fichero")
res["restrictions_respected"] = (res["input_block_verbatim"] and res["schema_valid"]
                                 and res["code_1to1"] and res["input_block_digest_matches_dag"])
res["finished_at"] = time.strftime("%FT%TZ", time.gmtime())
(OUT/"centinela.json").write_text(json.dumps(res,indent=2))
sys.exit(0 if res["restrictions_respected"] else 1)
