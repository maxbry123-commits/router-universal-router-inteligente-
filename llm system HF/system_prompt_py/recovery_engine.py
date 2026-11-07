# recovery_engine.py
import time
import random
import threading
import json
import os
from enum import Enum
from typing import Callable, Any, Optional

# --- CIRCUIT BREAKER ---
class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"

class CircuitOpenError(Exception):
    """Excepción lanzada cuando el circuito está abierto y no permite llamadas."""
    pass

class CircuitBreaker:
    def __init__(self, name: str, failure_threshold: int = 5, cooldown: float = 60.0):
        self.name = name
        self.failure_threshold = failure_threshold
        self.cooldown = cooldown
        self.failures = 0
        self.last_failure_time = 0.0
        self.state = CircuitState.CLOSED
        self.lock = threading.Lock()

    def call(self, func: Callable, *args, **kwargs) -> Any:
        with self.lock:
            if self.state == CircuitState.OPEN:
                if time.time() - self.last_failure_time > self.cooldown:
                    self.state = CircuitState.HALF_OPEN
                else:
                    raise CircuitOpenError(f"Circuito '{self.name}' abierto. Esperando cooldown.")

        try:
            result = func(*args, **kwargs)
            with self.lock:
                if self.state == CircuitState.HALF_OPEN:
                    self.state = CircuitState.CLOSED
                    self.failures = 0
            return result
        except Exception as e:
            with self.lock:
                self.failures += 1
                self.last_failure_time = time.time()
                if self.failures >= self.failure_threshold:
                    self.state = CircuitState.OPEN
            raise e

# --- DEAD LETTER QUEUE (DLQ) ---
class DeadLetterQueue:
    """Guarda las tareas que fallaron permanentemente para revisión manual."""
    def __init__(self, filepath: str = "dead_letter.json"):
        self.filepath = filepath
        self.lock = threading.Lock()

    def push(self, provider: str, error: str, payload: dict) -> None:
        with self.lock:
            data = []
            if os.path.exists(self.filepath):
                try:
                    with open(self.filepath, "r", encoding="utf-8") as f:
                        data = json.load(f)
                except json.JSONDecodeError:
                    data = []
            
            data.append({
                "timestamp": time.time(),
                "provider": provider,
                "error": error,
                "payload": payload
            })
            
            tmp_path = self.filepath + ".tmp"
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            os.replace(tmp_path, self.filepath)

# --- BACKOFF EXPONENCIAL ---
def exponential_backoff(attempt: int, base: float = 1.0, cap: float = 30.0) -> float:
    """Calcula el tiempo de espera exponencial con jitter."""
    delay = min(cap, base * (2 ** attempt))
    jitter = random.uniform(0, delay * 0.1)
    return delay + jitter

# --- MOTOR DE RECUPERACIÓN PRINCIPAL ---
BREAKERS = {
    "groq": CircuitBreaker("groq", failure_threshold=5, cooldown=60.0),
    "nvidia": CircuitBreaker("nvidia", failure_threshold=5, cooldown=60.0),
}
DLQ = DeadLetterQueue()

def call_with_recovery(provider: str, func: Callable, max_retries: int = 3, payload_for_dlq: Optional[dict] = None) -> Any:
    """
    Ejecuta una función con protección de Circuit Breaker y reintentos.
    Si falla permanentemente, guarda en la Dead Letter Queue.
    """
    breaker = BREAKERS.get(provider)
    if not breaker:
        return func()

    last_error = None
    for attempt in range(max_retries):
        try:
            return breaker.call(func)
        except CircuitOpenError as e:
            # El circuito está abierto, no reintentamos, pasamos al fallback
            last_error = e
            break
        except Exception as e:
            last_error = e
            if attempt < max_retries - 1:
                sleep_time = exponential_backoff(attempt)
                time.sleep(sleep_time)
            else:
                # Se agotaron los reintentos
                if payload_for_dlq:
                    DLQ.push(provider, str(e), payload_for_dlq)
                raise last_error
                
    raise last_error if last_error else RuntimeError("Fallo desconocido en recovery_engine")
