import argparse
import hashlib
import json
import os
import re
from pathlib import Path

def canon(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"))

def digest(value):
    return hashlib.sha256(value.encode("utf-8")).hexdigest()

def confined(root, relative):
    if not isinstance(relative, str) or not relative or Path(relative).is_absolute():
        raise ValueError("Ruta no relativa")
    target = (root / relative).resolve()
    if not target.is_relative_to(root):
        raise ValueError("Ruta fuera del workspace")
    return target

def validate(doc, policy):
    if not isinstance(doc, dict) or not isinstance(doc.get("meta"), dict):
        raise ValueError("Falta meta")
    job = doc["meta"].get("name", "")
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,48}", job):
        raise ValueError("meta.name invalido")
    ops = doc.get("ops")
    if not isinstance(ops, list) or not 1 <= len(ops) <= policy["max_ops"]:
        raise ValueError("Cantidad invalida")
    allowed = set(policy["allowed_ops"])
    seen = set()
    for item in ops:
        if item["id"] in seen:
            raise ValueError("ID duplicado")
        seen.add(item["id"])
        if item.get("op") not in allowed:
            raise ValueError("Operacion no autorizada")
        deps = item.get("depends_on", [])
        for dep in deps:
            if dep not in seen and dep not in [o["id"] for o in ops]:
                raise ValueError("Dependencia ausente")
    index = {x["id"]: x for x in ops}
    active, done = set(), set()
    def visit(node):
        if node in active: raise ValueError("Ciclo en DAG")
        if node in done: return
        active.add(node)
        for d in index[node].get("depends_on", []):
            visit(d)
        active.remove(node)
        done.add(node)
    for node in index: visit(node)
    return job, ops

async def operate_async(root, item):
    name = item["op"]
    if name == "inspect_workspace":
        return {"items": sorted(x.name for x in root.iterdir())[:100]}
    if name == "finish":
        return {"message": "Operaciones completadas"}
    path = confined(root, item["path"])
    if name == "create_directory":
        path.mkdir(parents=True, exist_ok=True)
        return {"path": item["path"], "exists": True}
    if name == "write_text":
        content = item["text"]
        if path.exists() and path.read_text(encoding="utf-8") != content:
            raise ValueError("Se rechaza sobrescribir contenido distinto")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return {"path": item["path"], "sha256": digest(content)}
    if name == "read_text":
        content = path.read_text(encoding="utf-8")
        return {"path": item["path"], "sha256": digest(content)}
    if name == "verify_exists":
        if not path.is_file(): raise AssertionError("Archivo inexistente")
        return {"path": item["path"], "verified": True}
    if name == "verify_contains":
        if item["text"] not in path.read_text(encoding="utf-8"): raise AssertionError("Texto ausente")
        return {"path": item["path"], "verified": True}
    raise ValueError("No implementado")

def still_valid(root, item, receipt):
    if item["op"] == "create_directory":
        return confined(root, item["path"]).is_dir()
    if item["op"] == "write_text":
        target = confined(root, item["path"])
        return target.is_file() and digest(target.read_text(encoding="utf-8")) == receipt.get("sha256")
    if item["op"] in ("verify_exists", "verify_contains", "read_text"):
        return True
    return False

class PersistenceEngine:
    def __init__(self, root, policy):
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        self.policy = policy

    async def run_async(self, doc):
        job, operations = validate(doc, self.policy)
        checksum = digest(canon(doc))
        cp_dir = self.root / ".receipts"
        cp_dir.mkdir(exist_ok=True)
        cp = cp_dir / (job + ".json")
        state = {"plan_sha256": checksum, "done": {}}
        if cp.exists():
            state = json.loads(cp.read_text(encoding="utf-8"))
            if state["plan_sha256"] != checksum:
                raise ValueError("Cambio de plan")

        pending = {x["id"]: x for x in operations}
        completed = set()
        receipts = []

        while pending:
            ready = next((x for x in operations if x["id"] in pending and set(x.get("depends_on", [])).issubset(completed)), None)
            if not ready: raise ValueError("DAG bloqueado")

            rid = ready["id"]
            old = state["done"].get(rid)
            if old and still_valid(self.root, ready, old):
                result = old
            else:
                result = await operate_async(self.root, ready)
                state["done"][rid] = result
                cp.write_text(json.dumps(state, indent=2), encoding="utf-8")

            completed.add(rid)
            receipts.append({"id": rid, "op": ready["op"], "result": result})
            del pending[rid]

        return {"ok": True, "receipts": receipts}
