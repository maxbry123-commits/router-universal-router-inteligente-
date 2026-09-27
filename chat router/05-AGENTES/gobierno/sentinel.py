"""Sentinel — watchdog de runtime (doc 23, nivel 6).

Vigila ejecución, errores, bloqueos y desviaciones.
Reglas extra del Director:
- mismo error 3 veces -> REASSIGN
- heartbeat_at más viejo que max_minutos (30 por defecto) -> REASSIGN
"""
from __future__ import annotations

from datetime import datetime, timezone


class Sentinel:
    """Inspecciona el estado de una tarea y devuelve una acción."""

    def __init__(self, max_minutos: int = 30) -> None:
        self.max_minutos = max_minutos
        self._errores: dict[str, int] = {}

    def inspect(self, task_state: dict) -> dict:
        if task_state.get("unauthorized_change"):
            return {"action": "BLOCK"}

        status = task_state.get("status")

        if status == "ERROR":
            error = str(task_state.get("error", ""))
            self._errores[error] = self._errores.get(error, 0) + 1
            if self._errores[error] >= 3:
                return {"action": "REASSIGN"}
            return {"action": "RECOVER"}

        if status == "STALLED":
            return {"action": "REASSIGN"}

        heartbeat = task_state.get("heartbeat_at")
        if heartbeat:
            if isinstance(heartbeat, str):
                heartbeat = datetime.fromisoformat(heartbeat)
            if heartbeat.tzinfo is None:
                heartbeat = heartbeat.replace(tzinfo=timezone.utc)
            edad = (datetime.now(timezone.utc) - heartbeat).total_seconds()
            if edad > self.max_minutos * 60:
                return {"action": "REASSIGN"}

        return {"action": "CONTINUE"}
