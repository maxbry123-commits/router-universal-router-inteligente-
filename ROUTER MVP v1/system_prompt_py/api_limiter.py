import time
import threading
from collections import deque

class TokenBucket:
    def __init__(self, rpm: int, tpm: int):
        self.rpm = rpm
        self.tpm = tpm
        self.req_ts = deque()
        self.tok_ts = deque()
        self.lock = threading.Lock()

    def _clean(self, now: float):
        while self.req_ts and now - self.req_ts[0] > 60:
            self.req_ts.popleft()
        while self.tok_ts and now - self.tok_ts[0][0] > 60:
            self.tok_ts.popleft()

    def acquire(self, est_tokens: int = 1000, timeout: float = 60.0) -> bool:
        start = time.time()
        while time.time() - start < timeout:
            with self.lock:
                now = time.time()
                self._clean(now)
                if len(self.req_ts) < self.rpm and sum(t for _, t in self.tok_ts) + est_tokens <= self.tpm:
                    self.req_ts.append(now)
                    self.tok_ts.append((now, est_tokens))
                    return True
            time.sleep(1.0)
        return False

LIMITERS = {
    "groq": TokenBucket(30, 8000),
    "nvidia": TokenBucket(40, 1000000)
}

def wait_for_slot(provider: str, est_tokens: int = 1000) -> bool:
    limiter = LIMITERS.get(provider)
    if not limiter:
        return True
    return limiter.acquire(est_tokens)
