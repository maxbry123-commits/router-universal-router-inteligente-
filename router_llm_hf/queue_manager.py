"""
queue_manager.py — Cola con prioridad (Control Plane)
1 tarea por modelo en ejecucion; salto al 85% de RAM.
"""
from __future__ import annotations
import asyncio
import time
import uuid
import logging
from typing import Literal, Dict, Optional, List, Any
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class Priority(Enum):
    HIGH = 0
    NORMAL = 1
    LOW = 2


@dataclass
class Task:
    task_id: str
    model_id: str
    priority: Priority = Priority.NORMAL
    payload: Dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
    status: Literal["QUEUED", "RUNNING", "DONE", "FAILED"] = "QUEUED"
    attempts: int = 0
    last_error: Optional[str] = None


class QueueManager:
    MAX_RAM_PCT = 85.0

    def __init__(self, max_concurrent: int = 3) -> None:
        self.max_concurrent = max_concurrent
        self._queues: Dict[Priority, List[Task]] = {p: [] for p in Priority}
        self._running: Dict[str, Task] = {}
        self._index: Dict[str, Task] = {}
        self._lock = asyncio.Lock()

    async def _current_ram_pct(self) -> float:
        try:
            import psutil
            return float(psutil.virtual_memory().percent)
        except Exception:
            return 0.0

    async def enqueue(self, model_id: str, payload: Dict[str, Any],
                      priority: Priority = Priority.NORMAL) -> str:
        task_id = str(uuid.uuid4())
        task = Task(task_id=task_id, model_id=model_id,
                    priority=priority, payload=payload)
        async with self._lock:
            self._queues[priority].append(task)
            self._index[task_id] = task
        logger.info("Enqueued %s model=%s pri=%s", task_id, model_id, priority.name)
        return task_id

    async def next_task(self) -> Optional[Task]:
        async with self._lock:
            if await self._current_ram_pct() >= self.MAX_RAM_PCT:
                logger.warning("RAM al limite: no se despacha")
                return None
            for pri in (Priority.HIGH, Priority.NORMAL, Priority.LOW):
                while self._queues[pri]:
                    task = self._queues[pri][0]
                    if task.model_id in self._running:
                        return None
                    self._queues[pri].pop(0)
                    task.status = "RUNNING"
                    self._running[task.model_id] = task
                    return task
            return None

    async def complete(self, task_id: str, success: bool = True,
                       error: Optional[str] = None) -> None:
        async with self._lock:
            task = self._index.get(task_id)
            if not task:
                return
            running = self._running.get(task.model_id)
            if running is not None and running.task_id == task_id:
                del self._running[task.model_id]
            task.status = "DONE" if success else "FAILED"
            task.last_error = error
            task.attempts += 1

    async def snapshot(self) -> Dict[str, Any]:
        async with self._lock:
            return {
                "queued": sum(len(q) for q in self._queues.values()),
                "running": len(self._running),
                "ram_pct": await self._current_ram_pct(),
                "index_size": len(self._index),
            }
