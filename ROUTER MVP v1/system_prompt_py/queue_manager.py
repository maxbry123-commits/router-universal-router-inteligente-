import asyncio
import time
import json
from collections import deque

class QueueManager:
    def __init__(self, max_concurrent=3):
        self.max_concurrent = max_concurrent
        self.active_requests = 0
        self.queue = asyncio.Queue()
        self.lock = asyncio.Lock()

    async def acquire(self):
        async with self.lock:
            if self.active_requests < self.max_concurrent:
                self.active_requests += 1
                return True
        future = asyncio.Future()
        await self.queue.put(future)
        return await future

    async def release(self):
        async with self.lock:
            if not self.queue.empty():
                future = await self.queue.get()
                future.set_result(True)
            else:
                self.active_requests -= 1

    def status(self):
        return {"active": self.active_requests, "waiting": self.queue.qsize()}
