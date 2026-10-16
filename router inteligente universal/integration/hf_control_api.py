"""Control plane HF RETIRADO.

Antes montaba /control/hf/workers/ensure, /workers/invoke y el autoscaler de
integration/hf_worker_pool.py sobre HF Jobs (cpu-basic/cpu-upgrade). Queda solo
un status local de CPU/RAM para telemetria: la saturacion se resuelve con la
cola existente, nunca lanzando computo.
"""
from __future__ import annotations

import os
from typing import Any

from fastapi import APIRouter, Depends

from .chat_mvp.router import _auth


def build_hf_control_router() -> APIRouter:
    r = APIRouter(prefix="/control/hf", tags=["hf-control"])

    @r.get("/status")
    def status(_owner: str = Depends(_auth)) -> dict[str, Any]:
        cpu = ram = -1.0
        try:
            import psutil
            cpu = float(psutil.cpu_percent(interval=0.1))
            ram = float(psutil.virtual_memory().percent)
        except Exception:  # noqa: BLE001
            pass
        return {
            "ok": True,
            "runtime": "hf-space-cpu-upgrade-32gb",
            "politica": "saturacion=cola (sin autoscaler ni workers)",
            "cpu_percent": cpu,
            "ram_percent": ram,
            "hf_jobs_capacidad": 0,
            "env_retirado": sorted(k for k in ("HF_CONTROL_JOBS_TOKEN", "HF_AUTOSCALE_MAX_WORKERS") if not os.getenv(k)),
        }

    return r
