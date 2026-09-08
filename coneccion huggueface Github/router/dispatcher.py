from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Iterable

RAM_THRESHOLD = 95.0
WORKER_ORDER = ("HF1", "HF2", "HF3")


@dataclass(frozen=True)
class WorkerStatus:
    worker_id: str
    ram_percent: float = 0.0
    busy: bool = False

    @property
    def available(self) -> bool:
        return (not self.busy) and self.ram_percent < RAM_THRESHOLD


def choose_worker(statuses: Iterable[WorkerStatus]) -> str | None:
    by_id = {status.worker_id: status for status in statuses}
    for worker_id in WORKER_ORDER:
        status = by_id.get(worker_id, WorkerStatus(worker_id=worker_id))
        if status.available:
            return worker_id
    return None


class TaskQueue:
    def __init__(self) -> None:
        self._items: deque[dict] = deque()

    def enqueue(self, task: dict) -> None:
        self._items.append(task)

    def dequeue(self) -> dict | None:
        return self._items.popleft() if self._items else None

    def __len__(self) -> int:
        return len(self._items)


def route(task: dict, statuses: Iterable[WorkerStatus], queue: TaskQueue) -> dict:
    worker_id = choose_worker(statuses)
    if worker_id is None:
        queue.enqueue(task)
        return {"state": "WAITING", "worker": None, "queue_size": len(queue)}
    return {"state": "DISPATCH", "worker": worker_id, "queue_size": len(queue)}
