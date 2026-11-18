"""semantic_cache.py - Cache de prompt->respuesta con TTL.
Determinista: sha256 del payload. Sin embeddings, sin LLM."""
import hashlib
import json
import os
import time
from pathlib import Path

CACHE_DIR = Path(os.getenv("CACHE_DIR", "state/cache"))
CACHE_DIR.mkdir(parents=True, exist_ok=True)
TTL = int(os.getenv("CACHE_TTL", "3600"))


def _key(payload: dict) -> str:
    """Hash canónico del payload. Ordenado para determinismo."""
    blob = json.dumps(payload, sort_keys=True, ensure_ascii=False).encode()
    return hashlib.sha256(blob).hexdigest()


def get(payload: dict) -> dict | None:
    """Devuelve respuesta cacheada o None si expiró/ausente."""
    k = _key(payload)
    p = CACHE_DIR / f"{k}.json"
    if not p.exists():
        return None
    try:
        d = json.loads(p.read_text("utf-8"))
        if time.time() - d.get("ts", 0) > TTL:
            p.unlink(missing_ok=True)
            return None
        return d.get("resp")
    except Exception:
        return None


def put(payload: dict, resp: dict) -> None:
    """Almacena respuesta. Fail-soft: no rompe si falla el write."""
    try:
        p = CACHE_DIR / f"{_key(payload)}.json"
        p.write_text(
            json.dumps({"ts": time.time(), "resp": resp}, ensure_ascii=False),
            "utf-8",
        )
    except Exception:
        pass


def stats() -> dict:
    """Uso: devuelve cantidad de entradas y tamaño total."""
    try:
        files = list(CACHE_DIR.glob("*.json"))
        size = sum(f.stat().st_size for f in files)
        return {"entries": len(files), "bytes": size, "ttl": TTL}
    except Exception:
        return {"entries": 0, "bytes": 0, "ttl": TTL}


def purge_expired() -> int:
    """Borra entradas expiradas. Devuelve cuántas eliminó."""
    n = 0
    now = time.time()
    for p in CACHE_DIR.glob("*.json"):
        try:
            d = json.loads(p.read_text("utf-8"))
            if now - d.get("ts", 0) > TTL:
                p.unlink()
                n += 1
        except Exception:
            pass
    return n
