"""Capa de salud del Canvas (N4-A).

Fichero: health.py
Responsabilidad: agregar el estado real de los 6 adapters en un payload
consumible por GET /health y por el WS /ws/progress.

FAIL_CLOSED: si el engine falla, este modulo devuelve estado degradado
explícito (nunca lanza).
"""

from __future__ import annotations

import time
from typing import Any, Dict, List

import canvas_engine as engine

STATUS_OK = "OK"
STATUS_OMITIDO = "OMITIDO"
STATUS_ERROR = "ERROR"


def health_snapshot() -> List[Dict[str, Any]]:
    """Estado por adapter. NUNCA lanza (el engine ya aísla cada adapter)."""
    try:
        snapshot = engine.health_all()
    except Exception as exc:  # pragma: no cover - defensivo
        return [
            {
                "tool": tool,
                "status": STATUS_ERROR,
                "reason": f"{type(exc).__name__}: {exc}",
                "version": None,
            }
            for tool in engine.ALL_TOOLS
        ]
    if not isinstance(snapshot, list):  # pragma: no cover - defensivo
        return [
            {
                "tool": tool,
                "status": STATUS_ERROR,
                "reason": f"health_all() devolvio {type(snapshot).__name__}",
                "version": None,
            }
            for tool in engine.ALL_TOOLS
        ]
    return snapshot


def health_payload() -> Dict[str, Any]:
    """Payload agregado de salud: {"ok","status","adapters","counts","timestamp"}."""
    snapshot = health_snapshot()
    counts: Dict[str, int] = {STATUS_OK: 0, STATUS_OMITIDO: 0, STATUS_ERROR: 0}
    for entry in snapshot:
        status = str(entry.get("status") or STATUS_ERROR)
        counts[status] = counts.get(status, 0) + 1
    if counts.get(STATUS_ERROR):
        overall = STATUS_ERROR
    elif counts.get(STATUS_OK):
        overall = STATUS_OK
    else:
        overall = STATUS_OMITIDO
    return {
        "ok": overall != STATUS_ERROR,
        "status": overall,
        "adapters": snapshot,
        "counts": counts,
        "total": len(snapshot),
        "timestamp": time.time(),
    }
