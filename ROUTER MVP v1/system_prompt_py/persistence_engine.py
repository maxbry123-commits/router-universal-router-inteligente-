import argparse, hashlib, json, os, re
from pathlib import Path

def canon(value): return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
def digest(value): return hashlib.sha256(value.encode("utf-8")).hexdigest()
def confined(root, relative):
    if not isinstance(relative, str) or not relative or Path(relative).is_absolute(): raise ValueError("Ruta no relativa")
    target = (root / relative).resolve()
    if not target.is_relative_to(root): raise ValueError("Ruta fuera del workspace")
    return target

def validate(doc, policy):
    if not isinstance(doc, dict) or not isinstance(doc.get("meta"), dict): raise ValueError("Falta meta")
    job = doc["meta"].get("name", "")
    if not isinstance(job, str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,48}", job): raise ValueError("meta.name invalido")
    ops = doc.get("ops")
    if not isinstance(ops, list) or not 1 <= len(ops) <= policy["max_ops"]: raise ValueError("Cantidad de operaciones invalida")
    allowed = set(policy["allowed_ops"])
    seen = set()
    for item in ops:
        if not isinstance(item, dict) or not isinstance(item.get("id"), str): raise ValueError("Cada operacion requiere id")
        if item["id"] in seen: raise ValueError("ID duplicado")
        seen.add(item["id"])
        if item.get("op") not in allowed: raise ValueError("Operacion no autorizada: " + str(item.get("op")))
        deps = item.get("depends_on", [])
        if not isinstance(deps, list) or any(not isinstance(d, str) for d in deps): raise ValueError("depends_on invalido")
        if item["op"] in ("create_directory", "write_text", "read_text", "verify_exists", "verify_contains"):
            if not isinstance(item.get("path"), str): raise ValueError("Falta path")
        if item["op"] == "write_text":
            if not isinstance(item.get("text"), str) or len(item["text"]) > policy["max_text_chars"]: raise ValueError("Texto invalido o demasiado largo")
        if item["op"] == "verify_contains" and not isinstance(item.get("text"), str): raise ValueError("Falta texto a verificar")
    index = {x["id"]: x for x in ops}
    for item in ops:
        for dep in item.get("depends_on", []):
            if dep not in index or dep == item["id"]: raise ValueError("Dependencia ausente o propia")
    active, done = set(), set()
    def visit(node):
        if node in active: raise ValueError("Ciclo en DAG")
        if node in done: return
        active.add(node)
        for d in index[node].get("depends_on", []): visit(d)
        active.remove(node); done.add(node)
    for node in index: visit(node)
    return job, ops

def operate(root, item):
    name = item["op"]
    if name == "inspect_workspace": return {"items": sorted(x.name for x in root.iterdir())[:100]}
    if name == "finish": return {"message": "Operaciones completadas"}
    path = confined(root, item["path"])
    if name == "create_directory":
        path.mkdir(parents=True, exist_ok=True)
        return {"path": item["path"], "exists": path.is_dir()}
    if name == "write_text":
        content = item["text"]
        if not path.parent.is_dir(): raise ValueError("Directorio padre no existe")
        if path.exists() and path.read_text(encoding="utf-8") != content: raise ValueError("Se rechaza sobrescribir contenido diferente")
        path.write_text(content, encoding="utf-8")
        return {"path": item["path"], "sha256": digest(content)}
    if name == "read_text":
        content = path.read_text(encoding="utf-8")
        return {"path": item["path"], "sha256": digest(content), "preview": content[:400]}
    if name == "verify_exists":
        if not path.is_file(): raise AssertionError("Archivo inexistente")
        return {"path": item["path"], "verified": True}
    if name == "verify_contains":
        if item["text"] not in path.read_text(encoding="utf-8"): raise AssertionError("Texto esperado ausente")
        return {"path": item["path"], "verified": True}
    raise ValueError("Operacion no implementada")

def still_valid(root, item, receipt):
    if item["op"] == "create_directory": return confined(root, item["path"]).is_dir()
    if item["op"] == "write_text":
        target = confined(root, item["path"])
        return target.is_file() and digest(target.read_text(encoding="utf-8")) == receipt.get("sha256")
    return False

def atomic_json(path, content):
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(content, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp, path)

def main():
    cli = argparse.ArgumentParser()
    cli.add_argument("plan"); cli.add_argument("--policy", required=True); cli.add_argument("--root", required=True)
    args = cli.parse_args()
    root = Path(args.root).resolve(); root.mkdir(parents=True, exist_ok=True)
    report = {"ok": False, "ops_total": 0, "completed": [], "errors": []}
    try:
        policy = json.loads(Path(args.policy).read_text(encoding="utf-8"))
        doc = json.loads(Path(args.plan).read_text(encoding="utf-8"))
        job, operations = validate(doc, policy)
        report["ops_total"] = len(operations)
        checksum = digest(canon(doc))
        cp_dir = root / ".receipts"; cp_dir.mkdir(exist_ok=True)
        cp = cp_dir / (job + ".json")
        state = {"plan_sha256": checksum, "done": {}}
        if cp.exists():
            state = json.loads(cp.read_text(encoding="utf-8"))
            if state["plan_sha256"] != checksum: raise ValueError("Cambio de plan: requiere nuevo meta.name")
        pending = {x["id"]: x for x in operations}; completed = set()
        while pending:
            ready = next((x for x in operations if x["id"] in pending and set(x.get("depends_on", [])).issubset(completed)), None)
            if ready is None: raise ValueError("DAG sin nodos listos")
            rid = ready["id"]; old = state["done"].get(rid)
            if old and still_valid(root, ready, old): result = old
            else:
                result = operate(root, ready)
                state["done"][rid] = result
                atomic_json(cp, state)
            completed.add(rid); report["completed"].append({"id": rid, "op": ready["op"], "receipt": result}); del pending[rid]
        report["ok"] = True
    except Exception as exc:
        report["errors"].append({"type": type(exc).__name__, "message": str(exc)})
    print("ENGINE_REPORT " + canon(report))
    return 0 if report["ok"] else 1

if __name__ == "__main__": raise SystemExit(main())
