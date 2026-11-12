import time
import threading
from typing import List, Dict, Optional

class KeyPool:
    def __init__(self, provider: str, keys: List[str], cooldown_s: float = 60.0):
        self.provider = provider
        self.keys = [k for k in keys if k.strip()]
        self.cooldown_s = cooldown_s
        self.cooldowns: Dict[str, float] = {k: 0.0 for k in self.keys}
        self.session_keys: Dict[str, str] = {}
        self._index = 0
        self.lock = threading.Lock()

    def get_key(self, session_id: Optional[str] = None) -> Optional[str]:
        with self.lock:
            now = time.time()
            if session_id and session_id in self.session_keys:
                sticky_key = self.session_keys[session_id]
                if sticky_key in self.cooldowns and now >= self.cooldowns.get(sticky_key, 0):
                    return sticky_key
                else:
                    del self.session_keys[session_id]

            for _ in range(len(self.keys)):
                if not self.keys:
                    return None
                key = self.keys[self._index]
                self._index = (self._index + 1) % len(self.keys)
                if now >= self.cooldowns.get(key, 0):
                    if session_id:
                        self.session_keys[session_id] = key
                    return key
            return None

    def mark_rate_limited(self, key: str):
        with self.lock:
            self.cooldowns[key] = time.time() + self.cooldown_s
            self.session_keys = {sid: k for sid, k in self.session_keys.items() if k != key}
