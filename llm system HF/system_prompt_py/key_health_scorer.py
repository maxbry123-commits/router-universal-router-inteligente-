# key_health_scorer.py
import time
import threading
from dataclasses import dataclass
from typing import Dict, List, Optional

@dataclass
class KeyHealth:
    key: str
    status: str = "unknown"  # healthy, degraded, invalid, cooldown
    consecutive_failures: int = 0
    last_check_ts: float = 0.0
    last_error: Optional[str] = None
    score: float = 1.0

class KeyHealthScorer:
    def __init__(self, health_check_fn, interval_s: float = 300.0):
        self.health_check_fn = health_check_fn
        self.interval_s = interval_s
        self.health: Dict[str, KeyHealth] = {}
        self.lock = threading.Lock()
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def register_keys(self, keys: List[str]):
        with self.lock:
            for key in keys:
                self.health[key] = KeyHealth(key=key)

    def _loop(self):
        while not self._stop.wait(self.interval_s):
            self.run_health_check()

    def run_health_check(self):
        with self.lock:
            keys = list(self.health.keys())
        for key in keys:
            try:
                ok = self.health_check_fn(key)
                with self.lock:
                    h = self.health[key]
                    h.last_check_ts = time.time()
                    if ok:
                        h.status = "healthy"
                        h.consecutive_failures = 0
                        h.score = min(1.0, h.score + 0.1)
                    else:
                        h.consecutive_failures += 1
                        h.score = max(0.0, h.score - 0.2)
                        h.status = "degraded" if h.consecutive_failures < 3 else "invalid"
            except Exception as e:
                with self.lock:
                    h = self.health[key]
                    h.status = "invalid"
                    h.last_error = str(e)
                    h.score = 0.0

    def mark_failure(self, key: str, error: str):
        with self.lock:
            h = self.health.get(key)
            if h:
                h.consecutive_failures += 1
                h.last_error = error
                h.score = max(0.0, h.score - 0.3)
                if "401" in error or "403" in error:
                    h.status = "invalid"

    def get_healthy_keys(self) -> List[str]:
        with self.lock:
            return [k for k, h in self.health.items() if h.status in ("healthy", "degraded")]

    def score(self, key: str) -> float:
        with self.lock:
            return self.health.get(key, KeyHealth(key=key)).score

    def stop(self):
        self._stop.set()
