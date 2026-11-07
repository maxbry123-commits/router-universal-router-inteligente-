# retry_controller.py
import time
from core_recovery import DeadLetterQueue, exponential_backoff
from sentinel_observability import Sentinel

class RetryController:
    MAX_RETRIES = 3

    def __init__(self, sentinel: Sentinel):
        self.sentinel = sentinel
        self.dlq = DeadLetterQueue()

    def execute_with_retry(self, node_id: str, func, *args, **kwargs):
        """
        Ejecuta una función con reintentos.
        Si falla los 3 intentos, la envía a la Dead Letter Queue.
        """
        attempts = 0
        while attempts < self.MAX_RETRIES:
            attempts += 1
            try:
                # Ejecuta la función (ej. llamada al LLM)
                result = func(*args, **kwargs)
                self.sentinel.log({"event": "node_success", "node_id": node_id, "attempt": attempts})
                return result
            except Exception as e:
                self.sentinel.log({"event": "node_failed", "node_id": node_id, "attempt": attempts, "error": str(e)})
                if attempts >= self.MAX_RETRIES:
                    # Guardar en la cola de errores para revisión manual
                    self.dlq.push(node_id=node_id, error=str(e), payload=kwargs)
                    raise Exception(f"Fallo permanente en {node_id} tras {attempts} intentos.") from e
                
                # Esperar antes de reintentar (Backoff Exponencial)
                time.sleep(exponential_backoff(attempts, base=0.5, cap=10.0))
