import time
import random
import threading
from enum import Enum

class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"

class CircuitOpenError(Exception):
    pass

class CircuitBreaker:
    def __init__(self, name: str, fail_thresh: int = 5, cooldown: float = 60.0, max_half_open_calls: int = 1, excluded_exceptions: tuple = ()):
        self.name = name
        self.fail_thresh = fail_thresh
        self.cooldown = cooldown
        self.max_half_open_calls = max_half_open_calls
        self.excluded_exceptions = excluded_exceptions
        self.failures = 0
        self.last_fail_ts = 0.0
        self.state = CircuitState.CLOSED
        self._half_open_calls = 0
        self.lock = threading.Lock()

    def call(self, fn, *args, **kwargs):
        with self.lock:
            if self.state == CircuitState.OPEN:
                if time.time() - self.last_fail_ts > self.cooldown:
                    self.state = CircuitState.HALF_OPEN
                    self._half_open_calls = 0
                else:
                    raise CircuitOpenError(f"Circuit '{self.name}' is OPEN")
            if self.state == CircuitState.HALF_OPEN:
                if self._half_open_calls >= self.max_half_open_calls:
                    raise CircuitOpenError(f"Circuit '{self.name}' HALF_OPEN limit reached")
                self._half_open_calls += 1
        try:
            result = fn(*args, **kwargs)
            with self.lock:
                if self.state == CircuitState.HALF_OPEN:
                    self.state = CircuitState.CLOSED
                    self.failures = 0
                    self._half_open_calls = 0
            return result
        except Exception as exc:
            if isinstance(exc, self.excluded_exceptions):
                raise
            with self.lock:
                self.failures += 1
                self.last_fail_ts = time.time()
                if self.failures >= self.fail_thresh:
                    self.state = CircuitState.OPEN
            raise

def exponential_backoff(attempt: int, base: float = 1.0, cap: float = 30.0) -> float:
    return min(cap, base * (2 ** attempt)) + random.uniform(0, 0.5)

BREAKERS = {"groq": CircuitBreaker("groq"), "nvidia": CircuitBreaker("nvidia")}
