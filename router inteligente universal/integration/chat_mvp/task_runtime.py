"""T-11-C/D runtime: claim/lease/heartbeat, STUCK, failure policy, crash/resume, WorkerBootstrap.

Contracts from chat router/01-PLAN/T-11 (NUEVO-08..NUEVO-12). Patterns adapted from the
downloaded OSS components under "Componente open soure/" (Temporal-Python-SDK heartbeat/lease
semantics, Durable-Task-Python work-item locking) and the repo's own
chat router/05-AGENTES/asistentes/heartbeat.py stall detection.
Stdlib only, deterministic, fail-closed.
"""
from __future__ import annotations

import hashlib
import json
import time
from dataclasses import asdict, dataclass, field

_LEASE_MAX_SECONDS = 3600
_CLAIM_FIELDS = ("claim_id", "node_id", "worker_id", "base_sha", "write_scope",
                 "lease_expires_at", "heartbeat_at", "status")


class ContractError(ValueError):
    pass


class LeaseError(RuntimeError):
    pass


def _now() -> float:
    return time.time()


def _canonical(obj: object) -> str:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _scopes_overlap(a: list[str], b: list[str]) -> bool:
    for x in a:
        for y in b:
            if x == y or x.startswith(y + "/") or y.startswith(x + "/"):
                return True
    return False


def validate_claim(data: dict) -> dict:
    if not isinstance(data, dict):
        raise ContractError("claim no es objeto")
    missing = [k for k in _CLAIM_FIELDS if k not in data]
    if missing:
        raise ContractError(f"claim falta campos: {missing}")
    if not isinstance(data["write_scope"], list) or not data["write_scope"]:
        raise ContractError("write_scope vacío")
    if data["status"] not in {"CLAIMED", "RELEASED", "EXPIRED"}:
        raise ContractError("status inválido")
    return data


class ClaimManager:
    """Registro de claims con lease. Doble writer sobre scope solapado: rechazado."""

    def __init__(self, lease_seconds: int = 300):
        self.lease_seconds = lease_seconds
        self.claims: dict[str, dict] = {}

    def acquire(self, claim: dict, now: float | None = None) -> dict:
        validate_claim(claim)
        now = _now() if now is None else now
        for other in self.claims.values():
            if other["status"] == "CLAIMED" and not self.expired(other, now)                     and _scopes_overlap(other["write_scope"], claim["write_scope"]):
                raise LeaseError(f"SCOPE_OVERLAP:{other['claim_id']}")
        if float(claim["lease_expires_at"] or 0) <= now:
            claim["lease_expires_at"] = now + self.lease_seconds
        claim["heartbeat_at"] = now
        claim["status"] = "CLAIMED"
        self.claims[claim["claim_id"]] = dict(claim)
        return claim

    def expired(self, claim: dict, now: float | None = None) -> bool:
        now = _now() if now is None else now
        return float(claim.get("lease_expires_at") or 0) <= now

    def heartbeat(self, claim_id: str, now: float | None = None) -> dict:
        now = _now() if now is None else now
        claim = self.claims.get(claim_id)
        if claim is None or claim["status"] != "CLAIMED":
            raise LeaseError(f"CLAIM_NOT_ACTIVE:{claim_id}")
        if self.expired(claim, now):
            claim["status"] = "EXPIRED"
            raise LeaseError(f"LEASE_EXPIRED:{claim_id}")
        # heartbeat renueva dentro de límites: nunca más allá de lease_seconds desde ahora
        new_expiry = min(now + self.lease_seconds, float(claim["heartbeat_at"]) + _LEASE_MAX_SECONDS)
        claim["lease_expires_at"] = new_expiry
        claim["heartbeat_at"] = now
        return claim

    def release(self, claim_id: str) -> dict:
        claim = self.claims.get(claim_id)
        if claim is None:
            raise LeaseError(f"CLAIM_UNKNOWN:{claim_id}")
        claim["status"] = "RELEASED"
        return claim

    def side_effect_allowed(self, claim_id: str, scope: str, now: float | None = None) -> None:
        """Lease expirada no permite side effect; scope fuera de write_scope tampoco."""
        now = _now() if now is None else now
        claim = self.claims.get(claim_id)
        if claim is None or claim["status"] != "CLAIMED":
            raise LeaseError(f"SIDE_EFFECT_DENIED_NO_CLAIM:{claim_id}")
        if self.expired(claim, now):
            claim["status"] = "EXPIRED"
            raise LeaseError(f"SIDE_EFFECT_DENIED_LEASE_EXPIRED:{claim_id}")
        if not any(scope == s or scope.startswith(s + "/") for s in claim["write_scope"]):
            raise LeaseError(f"SIDE_EFFECT_DENIED_SCOPE:{scope}")


