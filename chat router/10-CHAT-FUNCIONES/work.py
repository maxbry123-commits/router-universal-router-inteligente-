"""Estado de trabajos para la barra WORK."""
from __future__ import annotations
from copy import deepcopy
from typing import Any

VALID = {"RUNNING", "PAUSED", "CANCELLED", "DONE"}
_JOBS: dict[str, dict[str, Any]] = {}

def crear(work_id: str, tareas: list[dict] | None = None) -> dict:
    if not work_id:
        raise ValueError("work_id requerido")
    _JOBS[work_id] = {"id": work_id, "status": "RUNNING", "progress": 0,
                      "tasks": deepcopy(tareas or [])}
    return obtener(work_id)

def obtener(work_id: str) -> dict:
    if work_id not in _JOBS:
        raise KeyError(work_id)
    return deepcopy(_JOBS[work_id])

def listar() -> list[dict]:
    return [deepcopy(v) for v in _JOBS.values()]

def _set(work_id: str, status: str) -> dict:
    if status not in VALID:
        raise ValueError(status)
    _JOBS[work_id]["status"] = status
    return obtener(work_id)

def pausar(work_id: str) -> dict:
    return _set(work_id, "PAUSED")

def cancelar(work_id: str) -> dict:
    return _set(work_id, "CANCELLED")

def reintentar(work_id: str) -> dict:
    return _set(work_id, "RUNNING")

def aprobar(work_id: str) -> dict:
    _JOBS[work_id]["progress"] = 100
    return _set(work_id, "DONE")

def progreso(work_id: str, porcentaje: int) -> dict:
    if porcentaje < 0 or porcentaje > 100:
        raise ValueError("progreso fuera de rango")
    _JOBS[work_id]["progress"] = porcentaje
    if porcentaje == 100:
        _JOBS[work_id]["status"] = "DONE"
    return obtener(work_id)
