import asyncio
import time
import random

class AsyncCircuitBreaker:
    def __init__(self, name: str, fail_thresh: int = 5, cooldown: float = 60.0):
        self.name = name
        self.fail_thresh = fail_thresh
        self.cooldown = cooldown
        self.failures = 0
        self.last_fail_ts = 0.0
        self.state = 'closed'
        self._lock = asyncio.Lock()

    async def call(self, fn, *args, **kwargs):
        async with self._lock:
            if self.state == 'open':
                if time.time() - self.last_fail_ts > self.cooldown:
                    self.state = 'half_open'
                else:
                    raise Exception(f'Circuit {self.name} OPEN')
        try:
            result = await fn(*args, **kwargs)
            async with self._lock:
                if self.state == 'half_open':
                    self.state = 'closed'
                    self.failures = 0
            return result
        except Exception:
            async with self._lock:
                self.failures += 1
                self.last_fail_ts = time.time()
                if self.failures >= self.fail_thresh:
                    self.state = 'open'
            raise

def async_backoff(attempt: int, base: float = 1.0, cap: float = 30.0) -> float:
    return min(cap, base * (2 ** attempt)) + random.uniform(0, 0.5)
