"""Deterministic logical scheduler for the three RIU Hugging Face compute slots.

This module owns only slot selection. Job submission stays in hf_jobs_compute.py
so the Router has one Hugging Face Jobs submission implementation.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

WORKER_ORDER = ("HF1", "HF2", "HF3")
RAM_THRESHOLD = 95.0


@dataclass(frozen=True)
class HFSlot:
    worker_id: str
    ram_percent: float = 0.0
    busy: bool = False

    def __post_init__(self) -> None:
        if self.worker_id not in WORKER_ORDER:
            raise ValueError(f"UNKNOWN_HF_WORKER:{self.worker_id}")
        if not 0.0 <= float(self.ram_percent) <= 100.0:
            raise ValueError("HF_RAM_PERCENT_OUT_OF_RANGE")

    @property
    def available(self) -> bool:
        return (not self.busy) and float(self.ram_percent) < RAM_THRESHOLD


def choose_hf_slot(slots: Iterable[HFSlot]) -> str | None:
    """Return the first explicitly reported available slot, else None.

    Missing slot telemetry is never treated as available: fail closed.
    """
    by_id: dict[str, HFSlot] = {}
    for slot in slots:
        if slot.worker_id in by_id:
            raise ValueError(f"DUPLICATE_HF_WORKER:{slot.worker_id}")
        by_id[slot.worker_id] = slot

    for worker_id in WORKER_ORDER:
        slot = by_id.get(worker_id)
        if slot is not None and slot.available:
            return worker_id
    return None


def scheduler_decision(slots: Iterable[HFSlot]) -> dict[str, str | None]:
    worker_id = choose_hf_slot(slots)
    if worker_id is None:
        return {"state": "WAITING", "worker": None}
    return {"state": "DISPATCH", "worker": worker_id}


def dispatch_hf_request(
    slots: Iterable[HFSlot],
    request: object,
    submitter: object,
) -> dict[str, object]:
    """Select one logical slot and delegate submission to the canonical submitter.

    The submitter must expose submit(request). This module never implements
    Hugging Face Job submission itself.
    """
    worker_id = choose_hf_slot(slots)
    if worker_id is None:
        return {"state": "WAITING", "worker": None}
    submit = getattr(submitter, "submit", None)
    if not callable(submit):
        raise TypeError("HF_SUBMITTER_MUST_EXPOSE_SUBMIT")
    result = submit(request)
    if not isinstance(result, dict):
        raise TypeError("HF_SUBMITTER_INVALID_RESULT")
    return {"state": "DISPATCH", "worker": worker_id, **result}
