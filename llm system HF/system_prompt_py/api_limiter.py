# api_limiter.py
import asyncio
import time
from collections import deque

class AsyncTokenBucket:
    def __init__(self, rpm: int, tpm: int):
        self.rpm = rpm
        self.tpm = tpm
        self.req_ts = deque()
        self.tok_ts = deque()
        self._lock = asyncio.Lock()

    async def _clean(self, now: float):
        while self.req_ts and now - self.req_ts[0] > 60:
            self.req_ts.popleft()
        while self.tok_ts and now - self.tok_ts[0][0] > 60:
            self.tok_ts.popleft()

    async def acquire(self, est_tokens: int = 1000, timeout: float = 60.0) -> bool:
        start = time.monotonic()
        while time.monotonic() - start < timeout:
            async with self._lock:
                now = time.monotonic()
                await self._clean(now)
                if len(self.req_ts) < self.rpm and sum(t for _, t in self.tok_ts) + est_tokens <= self.tpm:
                    self.req_ts.append(now)
                    self.tok_ts.append((now, est_tokens))
                    return True
            await asyncio.sleep(0.1)
        return False

LIMITERS = {
    "groq": AsyncTokenBucket(rpm=30, tpm=8000),
    "nvidia": AsyncTokenBucket(rpm=40, tpm=100000),
}

async def wait_for_slot(provider: str, est_tokens: int = 1000) -> bool:
    limiter = LIMITERS.get(provider)
    if not limiter:
        return True
    return await limiter.acquire(est_tokens)
