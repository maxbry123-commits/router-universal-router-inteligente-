"""lifeguard RETIRADO a solo-lectura (2026-10-16).

Antes envolvia agents-yaiwes/common/guardian.py para vigilar/re-lanzar Jobs HF
(Router <-> guardian). Ahora: solo status de salud local del Space permanente.
SIN capacidad de crear, cancelar ni inspeccionar computo HF.
"""
from __future__ import annotations

from typing import Any

ACTIONS = ("status",)
_RETIRADO = "guardian/lifeguard retirado: el runtime permanente es el Space CPU 32 GB"


def handle(action: str, payload: "dict | None" = None) -> dict:
    if action != "status":
        return {"ok": False, "error": _RETIRADO, "allowed": list(ACTIONS)}
    cpu = ram = -1.0
    try:
        import psutil
        cpu = float(psutil.cpu_percent(interval=0.1))
        ram = float(psutil.virtual_memory().percent)
    except Exception:  # noqa: BLE001
        pass
    return {"ok": True, "modo": "health-only", "cpu_percent": cpu, "ram_percent": ram,
            "nota": "sin creacion de computo; saturacion = cola"}


def start_peer_watch() -> bool:
    return False
