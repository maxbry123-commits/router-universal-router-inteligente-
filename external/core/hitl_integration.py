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
        if ApprovalGate is None:
            raise RuntimeError(
                "FATAL: approval_gate.py no disponible. "
                "HITL no puede operar."
            )
        self.gate = ApprovalGate()

    async def maybe_gate(self, action, payload, executor):
        return await self.gate.gate(action, payload, executor)

    def is_sensitive(self, action):
        return action in SENSITIVE_ACTIONS

    def pending(self):
        return self.gate.pending()


try:
    HITL = HITLIntegration()
except RuntimeError as e:
    import logging
    logging.getLogger(__name__).error(str(e))
    HITL = None
