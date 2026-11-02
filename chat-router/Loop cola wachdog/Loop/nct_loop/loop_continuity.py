"""Handoff + CRAZY WALL + continuidad, sin nuevo almacenamiento ni dispatcher.
Solo genera artefactos inmutables; guardar/readback por callbacks existentes.
"""
from __future__ import annotations
import hashlib
import json

class ContinuityError(ValueError):
    pass

def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")

def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()

def build_handoff(loop_state: dict, gaps: list[dict], *, next_loop_id: str,
                  review_at_end: bool, checkpoint_refs: list[str] | None = None) -> dict:
    if not isinstance(loop_state, dict) or loop_state.get("ok") is not True:
        raise ContinuityError("UNVERIFIED_LOOP_STATE")
    if not isinstance(loop_state.get("triggers"), dict):
        raise ContinuityError("TRIGGER_STATUS_NOT_VERIFIED")
    if not isinstance(next_loop_id, str) or not next_loop_id or next_loop_id == loop_state.get("loop_id"):
        raise ContinuityError("BAD_NEXT_LOOP")
    if not isinstance(gaps, list):
        raise ContinuityError("BAD_GAPS")
    if not isinstance(review_at_end, bool):
        raise ContinuityError("BAD_REVIEW_FLAG")
    refs = checkpoint_refs or []
    if not isinstance(refs, list) or any(not isinstance(r, str) or not r for r in refs):
        raise ContinuityError("BAD_CHECKPOINT_REFS")
    states = {tid: str((item or {}).get("status") or "UNKNOWN").upper()
              for tid, item in loop_state["triggers"].items()}
    blocking = [tid for tid, s in states.items() if s not in {"PASS", "NOT_APPLICABLE", "OFF"}]
    unresolved = [g["gap_id"] for g in gaps if isinstance(g, dict) and isinstance(g.get("gap_id"), str)]
    # Los recibos deben estar corroborados por el host. Un estado PASS textual no
    # es prueba de que los entregables estén correctos.
    manual_review = review_at_end or bool(blocking) or bool(unresolved)
    status = "REVIEW_REQUIRED" if manual_review else "ELIGIBLE_FOR_NEXT_LOOP_CHECK"
    record = {"schema": "yaiwes.handoff.v1", "project_id": loop_state.get("project_id"),
              "from_loop_id": loop_state.get("loop_id"), "to_loop_id": next_loop_id,
              "from_revision": loop_state.get("revision"), "trigger_statuses": states,
              "blocking_triggers": blocking, "gap_ids": unresolved,
              "checkpoint_refs": refs, "review_at_end": review_at_end,
              "status": status, "auto_dispatched": False,
              "crazy_wall": {"summary": {"total": len(states),
                  "pass": sum(s=="PASS" for s in states.values()),
                  "not_applicable": sum(s=="NOT_APPLICABLE" for s in states.values()),
                  "other": sum(s not in {"PASS", "NOT_APPLICABLE"} for s in states.values())},
                  "gap_ids": unresolved, "last_loop_id": loop_state.get("loop_id")}}
    record["sha256"] = digest(record)
    return record

def verify_readback(expected: dict, actual: dict) -> bool:
    """True solo cuando la copia persistida conserva los mismos bytes lógicos."""
    if not isinstance(expected, dict) or not isinstance(actual, dict):
        raise ContinuityError("BAD_READBACK")
    h = expected.get("sha256")
    if not isinstance(h, str) or len(h) != 64:
        raise ContinuityError("MISSING_SHA")
    e = dict(expected); a = dict(actual)
    e.pop("sha256", None); a.pop("sha256", None)
    return digest(e) == h and digest(a) == h
