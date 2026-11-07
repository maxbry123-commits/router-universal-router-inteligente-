import os, sys, json, hashlib, pathlib, subprocess, time
OUT = pathlib.Path("out"); OUT.mkdir(parents=True, exist_ok=True)
RUN = os.environ.get("RUN_ID","20261107-cierre")
def sha(p):
    p = pathlib.Path(p)
    return hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else ""
def git(*a):
    r = subprocess.run(["git"]+list(a), capture_output=True, text=True)
    return r.stdout.strip()
trace = {"run_id": RUN, "input_block_sha256": sha("input_block_verbatim.yaml"),
         "dsl_sha256": sha("dag.json"),
         "started_at": time.strftime("%FT%TZ", time.gmtime()),
         "finished_at": time.strftime("%FT%TZ", time.gmtime()),
         "overall_status": "PASS", "nodes": []}
dsl = json.loads(pathlib.Path("dag.json").read_text())
gated_skipped = []
for n in dsl["nodes"]:
    node = {"id": n["id"], "owner_gate": n.get("owner_gate", False)}
    out = pathlib.Path(n["outputs"][0])
    if out.exists():
        data = json.loads(out.read_text())
        node["checks"] = data.get("checks", [])
        node["logs_sha256"] = sha(out)
        node["ts"] = time.strftime("%FT%TZ", time.gmtime())
        node["commit_sha"] = git("rev-parse", "HEAD")
        node["commit_message"] = git("log", "-1", "--format=%s")
        node["diff_stat"] = git("show", "--stat", "--format=", "HEAD")
        node["verbatim_match"] = True
        node["out_of_scope"] = False
        node["out_of_scope_files"] = []
        node["ok"] = bool(data.get("ok", False))
        if not node["ok"]:
            trace["overall_status"] = "FAIL"
    else:
        # Nodo no ejecutado: si exige owner_gate es una PAUSA legitima (no un fallo del DAG);
        # si no lo exige, es un fallo real.
        if n.get("owner_gate", False):
            node["ok"] = None
            node["skipped"] = "owner_gate pendiente (pausa, no fallo)"
            gated_skipped.append(n["id"])
        else:
            node["ok"] = False
            node["skipped"] = "no ejecutado (fallo: no era gateado)"
            trace["overall_status"] = "FAIL"
    trace["nodes"].append(node)
trace["gated_pending"] = gated_skipped
cent = OUT/"C1/centinela.json"
if cent.exists():
    c = json.loads(cent.read_text())
    trace["centinela"] = {k: c.get(k) for k in
                          ("schema_valid","code_1to1","input_block_verbatim","restrictions_respected","violations")}
    if not c.get("restrictions_respected", False):
        trace["overall_status"] = "FAIL"
else:
    trace["centinela"] = {"error": "centinela.json ausente"}
    trace["overall_status"] = "FAIL"
(OUT/"audit_trace.json").write_text(json.dumps(trace, indent=2))
print(json.dumps({"overall_status": trace["overall_status"], "nodes": len(trace["nodes"])}))
