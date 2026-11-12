"""space_queue.py — Cola 85% RAM -> salto Space (HF Control)"""
import asyncio
import logging
import uuid
from typing import Dict, List, Optional
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

@dataclass(order=True)
class SpaceTask:
    priority: int
    task_id: str = field(compare=False)
    space_id: str = field(compare=False)
    payload: Dict = field(default_factory=dict, compare=False)

class SpaceQueue:
    MAX_RAM_PCT = 85.0

    def __init__(self):
        self._queue: List[SpaceTask] = []
        self._running: Dict[str, SpaceTask] = {}
        self._skips_by_ram = 0
        self._lock = asyncio.Lock()

    async def _current_ram_pct(self) -> float:
        try:
            import psutil
            return float(psutil.virtual_memory().percent)
        except Exception:
            return 0.0

    async def enqueue(self, space_id: str, payload: Dict,
                      priority: int = 1, task_id: str = None) -> str:
        tid = task_id or str(uuid.uuid4())
        task = SpaceTask(priority=priority, task_id=tid,
                         space_id=space_id, payload=payload)
        async with self._lock:
            self._queue.append(task)
            self._queue.sort(key=lambda t: t.priority)
        return tid

    async def next_task(self) -> Optional[SpaceTask]:
        async with self._lock:
            ram = await self._current_ram_pct()
            if ram >= self.MAX_RAM_PCT:
                self._skips_by_ram += 1
                logger.warning("RAM %.1f%% >= %.1f%%: salto", ram, self.MAX_RAM_PCT)
                return None
            for task in self._queue:
                if task.space_id not in self._running:
                    self._running[task.space_id] = task
                    self._queue = [t for t in self._queue if t.task_id != task.task_id]
                    return task
            return None

    async def complete(self, task_id: str):
        async with self._lock:
            for sid, task in list(self._running.items()):
                if task.task_id == task_id:
                    del self._running[sid]
                    break

    async def snapshot(self) -> Dict:
        async with self._lock:
            return {
                "queued": len(self._queue),
                "running": len(self._running),
                "ram_pct": await self._current_ram_pct(),
                "skips_by_ram": self._skips_by_ram,
                "high": sum(1 for t in self._queue if t.priority == 0),
                "normal": sum(1 for t in self._queue if t.priority == 1),
                "low": sum(1 for t in self._queue if t.priority == 2),
            }

SPACE_QUEUE = SpaceQueue()
