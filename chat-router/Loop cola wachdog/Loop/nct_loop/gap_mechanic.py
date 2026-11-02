"""MECÁNICO SYSTEM — lógica pura, sin red, sin modelo, sin escritura.

Agregar gaps de varios LOOPs, preparar propuestas basadas en evidencia y validar
selecciones. El host usa el almacenamiento, el buscador y el writer existentes.
No otorgar permisos de escritura ni auto-atribuir PASS a este módulo.
"""
from __future__ import annotations
import hashlib
import json
import re
from typing import Any
from urllib.parse import urlsplit

_ID = re.compile(r"^[A-Za-z0-9_-]{1,80}$")
ISSUE_STATES = frozenset({"BLOCKED", "FAILED", "GAP", "NEEDS_RECONCILIATION", "FLAGGED", "ERROR", "TIMEOUT"})
TERMINAL = frozenset({"PASS", "NOT_APPLICABLE", "OFF"})
SOURCE_DOMAINS = {
    "github": "github.com", "huggingface": "huggingface.co",
    "stackoverflow": "stackoverflow.com", "python_docs": "docs.python.org",
    "mdn": "developer.mozilla.org", "fastapi": "fastapi.tiangolo.com",
    "pytest": "docs.pytest.org", "pypi": "pypi.org",
    "owasp": "owasp.org", "sqlite_docs": "sqlite.org",
}
PENDING_STATES = frozenset({"QUEUED", "PENDING", "STARTED", "RUNNING", "PAUSED", "DRAFT"})
TRUSTED_SOURCE_IDS = frozenset({
    "github", "huggingface", "stackoverflow", "python_docs", "mdn", "fastapi",
    "pytest", "pypi", "owasp", "sqlite_docs",
})

class GapError(ValueError):
    pass

