"""seals_worker.py - Firma objetivo S-02: SealsWorker.execute(TaskContract) -> NodeResult.

Fusión del staff: el worker NO es orquestador - es un micro-worker que
recibe TaskContract tipado y devuelve NodeResult tipado. Debajo delega en
las piezas ya existentes de seals_core: ejecutor (rutas DAG),
idempotencia (replay/conflict tipado), dag_engine (ruta válida o GAP),
sheriff_policy (acciones estructuradas), stuck_detector, crash_resume.
"""
from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

import ejecutor  # noqa: E402


@dataclass(frozen=True)
class TaskContract:
    """Contrato tipado de entrada: qué tipo de tarea y con qué payload."""
    tipo: str
    nombre: str = ""
    url: str = ""
    mission_id: str = ""
    command_id: str = ""
    extra: dict[str, Any] = field(default_factory=dict)

    def to_tarea(self) -> dict:
        tarea = {"tipo": self.tipo, "nombre": self.nombre, **self.extra}
        if self.url:
            tarea["url"] = self.url
        if self.mission_id:
            tarea["mission_id"] = self.mission_id
        if self.command_id:
            tarea["command_id"] = self.command_id
        return tarea


@dataclass(frozen=True)
class NodeResult:
    """Resultado tipado: status cerrado + evidencia + mission_id."""
    status: str
    mission_id: str
    evidencia: dict[str, Any] = field(default_factory=dict)
    nodo_dag: str = ""
    idempotencia: str = ""


class SealsWorker:
    """Micro-worker determinista; ejecuta TaskContract bajo la ruta DAG."""

    def execute(self, contract: TaskContract) -> NodeResult:
        resultado = ejecutor.ejecutar_tarea(contract.to_tarea())
        return NodeResult(
            status=resultado.get("status", "GAP"),
            mission_id=resultado.get("mission_id", contract.mission_id),
            evidencia=resultado.get("evidencia", {}),
            nodo_dag=resultado.get("nodo_dag", ""),
            idempotencia=resultado.get("idempotencia", ""),
        )
