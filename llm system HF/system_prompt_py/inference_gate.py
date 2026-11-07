# inference_gate.py
import asyncio
from fastapi import HTTPException

class InferenceGate:
    def __init__(self, max_concurrency: int = 10, max_queue: int = 100, retry_after_s: int = 5):
        self.semaphore = asyncio.Semaphore(max_concurrency)
        self.max_queue = max_queue
        self.retry_after_s = retry_after_s
        self.in_flight = 0
        self._lock = asyncio.Lock()

    async def acquire(self):
        async with self._lock:
            if self.in_flight >= self.max_queue:
                raise HTTPException(
                    status_code=503,
                    detail="Servidor saturado. Reintenta más tarde.",
                    headers={"Retry-After": str(self.retry_after_s)}
                )
            self.in_flight += 1
        await self.semaphore.acquire()

    def release(self):
        self.semaphore.release()
        asyncio.create_task(self._decrement())

    async def _decrement(self):
        async with self._lock:
            self.in_flight = max(0, self.in_flight - 1)
