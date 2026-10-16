from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

from huggingface_hub import fetch_job_metrics, inspect_job, run_job

CPU_FLAVOR = "cpu-upgrade"
HF_NAMESPACE = os.getenv("HF_NAMESPACE", "COMAND-CENTER-1")
RAM_THRESHOLD = 95.0
WORKER_ORDER = ("HF1", "HF2", "HF3")


@dataclass(frozen=True)
class SlotStatus:
    worker_id: str
    job_id: str | None = None
    stage: str = "IDLE"
    ram_percent: float = 0.0

    @property
    def available(self) -> bool:
        return self.stage not in {"RUNNING", "SCHEDULING"} and self.ram_percent < RAM_THRESHOLD


def _latest_ram_percent(job_id: str) -> float:
    latest: dict[str, Any] | None = None
    for metric in fetch_job_metrics(job_id=job_id):
        latest = metric
    if not latest:
        return 0.0
    used = float(latest.get("memory_used_bytes") or 0)
    total = float(latest.get("memory_total_bytes") or 0)
    return (used / total * 100.0) if total else 0.0


def refresh_slot(worker_id: str, job_id: str | None) -> SlotStatus:
    if not job_id:
        return SlotStatus(worker_id=worker_id)
    info = inspect_job(job_id=job_id)
    stage = str(info.status.stage)
    ram = _latest_ram_percent(job_id) if stage in {"RUNNING", "COMPLETED"} else 0.0
    return SlotStatus(worker_id=worker_id, job_id=job_id, stage=stage, ram_percent=ram)


def choose_slot(slots: list[SlotStatus]) -> str | None:
    by_id = {s.worker_id: s for s in slots}
    for worker_id in WORKER_ORDER:
        slot = by_id.get(worker_id, SlotStatus(worker_id))
        if slot.available:
            return worker_id
    return None


def launch_cpu_job(worker_id: str, command: list[str], *, name: str | None = None, timeout: str = "30m") -> dict[str, Any]:
    if worker_id not in WORKER_ORDER:
        raise ValueError(f"Unknown worker: {worker_id}")
    job = run_job(
        image="python:3.12-slim",
        command=command,
        flavor=CPU_FLAVOR,
        namespace=HF_NAMESPACE,
        timeout=timeout,
        name=name or f"{worker_id.lower()}-task",
    )
    return {
        "worker": worker_id,
        "job_id": job.id,
        "url": job.url,
        "flavor": CPU_FLAVOR,
        "namespace": HF_NAMESPACE,
    }


def dispatch(slots: list[SlotStatus], command: list[str], *, name: str | None = None, timeout: str = "30m") -> dict[str, Any]:
    worker = choose_slot(slots)
    if worker is None:
        return {"state": "WAITING", "worker": None}
    result = launch_cpu_job(worker, command, name=name, timeout=timeout)
    return {"state": "DISPATCH", **result}
