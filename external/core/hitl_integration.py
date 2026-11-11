"""hitl_integration.py — Cablea approval_gate al proxy (FAIL-CLOSED)"""
import logging
from typing import Dict, Any, Callable, Awaitable

logger = logging.getLogger(__name__)

_GATE = None
_SENSITIVE = set()
try:
    from external.tools.approval_gate import ApprovalGate, SENSITIVE_ACTIONS
    _GATE = ApprovalGate
    _SENSITIVE = SENSITIVE_ACTIONS
except ImportError:
    try:
        from tools.approval_gate import ApprovalGate, SENSITIVE_ACTIONS
        _GATE = ApprovalGate
        _SENSITIVE = SENSITIVE_ACTIONS
    except ImportError:
        pass


class HITLIntegration:
    def __init__(self):
        if _GATE is None:
            logger.error("approval_gate NO disponible — sistema en modo FAIL-CLOSED")
        self.gate = _GATE() if _GATE else None

    async def maybe_gate(self, action: str, payload: Dict[str, Any],
                         executor: Callable[[Dict], Awaitable[Any]]) -> Any:
        if self.gate is None:
            raise RuntimeError(
                "HITL FAIL-CLOSED: approval_gate ausente. "
                "Acciones sensibles bloqueadas."
            )
        return await self.gate.gate(action, payload, executor)

    def is_sensitive(self, action: str) -> bool:
        return action in _SENSITIVE

    def pending(self) -> list:
        return self.gate.pending() if self.gate else []


HITL = HITLIntegration()
