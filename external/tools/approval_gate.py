"""
approval_gate.py — Aprobacion Humana (HITL) para herramientas sensibles
Ubicacion: external/tools/approval_gate.py
Patron: OpenRouter requireApproval / LangChain human_in_the_loop.
Regla: acciones sensibles pausan en awaiting_approval hasta decision humana.
"""
from __future__ import annotations
import asyncio
import logging
import time
import uuid
from typing import Dict, Set, Optional, Any, Literal
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

SENSITIVE_ACTIONS: Set[str] = {
    "send_email", "delete_record", "write_file", "execute_shell",
    "payment", "grant_access", "drop_table", "force_push",
}


@dataclass
class ApprovalRequest:
    request_id: str
    action: str
    payload: Dict[str, Any]
    status: Literal["PENDING", "APPROVED", "REJECTED", "TIMEOUT"] = "PENDING"
    created_at: float = field(default_factory=time.time)
    decided_at: Optional[float] = None
    decided_by: Optional[str] = None
    reason: Optional[str] = None


class ApprovalGate:
    """Puerta HITL: exige aprobacion explicita para acciones sensibles."""

    TIMEOUT_S = 300.0

    def __init__(self) -> None:
        self._requests: Dict[str, ApprovalRequest] = {}
        self._events: Dict[str, asyncio.Event] = {}
        self._lock = asyncio.Lock()

    def is_sensitive(self, action: str) -> bool:
        return action in SENSITIVE_ACTIONS

    async def request_approval(self, action: str, payload: Dict[str, Any]) -> str:
        req_id = str(uuid.uuid4())
        async with self._lock:
            self._requests[req_id] = ApprovalRequest(
                request_id=req_id, action=action, payload=payload
            )
            self._events[req_id] = asyncio.Event()
        logger.info("HITL pendiente %s accion=%s", req_id, action)
        return req_id

    async def wait_for_decision(self, req_id: str, timeout_s: float = None) -> ApprovalRequest:
        timeout_s = timeout_s or self.TIMEOUT_S
        event = self._events.get(req_id)
        if event is None:
            raise KeyError(f"Request {req_id} no existe")
        try:
            await asyncio.wait_for(event.wait(), timeout=timeout_s)
        except asyncio.TimeoutError:
            async with self._lock:
                req = self._requests[req_id]
                req.status = "TIMEOUT"
                req.decided_at = time.time()
                req.reason = "timeout_sin_decision_humana"
            logger.warning("HITL %s timeout", req_id)
        return self._requests[req_id]

    async def decide(self, req_id: str, approved: bool, decided_by: str, reason: str = "") -> None:
        async with self._lock:
            req = self._requests.get(req_id)
            if req is None:
                raise KeyError(f"Request {req_id} no existe")
            req.status = "APPROVED" if approved else "REJECTED"
            req.decided_at = time.time()
            req.decided_by = decided_by
            req.reason = reason
            event = self._events.get(req_id)
            if event:
                event.set()
        logger.info("HITL %s -> %s por %s", req_id, req.status, decided_by)

    async def gate(self, action: str, payload: Dict[str, Any],
                   executor) -> Any:
        """Envoltorio: si sensible, espera aprobacion; si no, ejecuta directo."""
        if not self.is_sensitive(action):
            return await executor(payload)
        req_id = await self.request_approval(action, payload)
        req = await self.wait_for_decision(req_id)
        if req.status != "APPROVED":
            raise PermissionError(
                f"Accion {action} no aprobada (status={req.status}, reason={req.reason})"
            )
        return await executor(payload)

    def pending(self) -> list:
        return [
            {"request_id": r.request_id, "action": r.action, "status": r.status}
            for r in self._requests.values() if r.status == "PENDING"
        ]
