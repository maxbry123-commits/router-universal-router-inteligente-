"""Worker pool HF RETIRADO (2026-10-16).

Antes: vigia CPU/RAM y hacia run_job de cpu-basic/cpu-upgrade (workers Jobs),
cancelaba workers ociosos y atendia /control/hf/invoke. Queda un stub en memoria
que conserva la forma del API (status/launch/invoke/start/stop) para que los
imports viejos no rompan: NUNCA crea, inspecciona ni cancela computo.
La saturacion significa COLA en el Router permanente (Space 32 GB).
"""
from __future__ import annotations

import threading
import time
from dataclasses import dataclass, asdict
from typing import Any

MAX_WORKERS = 0  # retirado: 0 workers externos siempre
CHILD = True
_RETIRADO = "HF_JOBS_RETIRADOS: el runtime permanente es el Space CPU 32 GB; saturacion = cola"


@dataclass
class Worker:
    job_id: str
    url: str
    flavor: str
    created_at: float
    last_used_at: float
    state: str = "starting"

    def public(self) -> dict[str, Any]:
        now = time.time()
        out = asdict(self)
        out["age_s"] = round(now - self.created_at, 1)
        out["idle_s"] = round(now - self.last_used_at, 1)
        return out


class HFWorkerPool:
    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._workers: dict[str, Worker] = {}
        self._rr = 0
        self._stop = threading.Event()
        self.cpu_percent = 0.0
        self.ram_percent = 0.0
        self.last_error: str | None = None
        self.last_scale_reason: str | None = "retirado: Space permanente, sin autoscaler"

    @property
    def hf_token(self) -> str:
        return ""  # HF_CONTROL_JOBS_TOKEN eliminado del runtime

    @property
    def enabled(self) -> bool:
        return False

    def _metrics(self) -> tuple[float, float]:
        import psutil
        return float(psutil.cpu_percent(interval=0.2)), float(psutil.virtual_memory().percent)

    def launch(self, flavor: str, reason: str) -> Worker:
        raise RuntimeError(_RETIRADO)

    def inspect(self) -> None:
        return  # sin Jobs que inspeccionar

    def reap_idle(self) -> list[str]:
        return []  # sin Jobs que cancelar

    def choose(self) -> Worker | None:
        return None

    async def invoke(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {"status": "retirado", "error": _RETIRADO, "politica": "saturacion=cola"}

    def status(self) -> dict[str, Any]:
        try:
            self.cpu_percent, self.ram_percent = self._metrics()
        except Exception as exc:
            self.last_error = f"metrics:{type(exc).__name__}:{str(exc)[:120]}"
        return {
            "role": "permanent-controller",
            "enabled": False,
            "hf_jobs_retirados": True,
            "politica": "saturacion=cola (Space CPU 32 GB permanente)",
            "cpu_percent": self.cpu_percent,
            "ram_percent": self.ram_percent,
            "workers": [],
            "max_workers": 0,
            "jobs_token_present": False,
            "last_scale_reason": self.last_scale_reason,
            "last_error": self.last_error,
        }

    def start(self) -> None:
        return  # no hay loop: no se vigila CPU/RAM para lanzar computo

    def stop(self) -> None:
        self._stop.set()


POOL = HFWorkerPool()
