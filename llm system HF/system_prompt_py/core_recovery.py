# core_recovery.py
import os
import json
import time
import random
import hashlib
import tempfile
import threading
from enum import Enum

# ==========================================
# P0-1: ESCRITURA ATÓMICA (Extraído de execution_pipeline_dsl.py)
# ==========================================
def atomic_write_json(path: str, data: dict) -> None:
    """Escritura atómica para evitar corrupción si el proceso muere."""
    dir_name = os.path.dirname(path) or "."
    os.makedirs(dir_name, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(dir=dir_name, prefix=".tmp_", suffix=".json")
    try:
        with os.fdopen(fd, "w") as f:
            json.dump(data, f, indent=2, default=str)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_path, path)
    except Exception:
        if os.path.exists(tmp_path):
            try: os.unlink(tmp_path)
            except Exception: pass
        raise

# ==========================================
# P0-4: EXPONENTIAL BACKOFF (Extraído de execution_pipeline_dsl.py)
# ==========================================
def exponential_backoff(attempt: int, base: float = 1.0, cap: float = 60.0) -> float:
    delay = min(cap, base * (2 ** attempt))
    jitter = random.uniform(0, delay * 0.1)
    return delay + jitter

# ==========================================
# P0-3: CIRCUIT BREAKER (Extraído de execution_pipeline_dsl.py)
# ==========================================
class CircuitOpenError(Exception): pass

class CircuitBreaker:
    def __init__(self, name: str, failure_threshold: int = 5, cooldown: float = 60.0):
        self.name = name
        self.failure_threshold = failure_threshold
        self.cooldown = cooldown
        self.failures = 0
        self.last_failure_ts = 0.0
        self.state = "closed"
        self._lock = threading.Lock()

    def call(self, fn, *args, **kwargs):
        with self._lock:
            if self.state == "open":
                if time.time() - self.last_failure_ts > self.cooldown:
                    self.state = "half_open"
                else:
                    raise CircuitOpenError(f"Circuit '{self.name}' is OPEN")
        try:
            result = fn(*args, **kwargs)
            with self._lock:
                if self.state == "half_open":
                    self.state = "closed"
                    self.failures = 0
            return result
        except Exception:
            with self._lock:
                self.failures += 1
                self.last_failure_ts = time.time()
                if self.failures >= self.failure_threshold:
                    self.state = "open"
            raise

# ==========================================
# P0-6: DEAD LETTER QUEUE (Extraído de execution_pipeline_dsl.py)
# ==========================================
class DeadLetterQueue:
    DLQ_PATH = "dead_letter.json"

    @classmethod
    def push(cls, node_id: str, input_snapshot: dict, attempts: int, last_error: str):
        dlq = []
        if os.path.exists(cls.DLQ_PATH):
            try:
                with open(cls.DLQ_PATH) as f: dlq = json.load(f)
            except Exception: dlq = []
        dlq.append({
            "node_id": node_id, "input_snapshot": input_snapshot,
            "attempts": attempts, "last_error": last_error, "ts": time.time(),
        })
        try: atomic_write_json(cls.DLQ_PATH, dlq)
        except Exception: pass

# ==========================================
# P0-8: HEALTH CHECKS (Extraído de execution_pipeline_dsl.py)
# ==========================================
class HealthChecker:
    HEALTH_PATH = "health.json"

    @classmethod
    def refresh(cls, in_flight_node: str = None, status: str = "alive"):
        try:
            atomic_write_json(cls.HEALTH_PATH, {
                "alive": status == "alive",
                "ts": time.time(),
                "in_flight_node": in_flight_node,
                "status": status,
            })
        except Exception:
            pass