class StuckDetector:
    """fingerprint = sha256(action_type + canonical_args + evidence_state_hash).
    Repetido N veces sin nueva evidencia → STUCK → strategy_change | BLOCKED_WITH_TRACE."""

    def __init__(self, max_repeats: int = 3):
        self.max_repeats = max_repeats
        self.counts: dict[str, int] = {}

    def fingerprint(self, action_type: str, args: dict, evidence_state: object) -> str:
        return _sha(action_type + "|" + _canonical(args) + "|" + _sha(_canonical(evidence_state)))

    def record(self, action_type: str, args: dict, evidence_state: object,
               new_evidence: bool) -> str | None:
        fp = self.fingerprint(action_type, args, evidence_state)
        self.counts[fp] = 0 if new_evidence else self.counts.get(fp, 0) + 1
        if self.counts[fp] >= self.max_repeats:
            return "STUCK"
        return None


class FailureKind:
    RETRYABLE = "RETRYABLE"
    DEPENDENCY = "DEPENDENCY"
    AUTH = "AUTH"
    STUCK = "STUCK"
    CRASH = "CRASH"
    IRREVERSIBLE = "IRREVERSIBLE_FAILURE"
    NO_SOLUTION = "NO_NODE_SOLUTION"


FAILURE_POLICY: dict[str, dict] = {
    FailureKind.RETRYABLE: {"retry_allowed": True, "max_retries": 3, "backoff": "exponential",
                            "requires_human": False, "rollback": False, "next_state": "RETRY"},
    FailureKind.DEPENDENCY: {"retry_allowed": True, "max_retries": 2, "backoff": "fixed",
                             "requires_human": False, "rollback": False, "next_state": "WAIT_DEPENDENCY"},
    FailureKind.AUTH: {"retry_allowed": False, "max_retries": 0, "backoff": "none",
                       "requires_human": True, "rollback": False, "next_state": "BLOCKED_AUTH"},
    FailureKind.STUCK: {"retry_allowed": False, "max_retries": 0, "backoff": "none",
                        "requires_human": False, "rollback": False, "next_state": "STRATEGY_CHANGE"},
    FailureKind.CRASH: {"retry_allowed": True, "max_retries": 1, "backoff": "none",
                        "requires_human": False, "rollback": True, "next_state": "RESUME_CHECKPOINT"},
    FailureKind.IRREVERSIBLE: {"retry_allowed": False, "max_retries": 0, "backoff": "none",
                               "requires_human": True, "rollback": True, "next_state": "BLOCKED_WITH_TRACE"},
    FailureKind.NO_SOLUTION: {"retry_allowed": False, "max_retries": 0, "backoff": "none",
                              "requires_human": True, "rollback": True, "next_state": "BLOCKED_WITH_TRACE"},
}


def classify(exc: BaseException) -> str:
    """Clasificación tipada; nunca catch genérico → GAP. Retorna FailureKind."""
    if isinstance(exc, LeaseError):
        return FailureKind.DEPENDENCY
    if isinstance(exc, TimeoutError):
        return FailureKind.RETRYABLE
    if isinstance(exc, PermissionError):
        return FailureKind.AUTH
    if isinstance(exc, (ContractError, ValueError)):
        return FailureKind.IRREVERSIBLE
    if isinstance(exc, (OSError, RuntimeError)):
        return FailureKind.CRASH
    return FailureKind.IRREVERSIBLE


_CHECKPOINT_FIELDS = ("run_id", "node_id", "input_hash", "state_hash",
                      "base_sha", "evidence_cursor", "completed_side_effects")


@dataclass
class Checkpoint:
    run_id: str
    node_id: str
    input_hash: str
    state_hash: str
    base_sha: str
    evidence_cursor: int = 0
    completed_side_effects: list[str] = field(default_factory=list)

    def hash(self) -> str:
        return _sha(_canonical(asdict(self)))


def verify_checkpoint(data: dict, expected_state_hash: str, base_sha: str) -> Checkpoint:
    """LOAD → VALIDATE SCHEMA → VERIFY HASH → VERIFY BASE_SHA → RECONCILE → RESUME."""
    if not isinstance(data, dict):
        raise ContractError("checkpoint no es objeto")
    missing = [k for k in _CHECKPOINT_FIELDS if k not in data]
    if missing:
        raise ContractError(f"checkpoint falta campos: {missing}")
    cp = Checkpoint(
        run_id=str(data["run_id"]), node_id=str(data["node_id"]),
        input_hash=str(data["input_hash"]), state_hash=str(data["state_hash"]),
        base_sha=str(data["base_sha"]), evidence_cursor=int(data["evidence_cursor"]),
        completed_side_effects=list(data["completed_side_effects"]),
    )
    if cp.state_hash != expected_state_hash:
        raise ContractError("CHECKPOINT_STATE_HASH_MISMATCH")
    if cp.base_sha != base_sha:
        raise ContractError("CHECKPOINT_BASE_SHA_MISMATCH")
    return cp


