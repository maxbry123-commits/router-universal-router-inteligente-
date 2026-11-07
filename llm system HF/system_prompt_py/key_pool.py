# key_pool.py
import time
import threading
from collections import deque
from typing import List, Dict, Optional

class KeyCooldownError(Exception):
    """Se lanza cuando todas las claves están en cooldown."""
    pass

class KeyPool:
    """
    Pool de claves con rotación round-robin y cooldown por clave.
    Cada clave tiene su propio timestamp de cooldown.
    """
    def __init__(self, provider: str, keys: List[str], cooldown_s: float = 60.0):
        self.provider = provider
        self.keys = keys
        self.cooldown_s = cooldown_s
        self.cooldowns: Dict[str, float] = {k: 0.0 for k in keys}
        self._index = 0
        self.lock = threading.Lock()

    def get_key(self) -> Optional[str]:
        """
        Retorna la siguiente clave disponible.
        Si todas están en cooldown, retorna None.
        """
        with self.lock:
            now = time.time()
            for _ in range(len(self.keys)):
                key = self.keys[self._index]
                self._index = (self._index + 1) % len(self.keys)
                if now >= self.cooldowns[key]:
                    return key
            return None

    def mark_rate_limited(self, key: str):
        """Marca una clave como en cooldown tras un 429."""
        with self.lock:
            self.cooldowns[key] = time.time() + self.cooldown_s

    def available_count(self) -> int:
        """Número de claves actualmente disponibles."""
        now = time.time()
        with self.lock:
            return sum(1 for k in self.keys if now >= self.cooldowns[k])