def canonical(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")

def sha(value: Any) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()

def _identifier(value: Any, field: str) -> str:
    if not isinstance(value, str) or not _ID.fullmatch(value):
        raise GapError("BAD_" + field.upper())
    return value

def from_loop_state(payload: dict, *, at_closure: bool = False) -> list[dict]:
    """Lee salida REAL dsl_estado/get: triggers es un OBJETO indexado por ID.

    No convierte ausencia de recibos en PASS; OFF y NOT_APPLICABLE se anotan
    pero no se convierten en gaps, salvo bandera explícita.
    """
    if not isinstance(payload, dict) or payload.get("ok") is not True:
        raise GapError("UNVERIFIED_LOOP_STATE")
    project = _identifier(payload.get("project_id"), "project_id")
    loop = _identifier(payload.get("loop_id"), "loop_id")
    triggers = payload.get("triggers")
    if not isinstance(triggers, dict):
        raise GapError("TRIGGERS_MUST_BE_OBJECT")
    gaps = []
    for tid, info in sorted(triggers.items()):
        _identifier(tid, "trigger_id")
        if not isinstance(info, dict):
            raise GapError("INVALID_TRIGGER_INFO")
        status = str(info.get("status") or "UNKNOWN").upper()
        flags = info.get("flags") or []
        if not isinstance(flags, list):
            raise GapError("INVALID_FLAGS")
        # Un estado UNKNOWN no se declara fallo, pero sí pendiente de conciliación.
        if status not in ISSUE_STATES and status != "UNKNOWN" and not flags and not (at_closure and status in PENDING_STATES):
            continue
        if status == "UNKNOWN" and not flags:
            category = "UNVERIFIED"
        elif at_closure and status in PENDING_STATES and not flags:
            category = "PENDING"
        else:
            category = "GAP"
        error = str(info.get("error") or info.get("reason") or "")[:500]
        rec = {"project_id": project, "loop_id": loop, "trigger_id": tid,
               "status": status, "category": category, "error": error,
               "flags": flags[:30], "source_ref": str(info.get("source_ref") or "")[:350],
               "contract_sha256": str(info.get("contract_sha256") or "")[:64],
               "origin_revision": payload.get("revision")}
        rec["gap_id"] = "gap_" + sha({k: rec[k] for k in
                       ("project_id", "loop_id", "trigger_id", "status", "error", "flags", "contract_sha256")})[:24]
        rec["workflow"] = "RECOLECTAR → INVESTIGAR → PROPONER → REVISAR → TRIGGER → VERIFICAR"
        gaps.append(rec)
    return gaps

def merge_gaps(existing: list[dict], incoming: list[dict]) -> list[dict]:
    """Fusiona gaps de varios LOOPs sin borrar historia ni duplicar id."""
    if not isinstance(existing, list) or not isinstance(incoming, list):
        raise GapError("BAD_GAPS")
    ordered = []
    known = set()
    for gap in existing + incoming:
        if not isinstance(gap, dict) or not isinstance(gap.get("gap_id"), str):
            raise GapError("INVALID_GAP")
        if gap["gap_id"] not in known:
            ordered.append(dict(gap))
            known.add(gap["gap_id"])
    if len(ordered) > 2000:
        raise GapError("GAPS_LIMIT")
    return ordered

def normalize_research_hits(gap_id: str, raw_hits: list[dict]) -> list[dict]:
    """Filtra resultados del buscador confiable del Harness; jamás hace fetch.

    Cada resultado debe tener referencia externa, título y fragmento comprobable.
    La relevancia la determina un modelo especializado; esta función no la simula.
    """
    if not isinstance(gap_id, str) or not gap_id.startswith("gap_"):
        raise GapError("BAD_GAP_ID")
    if not isinstance(raw_hits, list) or len(raw_hits) > 100:
        raise GapError("BAD_SEARCH_RESULTS")
    kept = []
    for hit in raw_hits:
        if not isinstance(hit, dict) or hit.get("source_id") not in TRUSTED_SOURCE_IDS:
            continue
        title, url, excerpt = (hit.get(k) for k in ("title", "url", "excerpt"))
        retrieved_ref = hit.get("retrieved_ref")
        if not all(isinstance(x, str) and x.strip() for x in (title, url, excerpt, retrieved_ref)):
            continue
        if not url.startswith("https://") or len(url) > 800:
            continue
        try:
            hostname = (urlsplit(url).hostname or "").lower()
        except ValueError:
            continue
        domain = SOURCE_DOMAINS[hit["source_id"]]
        if hostname != domain and not hostname.endswith("." + domain):
            continue
        item = {"gap_id": gap_id, "source_id": hit["source_id"], "title": title[:240],
                "url": url, "excerpt": excerpt[:1600], "retrieved_ref": retrieved_ref[:240]}
        item["evidence_sha256"] = sha(item)
        kept.append(item)
    return kept

def propose(gap: dict, proposals: list[dict], research_hits: list[dict]) -> dict:
    """Empaqueta SOLUCIONES sin ejecutarlas. Modelo sugiere; operador selecciona."""
    if not isinstance(gap, dict) or not str(gap.get("gap_id", "")).startswith("gap_"):
        raise GapError("BAD_GAP")
    if not isinstance(proposals, list) or not 1 <= len(proposals) <= 10:
        raise GapError("PROPOSALS_1_10")
    refs = {h["evidence_sha256"] for h in research_hits}
    rows = []
    seen = set()
    for proposal in proposals:
        if not isinstance(proposal, dict):
            raise GapError("BAD_PROPOSAL")
        pid = _identifier(proposal.get("solution_id"), "solution_id")
        rationale = proposal.get("rationale")
        refs_used = proposal.get("evidence_shas")
        if pid in seen or not isinstance(rationale, str) or not rationale.strip():
            raise GapError("DUPLICATE_OR_EMPTY_PROPOSAL")
        if not isinstance(refs_used, list) or not refs_used or any(v not in refs for v in refs_used):
            raise GapError("UNVERIFIED_PROPOSAL_EVIDENCE")
        seen.add(pid)
        rows.append({"solution_id": pid, "rationale": rationale[:3000],
                     "evidence_shas": refs_used, "target_root": str(proposal.get("target_root") or "")[:300],
                     "risk": str(proposal.get("risk") or "UNASSESSED")[:100], "status": "AWAITING_SELECTION"})
    return {"kind": "MECHANIC_PROPOSALS", "gap_id": gap["gap_id"], "solutions": rows,
            "research_hits": research_hits, "approved": False, "executed": False,
            "revision_sha256": sha({"gap_id": gap["gap_id"], "solutions": rows})}

def prepare_selected_trigger(bundle: dict, solution_id: str, *, server_approval_ref: str,
                             target_loop: str) -> dict:
    """Devuelve INTENCIÓN DE TRIGGER. NO crea contrato ejecutable ni dispara tools.

    La validación de aprobación real corresponde al host autenticado N4. No se
    acepta una bandera booleana originada en el navegador.
    """
    _identifier(target_loop, "target_loop")
    if not isinstance(bundle, dict) or bundle.get("kind") != "MECHANIC_PROPOSALS":
        raise GapError("BAD_BUNDLE")
    if not isinstance(server_approval_ref, str) or not server_approval_ref.startswith("approval:"):
        raise GapError("SERVER_APPROVAL_REQUIRED")
    row = next((s for s in bundle.get("solutions", []) if s["solution_id"] == solution_id), None)
    if row is None:
        raise GapError("SOLUTION_NOT_FOUND")
    # El host debe verificar que este recibo pertenece al gap/solución y revisión actuales.
    return {"kind": "TRIGGER_DRAFT_NOT_EXECUTABLE", "loop_id": target_loop,
            "source_gap_id": bundle["gap_id"], "solution_id": solution_id,
            "approval_ref": server_approval_ref, "solution": dict(row),
            "status": "NEEDS_CONTRACT_COMPILATION", "enabled": False,
            "requires": ["server_verify_approval", "source_anchor", "original_sha256",
                         "constitution_guard", "trigger_contract_validation", "expected_revision",
                         "writer_n4_scope", "readback", "operator_review"]}
