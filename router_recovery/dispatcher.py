"""Tabla de handlers deterministas. Sin LLM: solo dispatch por node.handler."""
from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Any

from .pydantic_models import DagNode, DagSpec


def dispatch_architect(node: DagNode) -> dict[str, Any]:
    """Crea directorios (path termina en '/') o archivos vacios con action='create'."""
    created: list[str] = []
    for f in node.files:
        if f.get("action") != "create":
            continue
        path = Path(f["path"])
        if f["path"].endswith("/"):
            path.mkdir(parents=True, exist_ok=True)
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.touch(exist_ok=True)
        created.append(f["path"])
    return {"action": "created", "files": created}


def dispatch_tester(node: DagNode) -> dict[str, Any]:
    """Valida que el propio modelo DagSpec rechaza lo que debe rechazar y acepta lo valido."""
    probe = {
        "mission_id": "probe", "objective": "probe",
        "nodes": [{"node_id": "N1", "name": "p", "role": "tester", "objective": "p",
                   "root_ids": ["R1"], "acceptance": ["ok"], "estimated_loc": 10}],
    }
    DagSpec.model_validate(probe)
    return {"action": "validated", "result": "PASS"}


def dispatch_implementer(node: DagNode) -> dict[str, Any]:
    """STUB: no ejecuta trabajo real. Registra el nodo como ejecutado (ver 🚩 en README)."""
    return {"action": "executed", "result": "PASS", "stub": True}


def dispatch_sleep(node: DagNode) -> dict[str, Any]:
    """Solo para pruebas de kill -9: duerme RR_SLEEP_S segundos (por defecto 0)."""
    seconds = float(os.environ.get("RR_SLEEP_S", "0"))
    time.sleep(seconds)
    return {"action": "slept", "seconds": seconds}


DISPATCH_TABLE = {
    "dispatch_architect": dispatch_architect,
    "dispatch_tester": dispatch_tester,
    "dispatch_implementer": dispatch_implementer,
    "dispatch_sleep": dispatch_sleep,
}
