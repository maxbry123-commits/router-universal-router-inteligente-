"""Hash-only API Key Manager for Router Inteligente Universal."""
from __future__ import annotations
import hashlib, hmac, secrets, threading, time, uuid
from dataclasses import dataclass, field
from typing import Iterable

@dataclass
class KeyRecord:
    key_id: str
    agent_id: str
    salt: str
    key_hash: str
    scopes: tuple[str, ...] = ("route",)
    allowed_models: tuple[str, ...] = ()
    status: str = "active"
    created_at: float = field(default_factory=time.time)
    rotated_at: float | None = None
    revoked_at: float | None = None
    def public(self) -> dict:
        return {"key_id":self.key_id,"agent_id":self.agent_id,"scopes":list(self.scopes),"allowed_models":list(self.allowed_models),"status":self.status,"created_at":self.created_at,"rotated_at":self.rotated_at,"revoked_at":self.revoked_at}

class APIKeyManager:
    MAX_SLOTS = 100
    ITERATIONS = 200_000
    def __init__(self) -> None:
        self._records: dict[str, KeyRecord] = {}
        self._lock = threading.RLock()
    @staticmethod
    def _digest(key: str, salt_hex: str) -> str:
        return hashlib.pbkdf2_hmac("sha256", key.encode(), bytes.fromhex(salt_hex), APIKeyManager.ITERATIONS).hex()
    @staticmethod
    def _new_plaintext(agent_id: str) -> str:
        safe = "".join(c for c in agent_id if c.isalnum() or c in "-_")[:48]
        if not safe: raise ValueError("agent_id_invalido")
        return f"riu_{safe}_{secrets.token_urlsafe(32)}"
    def create(self, agent_id: str, scopes: Iterable[str] = ("route",), allowed_models: Iterable[str] = ()) -> tuple[str, dict]:
        with self._lock:
            if len(self._records) >= self.MAX_SLOTS: raise RuntimeError("max_slots_100")
            plain, salt = self._new_plaintext(agent_id), secrets.token_hex(16)
            rec = KeyRecord(f"key_{uuid.uuid4().hex[:20]}", agent_id, salt, self._digest(plain,salt), tuple(sorted(set(scopes))), tuple(sorted(set(allowed_models))))
            self._records[rec.key_id] = rec
            return plain, rec.public()
    def verify(self, plaintext: str, scope: str = "route", model_id: str | None = None) -> dict | None:
        if not plaintext or not plaintext.startswith("riu_"): return None
        with self._lock:
            for rec in self._records.values():
                if rec.status != "active": continue
                if not hmac.compare_digest(self._digest(plaintext, rec.salt), rec.key_hash): continue
                if scope not in rec.scopes: return None
                if model_id and rec.allowed_models and model_id not in rec.allowed_models: return None
                return rec.public()
        return None
    def revoke(self, key_id: str) -> bool:
        with self._lock:
            rec = self._records.get(key_id)
            if not rec: return False
            rec.status, rec.revoked_at = "revoked", time.time(); return True
    def rotate(self, key_id: str) -> tuple[str, dict]:
        with self._lock:
            rec = self._records.get(key_id)
            if not rec: raise KeyError("key_id_no_existe")
            plain, salt = self._new_plaintext(rec.agent_id), secrets.token_hex(16)
            rec.salt, rec.key_hash = salt, self._digest(plain,salt)
            rec.status, rec.rotated_at, rec.revoked_at = "active", time.time(), None
            return plain, rec.public()
    def list(self) -> list[dict]:
        with self._lock: return [r.public() for r in self._records.values()]
    def hash_state(self) -> list[dict]:
        with self._lock: return [{**r.public(),"salt":r.salt,"key_hash":r.key_hash} for r in self._records.values()]
