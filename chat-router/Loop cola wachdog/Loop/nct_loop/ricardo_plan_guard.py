"""Validador de admisión para el motor declarativo Ricardo de REFERENCIA.
NO ejecuta operaciones. Aplicar antes de usar referencia_ricardo/motor_cli.py.
"""
from __future__ import annotations
import hashlib
import json
import re
from pathlib import PurePosixPath

class RicardoGuardError(ValueError):
    pass

SENSITIVE = frozenset({".git", ".env", "secrets", "secret", "credentials", "tokens", "keys"})
MUTATING = frozenset({"write_text", "create_directory"})
SAFE_OPS = frozenset({"inspect_workspace", "create_directory", "write_text", "read_text", "verify_exists", "verify_contains", "finish"})

def _safe(path):
    if not isinstance(path, str) or not path or path.startswith("/") or "\\" in path or ":" in path or "\x00" in path:
        raise RicardoGuardError("PATH_OUT_OF_SCOPE")
    chunks = path.split("/")
    if any(x in {"", ".", ".."} or x.lower() in SENSITIVE for x in chunks):
        raise RicardoGuardError("PATH_OUT_OF_SCOPE")
    if chunks[-1].lower().startswith(".env") or chunks[-1].lower().endswith((".pem", ".key", ".p12")):
        raise RicardoGuardError("SENSITIVE_TARGET")
    return str(PurePosixPath(path))

def inspect_plan(doc: dict, policy: dict, *, allowed_write_paths: list[str] | None = None) -> dict:
    """Comprueba allowlist EXACTA del motor original, DAG, rutas y límites.

    `allowed_write_paths=None` significa SOLO lectura; no equivale a "todo".
    Debe llamarse de nuevo en el host inmediatamente antes de ejecutar.
    """
    if not isinstance(doc, dict) or not isinstance(policy, dict):
        raise RicardoGuardError("BAD_INPUT")
    allowed = policy.get("allowed_ops")
    if not isinstance(allowed, list) or not allowed or any(not isinstance(x, str) for x in allowed):
        raise RicardoGuardError("BAD_POLICY")
    n = policy.get("max_ops", 32)
    ops = doc.get("ops")
    if not isinstance(ops, list) or not 1 <= len(ops) <= n:
        raise RicardoGuardError("OPS_LIMIT")
    roots = allowed_write_paths if allowed_write_paths is not None else []
    if not isinstance(roots, list):
        raise RicardoGuardError("BAD_ROOTS")
    roots = [_safe(p) for p in roots]
    graph = {}
    writes = []
    for item in ops:
        if not isinstance(item, dict) or not isinstance(item.get("id"), str) or not re.fullmatch(r"[\w-]{1,80}", item["id"]):
            raise RicardoGuardError("BAD_OP_ID")
        oid, action = item["id"], item.get("op")
        if oid in graph:
            raise RicardoGuardError("DUPLICATE_OP_ID")
        if action not in allowed or action not in SAFE_OPS:
            raise RicardoGuardError("OP_NOT_ALLOWLISTED")
        deps = item.get("depends_on", [])
        if not isinstance(deps, list) or any(not isinstance(x, str) for x in deps) or len(deps) != len(set(deps)):
            raise RicardoGuardError("BAD_DEPENDENCIES")
        graph[oid] = deps
        if "path" in item:
            p = _safe(item["path"])
            if action in MUTATING:
                if not any(p == r or p.startswith(r.rstrip("/") + "/") for r in roots):
                    raise RicardoGuardError("WRITER_SCOPE_REQUIRED")
                writes.append(p)
        elif action in MUTATING:
            raise RicardoGuardError("WRITE_WITHOUT_PATH")
        if action == "write_text" and (not isinstance(item.get("text"), str) or len(item["text"]) > policy.get("max_text_chars", 10000)):
            raise RicardoGuardError("TEXT_LIMIT")
    visiting, visited = set(), set()
    def visit(x):
        if x not in graph:
            raise RicardoGuardError("DEPENDENCY_MISSING")
        if x in visiting:
            raise RicardoGuardError("CYCLIC_DAG")
        if x in visited:
            return
        visiting.add(x)
        for dep in graph[x]:
            visit(dep)
        visiting.remove(x)
        visited.add(x)
    for key in graph:
        visit(key)
    raw = json.dumps(doc, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return {"ok": True, "plan_sha256": hashlib.sha256(raw).hexdigest(),
            "ops": len(ops), "mutating_paths": sorted(set(writes)),
            "requires_n4_approval": bool(writes), "executed": False}
