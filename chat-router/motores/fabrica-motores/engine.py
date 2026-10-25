"""Contrato común de motores de la Fábrica UI (documento 18)."""
from __future__ import annotations

from typing import Any


class Engine:
    """Contrato base: id, capabilities, can_handle, execute, verify."""

    id: str = "engine.base"
    capabilities: list[str] = []

    async def can_handle(self, task: dict) -> bool:
        """True si la tarea pide una capacidad que este motor ofrece."""
        return task.get("capability") in self.capabilities

    async def execute(self, task: dict, context: dict | None = None) -> dict:
        raise NotImplementedError

    async def verify(self, result: dict) -> bool:
        """Verificación determinista mínima del resultado."""
        return isinstance(result, dict) and result.get("status") == "PASS"


def ok(payload: Any = None, **extra: Any) -> dict:
    result = {"status": "PASS"}
    if payload is not None:
        result["result"] = payload
    result.update(extra)
    return result


def fail(reason: str, **extra: Any) -> dict:
    result = {"status": "FAIL", "reason": reason}
    result.update(extra)
    return result
