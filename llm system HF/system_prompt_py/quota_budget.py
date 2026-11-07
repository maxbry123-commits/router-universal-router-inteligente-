# quota_budget.py
import time
import threading
from collections import defaultdict
from collections import deque

class QuotaBudget:
    """
    Contador local de RPM/TPM por clave.
    Anticipa el 429 antes de que el proveedor lo devuelva.
    """
    def __init__(self, rpm: int = 30, tpm: int = 8000, window_s: float = 60.0):
        self.rpm = rpm
        self.tpm = tpm
        self.window_s = window_s
        self.requests = defaultdict(lambda: deque())
        self.tokens = defaultdict(lambda: deque())
        self.lock = threading.Lock()

    def _clean(self, key: str, now: float):
        while self.requests[key] and now - self.requests[key][0] > self.window_s:
            self.requests[key].popleft()
        while self.tokens[key] and now - self.tokens[key][0][0] > self.window_s:
            self.tokens[key].popleft()

    def can_use(self, key: str, est_tokens: int = 1000) -> bool:
        """Retorna True si la clave tiene cupo para esta petición."""
        with self.lock:
            now = time.time()
            self._clean(key, now)
            current_rpm = len(self.requests[key])
            current_tpm = sum(t for _, t in self.tokens[key])
            return current_rpm < self.rpm and (current_tpm + est_tokens) <= self.tpm

    def record(self, key: str, est_tokens: int = 1000):
        """Registra una petición exitosa en la ventana deslizante."""
        with self.lock:
            now = time.time()
            self._clean(key, now)
            self.requests[key].append(now)
            self.tokens[key].append((now, est_tokens))

    def remaining_quota(self, key: str) -> dict:
        """Retorna el cupo restante estimado para una clave."""
        with self.lock:
            now = time.time()
            self._clean(key, now)
            return {
                "rpm_remaining": max(0, self.rpm - len(self.requests[key])),
                "tpm_remaining": max(0, self.tpm - sum(t for _, t in self.tokens[key]))
            }
