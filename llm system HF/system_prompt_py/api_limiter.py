# api_limiter.py
import time
import threading
from collections import deque
from typing import Dict, Optional

class TokenBucket:
    """
    Implementación de Token Bucket con ventana deslizante para evitar Rate Limits.
    Controla tanto RPM (Requests Per Minute) como TPM (Tokens Per Minute).
    """
    def __init__(self, rpm: int, tpm: int):
        self.rpm = rpm
        self.tpm = tpm
        self.request_timestamps = deque()
        self.token_timestamps = deque()
        self.lock = threading.Lock()

    def _clean_expired(self, now: float) -> None:
        """Limpia los registros que tienen más de 60 segundos de antigüedad."""
        while self.request_timestamps and now - self.request_timestamps[0] > 60:
            self.request_timestamps.popleft()
        while self.token_timestamps and now - self.token_timestamps[0][0] > 60:
            self.token_timestamps.popleft()

    def acquire(self, estimated_tokens: int = 1000, timeout: float = 60.0) -> bool:
        """
        Intenta adquirir un slot. Si no hay cupo, espera y reintenta hasta el timeout.
        Retorna True si se adquirió, False si se agotó el timeout.
        """
        start_time = time.time()
        while time.time() - start_time < timeout:
            with self.lock:
                now = time.time()
                self._clean_expired(now)
                
                current_rpm = len(self.request_timestamps)
                current_tpm = sum(t for _, t in self.token_timestamps)

                if current_rpm < self.rpm and (current_tpm + estimated_tokens) <= self.tpm:
                    # Hay cupo: registramos la petición y los tokens
                    self.request_timestamps.append(now)
                    self.token_timestamps.append((now, estimated_tokens))
                    return True
            
            # Si no hay cupo, esperamos un poco antes de volver a verificar
            time.sleep(1.0)
        
        return False

# Configuración estricta basada en la investigación:
# Groq Free: 30 RPM, 8K TPM
# NVIDIA NIM: 40 RPM (TPM es muy alto, lo dejamos alto)
LIMITERS: Dict[str, TokenBucket] = {
    "groq": TokenBucket(rpm=30, tpm=8000),
    "nvidia": TokenBucket(rpm=40, tpm=100000),
}

def wait_for_slot(provider: str, estimated_tokens: int = 1000, timeout: float = 60.0) -> bool:
    """Función de acceso rápido para obtener un slot del proveedor."""
    limiter = LIMITERS.get(provider)
    if not limiter:
        return True
    return limiter.acquire(estimated_tokens, timeout)
