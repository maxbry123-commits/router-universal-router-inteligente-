"""YAIWES DSL v1: contracts, verbatim integrity, DAG and safe predicates.
Only Python stdlib. This module has NO side effects and never executes skills.
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import PurePosixPath
from typing import Any, Mapping

ID = re.compile(r"^[A-Za-z0-9_-]{1,80}$")
SHA = re.compile(r"^[0-9a-f]{64}$")
REF = re.compile(r"^ancla:[A-Za-z0-9_.-]{1,120}$")
ROLES = {"arquitecto", "auditor", "ejecutor_codigo", "frontend", "refactor_revision"}
CATEGORIES = {"constitucion", "auditoria", "investigacion", "arquitectura", "componentes", "backend", "frontend", "canvas", "verificacion", "refactoria", "github", "continuidad"}
PREDICATES = {"always", "source_exists", "file_type_is", "requires_frontend", "requires_backend", "component_present", "prior_status", "approved_scope"}
STEP_KINDS = {"MODEL", "TOOL", "CHECK"}
READ_OPS = {"inspect_workspace", "read_text", "verify_exists", "verify_contains"}
WRITE_OPS = {"create_directory", "write_text"}
OPS = READ_OPS | WRITE_OPS | {"finish"}
TOP_FIELDS = {"schema", "id", "loop_id", "name", "category", "enabled", "note", "role", "source", "input_block_verbatim", "attachments", "depends_on", "when", "execution", "steps", "outputs", "on_pass", "on_not_applicable", "on_blocked"}

class ContractError(ValueError):
    def __init__(self, code: str, detail: str = ""):
        super().__init__(code + (": " + detail if detail else ""))
        self.code, self.detail = code, detail

def canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")

def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def _fields(obj: Any, allowed: set[str], required: set[str], label: str) -> None:
    if not isinstance(obj, dict):
        raise ContractError("BAD_TYPE", label)
    if missing := required - obj.keys():
        raise ContractError("MISSING_FIELD", label + " " + ",".join(sorted(missing)))
    if unknown := obj.keys() - allowed:
        raise ContractError("UNKNOWN_FIELD", label + " " + ",".join(sorted(unknown)))

def _id(value: Any, label: str) -> str:
    if not isinstance(value, str) or not ID.fullmatch(value):
        raise ContractError("BAD_ID", label)
    return value

def _safe_path(p: Any) -> str:
    if not isinstance(p, str) or not p or p.startswith("/") or "\\" in p or "\x00" in p:
        raise ContractError("PATH_OUT_OF_SCOPE", str(p)[:90])
    path = PurePosixPath(p)
    if ":" in p or any(x in ("..", ".") for x in p.split("/")):
        raise ContractError("PATH_OUT_OF_SCOPE", p[:90])
    return str(path)

def load_contract(raw: bytes | str) -> dict:
    if isinstance(raw, str):
        raw = raw.encode("utf-8")
    if not isinstance(raw, bytes) or len(raw) > 256_000:
        raise ContractError("BAD_CONTRACT_SIZE")
    try:
        obj = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ContractError("INVALID_JSON", str(exc)[:100]) from exc
    validate_contract(obj)
    return obj

def validate_contract(c: Any, *, source_bytes: bytes | None = None) -> dict:
    _fields(c, TOP_FIELDS, TOP_FIELDS - {"note", "attachments", "depends_on", "when", "on_not_applicable", "on_pass", "on_blocked"}, "trigger")
    if c["schema"] != "yaiwes.trigger.v1":
        raise ContractError("UNKNOWN_SCHEMA")
    _id(c["id"], "id"); _id(c["loop_id"], "loop_id")
    if not isinstance(c["name"], str) or not c["name"].strip() or len(c["name"]) > 150:
        raise ContractError("BAD_NAME")
    if c["category"] not in CATEGORIES or c["role"] not in ROLES:
        raise ContractError("BAD_CATEGORY_OR_ROLE")
    if type(c["enabled"]) is not bool:
        raise ContractError("BAD_ENABLED")
    if not isinstance(c.get("note", ""), str) or len(c.get("note", "")) > 1200:
        raise ContractError("BAD_NOTE")
    text = c["input_block_verbatim"]
    if not isinstance(text, str) or not text:
        raise ContractError("MISSING_VERBATIM")
    _fields(c["source"], {"document_ref", "section_id", "sha256", "original_document_sha256", "source_anchor_ref"}, {"document_ref", "section_id", "sha256"}, "source")
    _id(c["source"]["section_id"], "section_id")
    if not isinstance(c["source"]["document_ref"], str) or not c["source"]["document_ref"].startswith("source:"):
        raise ContractError("SOURCE_REF_INVALID")
    if not SHA.fullmatch(c["source"]["sha256"]):
        raise ContractError("SOURCE_SHA_INVALID")
    if c["source"].get("original_document_sha256") is not None:
        if not isinstance(c["source"]["original_document_sha256"], str) or not SHA.fullmatch(c["source"]["original_document_sha256"]):
            raise ContractError("DOCUMENT_SHA_INVALID")
        if not isinstance(c["source"].get("source_anchor_ref"), str) or not REF.fullmatch(c["source"]["source_anchor_ref"]):
            raise ContractError("DOCUMENT_ANCHOR_REQUIRED")
    raw_verbatim = text.encode("utf-8") if source_bytes is None else source_bytes
    if source_bytes is not None and raw_verbatim != text.encode("utf-8"):
        raise ContractError("VERBATIM_BYTES_CHANGED")
    if sha256(raw_verbatim) != c["source"]["sha256"]:
        raise ContractError("SOURCE_SHA_MISMATCH")
    for key in ("attachments", "depends_on"):
        values = c.get(key, [])
        if not isinstance(values, list) or len(values) != len(set(map(str, values))) or len(values) > 100:
            raise ContractError("BAD_LIST", key)
        for value in values:
            if key == "attachments":
                if not isinstance(value, str) or not REF.fullmatch(value):
                    raise ContractError("BAD_ANCHOR", str(value))
            else:
                _id(value, "depends_on")
    _fields(c.get("when", {"predicate": "always", "args": {}}), {"predicate", "args"}, {"predicate", "args"}, "when")
    cond = c.get("when", {"predicate": "always", "args": {}})
    if cond["predicate"] not in PREDICATES or not isinstance(cond["args"], dict):
        raise ContractError("BAD_PREDICATE")
    _fields(c["execution"], {"operation", "tool_profile", "max_model_calls", "write_paths", "timeout_s"}, {"operation", "tool_profile", "max_model_calls", "write_paths"}, "execution")
    ex = c["execution"]
    if ex["operation"] not in {"analyze", "inspect_source", "apply_approved_patch", "run_approved_test", "verify_artifacts"}:
        raise ContractError("OPERATION_UNKNOWN")
    if ex["tool_profile"] not in ("read_only", "writer_n4", "verify_only"):
        raise ContractError("BAD_PROFILE")
    if type(ex["max_model_calls"]) is not int or ex["max_model_calls"] not in (0, 1):
        raise ContractError("MAX_CALLS_ONE")
    if type(ex.get("timeout_s", 120)) is not int or not 1 <= ex.get("timeout_s", 120) <= 900:
        raise ContractError("BAD_TIMEOUT")
    if not isinstance(ex["write_paths"], list) or len(ex["write_paths"]) > 30:
        raise ContractError("BAD_WRITE_PATHS")
    for path in ex["write_paths"]:
        _safe_path(path)
    if ex["tool_profile"] != "writer_n4" and ex["write_paths"]:
        raise ContractError("READ_ONLY_WRITE_PATHS")
    _fields(c["outputs"], {"required_fields", "acceptance", "require_tool_receipt", "require_readback"}, {"required_fields", "acceptance", "require_tool_receipt", "require_readback"}, "outputs")
    out = c["outputs"]
    if not isinstance(out["required_fields"], list) or any(not isinstance(k, str) or not k for k in out["required_fields"]):
        raise ContractError("BAD_OUTPUT_FIELDS")
    if not isinstance(out["acceptance"], list) or any(not isinstance(k, str) or not k for k in out["acceptance"]):
        raise ContractError("BAD_ACCEPTANCE")
    if type(out["require_tool_receipt"]) is not bool or type(out["require_readback"]) is not bool:
        raise ContractError("BAD_OUTPUT_GATES")
    steps = c["steps"]
    if not isinstance(steps, list) or not 1 <= len(steps) <= 32:
        raise ContractError("STEPS_1_32")
    seen: dict[str, dict] = {}
    model_steps = 0
    for s in steps:
        _fields(s, {"id", "kind", "depends_on", "tool", "args"}, {"id", "kind", "depends_on"}, "step")
        sid = _id(s["id"], "step.id")
        if sid in seen:
            raise ContractError("DUPLICATE_STEP", sid)
        if s["kind"] not in STEP_KINDS:
            raise ContractError("UNKNOWN_STEP", sid)
        if s["kind"] == "MODEL":
            model_steps += 1
        if s["kind"] == "TOOL":
            if s.get("tool") not in OPS or not isinstance(s.get("args", {}), dict):
                raise ContractError("UNKNOWN_TOOL", sid)
            if s["tool"] in WRITE_OPS and ex["tool_profile"] != "writer_n4":
                raise ContractError("READ_ONLY_TOOL", sid)
            if "path" in s.get("args", {}):
                _safe_path(s["args"]["path"])
        elif "tool" in s or "args" in s:
            raise ContractError("EXTRA_STEP_FIELDS", sid)
        if not isinstance(s["depends_on"], list) or len(s["depends_on"]) != len(set(map(str, s["depends_on"]))):
            raise ContractError("BAD_STEP_DEPENDENCIES", sid)
        seen[sid] = s
    if model_steps != ex["max_model_calls"]:
        raise ContractError("MODEL_STEP_COUNT")
    for sid, s in seen.items():
        if any(d not in seen for d in s["depends_on"]):
            raise ContractError("UNKNOWN_STEP_DEPENDENCY", sid)
    visiting, visited = set(), set()
    def visit(sid: str):
        if sid in visiting:
            raise ContractError("DAG_CYCLE", sid)
        if sid in visited:
            return
        visiting.add(sid)
        for dep in seen[sid]["depends_on"]:
            visit(dep)
        visiting.remove(sid); visited.add(sid)
    for sid in seen:
        visit(sid)
    if c.get("on_pass", "NEXT") != "NEXT" or c.get("on_not_applicable", "RECORD_AND_NEXT") != "RECORD_AND_NEXT" or c.get("on_blocked", "FLAG_AND_STOP_DEPENDENTS") != "FLAG_AND_STOP_DEPENDENTS":
        raise ContractError("BAD_TRANSITIONS")
    return c

def ordered_steps(c: Mapping[str, Any]) -> list[dict]:
    """Stable topological order: original JSON order breaks ties."""
    pending = {s["id"]: s for s in c["steps"]}
    done, order = set(), []
    while pending:
        ready = next((sid for sid, st in pending.items() if set(st["depends_on"]) <= done), None)
        if ready is None:
            raise ContractError("DAG_CYCLE")
        order.append(pending.pop(ready)); done.add(ready)
    return order

def check_condition(cond: dict, facts: dict) -> tuple[str, str]:
    """Return EXECUTE | NOT_APPLICABLE | BLOCKED, relying only on HOST evidence."""
    p, a = cond["predicate"], cond["args"]
    if p == "always":
        return "EXECUTE", ""
    if p in ("requires_frontend", "requires_backend"):
        key = "frontend_required" if p == "requires_frontend" else "backend_required"
        value = facts.get(key)
    elif p == "source_exists":
        value = facts.get("source_exists", {}).get(a.get("source_ref"))
    elif p == "file_type_is":
        value = facts.get("file_types", {}).get(a.get("source_ref"))
        if value is not None:
            value = value == a.get("mime")
    elif p == "component_present":
        value = facts.get("components", {}).get(a.get("component_id"))
    elif p == "prior_status":
        value = facts.get("prior_status", {}).get(a.get("trigger_id"))
        if value is not None:
            value = value == a.get("status", "PASS")
    else:
        value = facts.get("approved_scope")
    if value is None:
        return "BLOCKED", "CONDITION_EVIDENCE_MISSING"
    return ("EXECUTE", "") if value is True else ("NOT_APPLICABLE", "HOST_EVIDENCE_FALSE")

def validate_loop(contracts: list[dict]) -> None:
    if not isinstance(contracts, list) or not 1 <= len(contracts) <= 100:
        raise ContractError("SLOTS_LIMIT_100")
    ids = set()
    for c in contracts:
        validate_contract(c)
        if c["id"] in ids:
            raise ContractError("DUPLICATE_TRIGGER", c["id"])
        ids.add(c["id"])
    for c in contracts:
        if any(d not in ids for d in c.get("depends_on", [])):
            raise ContractError("UNKNOWN_TRIGGER_DEPENDENCY", c["id"])
    visiting, visited = set(), set()
    by = {c["id"]: c for c in contracts}
    def visit(tid):
        if tid in visiting:
            raise ContractError("TRIGGER_CYCLE", tid)
        if tid in visited:
            return
        visiting.add(tid)
        for d in by[tid].get("depends_on", []):
            visit(d)
        visiting.remove(tid); visited.add(tid)
    for k in by:
        visit(k)
