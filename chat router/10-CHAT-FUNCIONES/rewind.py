"""Checkpoints en memoria por conversación/agente."""
from __future__ import annotations
from copy import deepcopy
from typing import Any

_CHECKPOINTS: dict[str, list[Any]] = {}

def guardar(conv_id: str, estado: Any) -> int:
    if not conv_id:
        raise ValueError("conv_id requerido")
    _CHECKPOINTS.setdefault(conv_id, []).append(deepcopy(estado))
    return len(_CHECKPOINTS[conv_id])

def volver(conv_id: str, pasos: int = 1) -> Any:
    if pasos < 1:
        raise ValueError("pasos debe ser >= 1")
    items = _CHECKPOINTS.get(conv_id, [])
    if len(items) <= pasos:
        raise IndexError("checkpoint insuficiente")
    for _ in range(pasos):
        items.pop()
    return deepcopy(items[-1])

def historial(conv_id: str) -> list[Any]:
    return deepcopy(_CHECKPOINTS.get(conv_id, []))
