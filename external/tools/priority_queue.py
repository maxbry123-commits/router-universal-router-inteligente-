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
    while True:
        task = await self.queue.get()
        if task.task_id in self.active_tasks:
            self.queue.task_done()
            continue
        self.active_tasks.add(task.task_id)
        try:
            async def wrapped_fn():
                try:
                    return await task.fn()
                except Exception as e:
                    logger.error(f"[Queue] {task.task_id} error: {e}")
                    return None
                finally:
                    self.active_tasks.discard(task.task_id)
            await router.dispatch(task.task_id, wrapped_fn)
            while task.task_id in self.active_tasks:
                await asyncio.sleep(0.1)
        except Exception as e:
            logger.error(f"[Queue] dispatch {task.task_id} fallo: {e}")
            self.active_tasks.discard(task.task_id)
        finally:
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
