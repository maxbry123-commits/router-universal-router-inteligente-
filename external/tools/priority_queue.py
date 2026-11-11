"""
priority_queue.py — Cola de prioridad para herramientas (salta inferencia pesada)
Ubicacion: external/tools/priority_queue.py
"""
import asyncio
import logging
from typing import Any, Callable
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass(order=True)
class PriorityTask:
    priority: int
    task_id: str = field(compare=False)
    fn: Callable = field(compare=False)


class ToolPriorityQueue:
    def __init__(self):
        self.queue = asyncio.PriorityQueue()
        self.active_tasks = set()

    async def submit(self, task_id: str, fn: Callable, priority: int = 1):
        """priority: 0 (alta, ej: health), 1 (normal), 2 (baja, ej: batch)"""
        await self.queue.put(PriorityTask(priority, task_id, fn))
        logger.info(f"Task {task_id} encolada con prioridad {priority}")

    async def worker_loop(self, router):
        while True:
            task = await self.queue.get()
            if task.task_id in self.active_tasks:
                continue
            self.active_tasks.add(task.task_id)

            async def wrapped_fn():
                try:
                    return await task.fn()
                finally:
                    self.active_tasks.discard(task.task_id)

            await router.dispatch(task.task_id, wrapped_fn)
            self.queue.task_done()
