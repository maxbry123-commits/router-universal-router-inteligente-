# api_limiter.py
import time
import threading
from collections import deque

class TokenBucket:
    def __init__(self, rpm: int, tpm: int):
        self.rpm = rpm
        self.tpm = tpm
        self.request_timestamps = deque()
        self.token_timestamps = deque()
        self.lock = threading.Lock()

    def _clean_expired(self, now: float) -> None:
        while self.request_timestamps and now - self.request_timestamps[0] > 60:
            self.request_timestamps.popleft()
        while self.token_timestamps and now - self.token_timestamps[0][0] > 60:
            self.token_timestamps.popleft()

    def acquire(self, estimated_tokens: int = 1000, timeout: float = 60.0) -> bool:
        start_time = time.time()
        while time.time() - start_time < timeout:
            with self.lock:
                now = time.time()
                self._clean_expired(now)
                current_rpm = len(self.request_timestamps)
                current_tpm = sum(t for _, t in self.token_timestamps)

                if current_rpm < self.rpm and (current_tpm + estimated_tokens) <= self.tpm:
                    self.request_timestamps.append(now)
                    self.token_timestamps.append((now, estimated_tokens))
                    return True
            time.sleep(1.0)
        return False

LIMITERS = {
    "groq": TokenBucket(rpm=30, tpm=8000),      # Límites oficiales
    "nvidia": TokenBucket(rpm=40, tpm=100000),  # Límites oficiales
}

def wait_for_slot(provider: str, estimated_tokens: int = 1000, timeout: float = 60.0) -> bool:
    limiter = LIMITERS.get(provider)
    if not limiter: return True
    return limiter.acquire(estimated_tokens, timeout)