def reconcile_side_effect(cp: Checkpoint, effect_id: str) -> bool:
    """True si el efecto ya se ejecutó (idempotente: no repetir); si no, lo marca."""
    if effect_id in cp.completed_side_effects:
        return True
    cp.completed_side_effects.append(effect_id)
    return False


_BOOTSTRAP_STEPS = ("load_contract", "validate_schema", "verify_worker",
                    "verify_node", "verify_capability", "verify_scope",
                    "verify_base_sha", "verify_environment", "acquire_claim", "READY")


class BootstrapError(RuntimeError):
    def __init__(self, step: str, detail: str):
        super().__init__(f"BOOTSTRAP_FAIL:{step}:{detail}")
        self.step = step


def worker_bootstrap(contract: dict, worker_id: str, node_id: str,
                     capabilities: list[str], base_sha: str, env_ok: bool,
                     claims: ClaimManager, now: float | None = None) -> dict:
    """10 pasos antes de READY; cualquier fallo → no ejecutar."""
    if not isinstance(contract, dict):
        raise BootstrapError("load_contract", "no es objeto")
    required = {"task_id", "node_id", "worker_id", "capability", "write_scope", "base_sha"}
    missing = required - set(contract)
    if missing:
        raise BootstrapError("validate_schema", f"falta {sorted(missing)}")
    if contract["worker_id"] != worker_id:
        raise BootstrapError("verify_worker", "worker_id distinto")
    if contract["node_id"] != node_id:
        raise BootstrapError("verify_node", "nodo distinto")
    if contract["capability"] not in capabilities:
        raise BootstrapError("verify_capability", str(contract["capability"]))
    if not isinstance(contract["write_scope"], list) or not contract["write_scope"]:
        raise BootstrapError("verify_scope", "write_scope vacío")
    if contract["base_sha"] != base_sha:
        raise BootstrapError("verify_base_sha", "base_sha distinto")
    if not env_ok:
        raise BootstrapError("verify_environment", "entorno/herramientas no disponibles")
    claim = {
        "claim_id": f"claim-{contract['task_id']}-{worker_id}", "node_id": node_id,
        "worker_id": worker_id, "base_sha": base_sha, "write_scope": contract["write_scope"],
        "lease_expires_at": "", "heartbeat_at": "", "status": "CLAIMED",
    }
    claims.acquire(claim, now)
    return {"status": "READY", "claim": claim, "steps": list(_BOOTSTRAP_STEPS)}


# ---------------------------------------------------------------------------
# NUEVO-13 — Workspace aislado por writer
# ---------------------------------------------------------------------------

_WORKSPACE_FIELDS = ("parent_id", "child_id", "node_id", "claim_id", "workspace",
                     "base_sha", "write_scope", "command_id")


def validate_workspace(data: dict) -> dict:
    if not isinstance(data, dict):
        raise ContractError("workspace no es objeto")
    missing = [k for k in _WORKSPACE_FIELDS if k not in data]
    if missing:
        raise ContractError(f"workspace falta campos: {missing}")
    return data


class WorkspaceRegistry:
    """Cada writer tiene workspace aislado; no se comparte directorio mutable."""

    def __init__(self):
        self.workspaces: dict[str, dict] = {}

    def register(self, ws: dict, claims: ClaimManager, now: float | None = None) -> dict:
        validate_workspace(ws)
        claims.side_effect_allowed(ws["claim_id"], ws["workspace"], now)
        for other in self.workspaces.values():
            if other["workspace"] == ws["workspace"] and other["child_id"] != ws["child_id"]:
                raise LeaseError(f"WORKSPACE_SHARED:{ws['workspace']}")
        self.workspaces[ws["child_id"]] = dict(ws)
        return ws

    def promote(self, child_id: str, test_passed: bool, target_sha: str) -> dict:
        ws = self.workspaces.get(child_id)
        if ws is None:
            raise LeaseError(f"WORKSPACE_UNKNOWN:{child_id}")
        if not test_passed:
            ws["status"] = "DISCARDED"
            raise LeaseError(f"PROMOTE_DENIED_TESTS_FAILED:{child_id}")
        if ws["base_sha"] != target_sha:
            ws["status"] = "NEEDS_REBASE"
            raise LeaseError(f"BASE_SHA_CONFLICT:{child_id}")
        ws["status"] = "PROMOTED"
        return ws


# ---------------------------------------------------------------------------
# NUEVO-16 — Salida LLM tipada, fail-closed
# ---------------------------------------------------------------------------

_LLM_OUTPUT_FIELDS = ("decision", "confidence", "evidence_refs", "recommended_action", "unknowns")


