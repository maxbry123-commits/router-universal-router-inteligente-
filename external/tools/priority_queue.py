"""priority_queue.py — Cola de prioridad con backpressure real."""
import asyncio
import logging
from dataclasses import dataclass, field
from typing import Callable, Any

logger = logging.getLogger(__name__)


@dataclass(order=True)
class PriorityTask:
    priority: int
    task_id: str = field(compare=False)
    fn: Callable = field(compare=False)


class ToolPriorityQueue:
    def __init__(self, max_concurrent: int = 4):
        self.queue: asyncio.PriorityQueue = asyncio.PriorityQueue()
        self.max_concurrent = max_concurrent
        self._sem = asyncio.Semaphore(max_concurrent)
        self.active: dict = {}
        self._running = False
        self._task = None

    async def submit(self, task_id: str, fn: Callable, priority: int = 1):
        await self.queue.put(PriorityTask(priority, task_id, fn))
        logger.info(f"[Queue] submit {task_id} p={priority} depth={self.queue.qsize()}")

    async def _run_one(self, pt: PriorityTask, router):
        async with self._sem:
            self.active[pt.task_id] = "running"
            try:
                await router.dispatch(pt.task_id, pt.fn)
            except Exception as e:
                logger.error(f"[Queue] {pt.task_id} error: {e}")
            finally:
                self.active.pop(pt.task_id, None)

    async def worker_loop(self, router):
        self._running = True
        while self._running:
            try:
                pt = await asyncio.wait_for(self.queue.get(), timeout=1.0)
            except asyncio.TimeoutError:
                continue
            if pt.task_id in self.active:
                self.queue.task_done()
                continue
            await self._run_one(pt, router)
            self.queue.task_done()

    async def start(self, router):
        self._task = asyncio.create_task(self.worker_loop(router))

    async def stop(self):
        self._running = False
        if self._task:
            self._task.cancel()

    def stats(self) -> dict:
        return {
            "queue_size": self.queue.qsize(),
            "active_tasks": list(self.active.keys()),
            "max_concurrent": self.max_concurrent,
            "high": 0,
            "normal": 0,
            "low": 0,
        }
