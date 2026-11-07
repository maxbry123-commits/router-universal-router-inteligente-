# proxy_improvements.py
# Mejoras P0: cooldown exacto desde headers, espera inteligente, stats
import time
import threading
from typing import Dict, List, Optional
from dataclasses import dataclass, field

@dataclass
class KeyStats:
    key_id: str
    requests: int = 0
    errors: int = 0
    last_429: float = 0.0
    cooldown_until: float = 0.0
    remaining_requests: Optional[int] = None
    remaining_tokens: Optional[int] = None
    score: float = 1.0

class ImprovedKeyPool:
    """
    KeyPool mejorado con:
    - Cooldown exacto desde retry-after / x-ratelimit-reset-requests
    - Espera inteligente cuando todo el pool está en cooldown
    - Stats por key
    """
    def __init__(self, provider: str, keys: List[str]):
        self.provider = provider
        self.keys = [k for k in keys if k.strip()]
        self.stats: Dict[str, KeyStats] = {k: KeyStats(key_id=k[-8:]) for k in self.keys}
        self.lock = threading.Lock()
        self.idx = 0

    def get_key(self) -> Optional[str]:
        with self.lock:
            now = time.time()
            available = [k for k in self.keys if self.stats[k].cooldown_until <= now]
            if not available:
                return None
            # Least-recently-used entre disponibles
            key = min(available, key=lambda k: self.stats[k].requests)
            self.stats[key].requests += 1
            return key

    def mark_rate_limited(self, key: str, retry_after: float = 60.0):
        with self.lock:
            self.stats[key].cooldown_until = time.time() + retry_after
            self.stats[key].last_429 = time.time()
            self.stats[key].errors += 1
            self.stats[key].score = max(0.0, self.stats[key].score - 0.2)

    def update_from_headers(self, key: str, headers: dict):
        """Lee remaining y reset desde headers de Groq/NVIDIA."""
        with self.lock:
            s = self.stats[key]
            # Groq: x-ratelimit-remaining-requests, x-ratelimit-remaining-tokens
            rem_req = headers.get("x-ratelimit-remaining-requests")
            rem_tok = headers.get("x-ratelimit-remaining-tokens")
            if rem_req:
                s.remaining_requests = int(rem_req)
            if rem_tok:
                s.remaining_tokens = int(rem_tok)

    def time_until_available(self) -> float:
        with self.lock:
            now = time.time()
            cooldowns = [s.cooldown_until for s in self.stats.values() if s.cooldown_until > now]
            if not cooldowns:
                return 0.0
            return min(cooldowns) - now

    def get_stats(self) -> List[dict]:
        with self.lock:
            now = time.time()
            return [{
                "key_id": s.key_id,
                "requests": s.requests,
                "errors": s.errors,
                "score": round(s.score, 2),
                "cooldown_remaining": max(0, round(s.cooldown_until - now, 1)),
                "remaining_requests": s.remaining_requests,
                "remaining_tokens": s.remaining_tokens
            } for s in self.stats.values()]

def parse_retry_after(headers: dict) -> float:
    """Extrae segundos de retry-after o x-ratelimit-reset-requests."""
    # retry-after (segundos o HTTP date)
    ra = headers.get("retry-after")
    if ra:
        try:
            return float(ra)
        except:
            pass
    # Groq: x-ratelimit-reset-requests (ej. "1m26.4s")
    reset = headers.get("x-ratelimit-reset-requests")
    if reset:
        # Parse simple: "1m26.4s" -> 86.4
        total = 0.0
        if "m" in reset:
            m, rest = reset.split("m")
            total += float(m) * 60
            reset = rest
        if "s" in reset:
            total += float(reset.replace("s", ""))
        return total if total > 0 else 60.0
    return 60.0