def validate_llm_output(data: object) -> dict:
    if not isinstance(data, dict):
        raise ContractError("llm_output no es objeto")
    missing = [k for k in _LLM_OUTPUT_FIELDS if k not in data]
    if missing:
        raise ContractError(f"llm_output falta campos: {missing}")
    extra = set(data) - set(_LLM_OUTPUT_FIELDS)
    if extra:
        raise ContractError(f"llm_output campos extra: {sorted(extra)}")
    if not isinstance(data["evidence_refs"], list) or not isinstance(data["unknowns"], list):
        raise ContractError("llm_output tipos inválidos")
    return data


# ---------------------------------------------------------------------------
# NUEVO-17 — ResearchResult + NO_NEW_EVIDENCE
# ---------------------------------------------------------------------------

_RESEARCH_FIELDS = ("query", "sources", "source_type", "claims", "cross_check",
                    "new_evidence", "conclusion")


def validate_research_result(data: object) -> dict:
    if not isinstance(data, dict):
        raise ContractError("research_result no es objeto")
    missing = [k for k in _RESEARCH_FIELDS if k not in data]
    if missing:
        raise ContractError(f"research_result falta campos: {missing}")
    if data["new_evidence"] is not True and data["new_evidence"] is not False:
        raise ContractError("new_evidence debe ser boolean")
    return data


# ---------------------------------------------------------------------------
# NUEVO-18 — Persistencia por tarea (TASK/STATE/HANDOFF/EVIDENCE/EVENTS)
# ---------------------------------------------------------------------------

_TASK_FILES = ("TASK.json", "STATE.json", "HANDOFF.md", "EVIDENCE.json", "EVENTS.jsonl")


def ensure_task_folder(base: str, task_id: str) -> dict:
    """Crea la carpeta de task idempotentemente; snapshot local no duplica autoridad."""
    import os
    path = os.path.join(base, task_id)
    os.makedirs(path, exist_ok=True)
    created = []
    for name in _TASK_FILES:
        fp = os.path.join(path, name)
        if not os.path.exists(fp):
            with open(fp, "w", encoding="utf-8") as fh:
                fh.write("{}" if name.endswith(".json") else "")
            created.append(name)
    return {"task_id": task_id, "path": path, "files": list(_TASK_FILES), "created": created}


# ---------------------------------------------------------------------------
# NUEVO-19 — DISPATCH → EVIDENCE → FINALIZE (cierre separado)
# ---------------------------------------------------------------------------

_RUN_STATES = ("READY", "DISPATCHED", "RUNNING", "NEED_EVIDENCE", "VERIFIED", "FINALIZED")
_RUN_TRANSITIONS = {
    "READY": {"DISPATCHED"},
    "DISPATCHED": {"RUNNING"},
    "RUNNING": {"NEED_EVIDENCE", "VERIFIED"},
    "NEED_EVIDENCE": {"VERIFIED"},
    "VERIFIED": {"FINALIZED"},
    "FINALIZED": set(),
}


class RunLedger:
    """Estados de cierre; FINALIZE exige evidence ledger. Nadie se auto-declara PASS."""

    def __init__(self):
        self.runs: dict[str, dict] = {}

    def dispatch(self, run_id: str) -> dict:
        self.runs[run_id] = {"state": "DISPATCHED", "evidence": []}
        return self.runs[run_id]

    def transition(self, run_id: str, to_state: str) -> dict:
        run = self.runs.get(run_id)
        if run is None:
            raise ContractError(f"RUN_UNKNOWN:{run_id}")
        if to_state not in _RUN_STATES:
            raise ContractError(f"RUN_STATE_INVALID:{to_state}")
        if to_state not in _RUN_TRANSITIONS.get(run["state"], set()):
            raise ContractError(f"RUN_TRANSITION_INVALID:{run['state']}->{to_state}")
        if to_state == "VERIFIED" and not run["evidence"]:
            raise ContractError("RUN_NEEDS_EVIDENCE")
        run["state"] = to_state
        return run

    def attach_evidence(self, run_id: str, receipt: dict) -> dict:
        run = self.runs.get(run_id)
        if run is None:
            raise ContractError(f"RUN_UNKNOWN:{run_id}")
        run["evidence"].append(receipt)
        if run["state"] == "RUNNING":
            run["state"] = "NEED_EVIDENCE"
        return run

    def finalize(self, run_id: str, judge_receipt: dict) -> dict:
        run = self.runs.get(run_id)
        if run is None:
            raise ContractError(f"RUN_UNKNOWN:{run_id}")
        if run["state"] != "VERIFIED":
            raise ContractError("FINALIZE_REQUIRES_VERIFIED")
        if not isinstance(judge_receipt, dict) or not judge_receipt.get("judge"):
            raise ContractError("FINALIZE_REQUIRES_JUDGE")
        run["state"] = "FINALIZED"
        run["judge_receipt"] = judge_receipt
        return run
