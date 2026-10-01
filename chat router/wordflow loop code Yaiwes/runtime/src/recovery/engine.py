"""
Recovery Engine Module - PECP-MAXBRY-100x (Nodo T-011)
Protocolo RT-80 para auto-recuperación y escalación determinista.

N-2.6: recovery tipado. La acción ya no es solo RETRY/ESCALATE genérica:
cada fallo se clasifica en FailureKind (RETRYABLE, DEPENDENCY, AUTH, STUCK,
CRASH, IRREVERSIBLE_FAILURE, NO_NODE_SOLUTION) y la política concreta de
FAILURE_POLICY decide retry/backoff/human/rollback/next_state.
N-2.7: stuck detector. Misma acción + mismos args + mismo estado de
evidencia repetido max_repeats veces sin evidencia nueva -> BLOCKED_STUCK.
"""

from typing import Dict, Any
import json
from src.recovery.classifier import FailureClassifier
from src.recovery.checkpoint import CheckpointManager
from src.recovery.reconciliation import ReconciliationEngine
from src.core.task_runtime import FAILURE_POLICY, FailureKind, StuckDetector

_CATEGORY_TO_KIND = {
    "TIMEOUT": FailureKind.RETRYABLE,
    "RATE_LIMIT": FailureKind.RETRYABLE,
    "AUTH_ERROR": FailureKind.AUTH,
    "SCHEMA_VIOLATION": FailureKind.DEPENDENCY,
    "RESOURCE_EXHAUSTION": FailureKind.CRASH,
    "GENERIC_RUNTIME": FailureKind.IRREVERSIBLE,
}


class RecoveryEngine:
    """Orquesta la recuperación ante errores ejecutando la compuerta RT-80."""

    def __init__(self, max_repeats: int = 3) -> None:
        self.classifier = FailureClassifier()
        self.checkpoint_mgr = CheckpointManager()
        self.reconciliation = ReconciliationEngine()
        self.stuck = StuckDetector(max_repeats=max_repeats)

    def classify_kind(self, error_msg: str) -> str:
        """Categoría del clasificador -> FailureKind tipado."""
        category = self.classifier.classify(error_msg)["category"]
        return _CATEGORY_TO_KIND.get(category, FailureKind.IRREVERSIBLE)

    def handle_failure(self, node_id: str, error_msg: str, attempt: int,
                       current_state: Dict[str, Any],
                       action_type: str = "node", action_args: Dict[str, Any] | None = None,
                       new_evidence: bool = False) -> Dict[str, Any]:
        """
        RT-80 tipado: clasifica a FailureKind -> stuck check -> política concreta.
        """
        classification = self.classifier.classify(error_msg)
        ckp_res = self.checkpoint_mgr.create_checkpoint(f"{node_id}_fail_{attempt}", current_state)
        kind = self.classify_kind(error_msg)

        stuck = self.stuck.record(action_type, action_args or {}, current_state, new_evidence)
        if stuck:
            kind = FailureKind.STUCK

        policy = FAILURE_POLICY[kind]
        base = {
            "protocol": "RT-80",
            "kind": kind,
            "attempt": attempt,
            "node_id": node_id,
            "checkpoint": ckp_res["hash"],
            "classification": classification,
            "policy": policy,
        }

        if kind == FailureKind.STUCK:
            return {**base, "action": "BLOCKED_STUCK", "next_state": policy["next_state"]}

        if policy["retry_allowed"] and attempt < policy["max_retries"]:
            return {**base, "action": "RETRY", "attempt": attempt + 1,
                    "backoff": policy["backoff"], "next_state": policy["next_state"]}

        if policy["requires_human"]:
            return {**base, "action": "ESCALATE_TO_DIRECTOR",
                    "next_state": policy["next_state"],
                    "reason": f"{kind} requires human authority"}

        return {**base, "action": "NON_RETRYABLE", "next_state": policy["next_state"],
                "rollback": policy["rollback"]}


if __name__ == "__main__":
    print("=== TEST NODO T-011: RECOVERY ENGINE ===")
    engine = RecoveryEngine()
    res1 = engine.handle_failure("T-011", "HTTP 429 Too Many Requests", attempt=1, current_state={"step": 1})
    res2 = engine.handle_failure("T-011", "JSONSchema ValidationError", attempt=1, current_state={"step": 2})
    res3 = engine.handle_failure("T-011", "unauthorized token", attempt=1, current_state={"step": 3})
    for _ in range(3):
        res4 = engine.handle_failure("T-011", "timeout", attempt=1, current_state={"step": 4})
    print(json.dumps({"test_retry": res1, "test_escalate": res2, "test_auth": res3, "test_stuck": res4}, indent=2))
