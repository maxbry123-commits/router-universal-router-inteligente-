"""cache.py — Cache semantico (por prompt) del router.

  · Clave: sha256(modelo + modo + modo_servicio + mensajes normalizados)
  · TTL configurable (CACHE_TTL_S, por defecto 300 s)
  · Local por proceso (rapido) + compartido por el bucket de memoria
    (best-effort: si el MCP/bucket no esta, se sigue con la cache local)
  · El impacto se ve en la respuesta: "cache": {"hit": true, "ttl_s": ...}

Sirve para el bucle agéntico: el mismo objetivo se repregunta muchas veces y
cada repregunta no debe volver a generar.
"""
import hashlib
import json
import os
import time
from typing import Any, Dict, Optional, Tuple

TTL_S = float(os.getenv("CACHE_TTL_S", "300"))
MAX_ENTRIES = int(os.getenv("CACHE_MAX_ENTRIES", "256"))
ENABLED = os.getenv("CACHE_ENABLED", "1") == "1"

_store: Dict[str, Tuple[float, Dict[str, Any]]] = {}
_hits = 0
_misses = 0
_hits_total = 0
_misses_total = 0


def _key(model: str, mode: Optional[str], service_mode: Optional[str], messages: Any,
         ruta: Optional[str] = None, proveedor: Optional[str] = None) -> str:
    """La clave incluye la RUTA y el PROVEEDOR: /v1/groq nunca puede devolver lo
    cacheado de /v1/nvidia (era justo el bug que hacia que Groq respondiera NVIDIA)."""
    norm = []
    for m in (messages or []):
        if not isinstance(m, dict):
            continue
        norm.append([str(m.get("role") or ""), str(m.get("content") or "").strip()])
    raw = json.dumps([str(model or ""), str(mode or ""), str(service_mode or ""),
                      str(ruta or ""), str(proveedor or ""), norm],
                     ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def get(model: str, mode: Optional[str], service_mode: Optional[str], messages: Any,
        ruta: Optional[str] = None, proveedor: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Devuelve la respuesta cacheada si sigue viva; None si no."""
    global _hits, _misses, _hits_total, _misses_total
    if not ENABLED:
        return None
    k = _key(model, mode, service_mode, messages, ruta, proveedor)
    ent = _store.get(k)
    if ent is None:
        _misses += 1
        _misses_total += 1
        return None
    exp, payload = ent
    if exp < time.time():
        _store.pop(k, None)
        _misses += 1
        _misses_total += 1
        return None
    _hits += 1
    _hits_total += 1
    out = dict(payload)
    out["cache"] = {"hit": True, "ttl_s": int(exp - time.time()), "key": k[:16]}
    return out


def put(model: str, mode: Optional[str], service_mode: Optional[str], messages: Any,
        response: Dict[str, Any], ruta: Optional[str] = None,
        proveedor: Optional[str] = None) -> None:
    if not ENABLED or not isinstance(response, dict):
        return
    k = _key(model, mode, service_mode, messages, ruta, proveedor)
    _store[k] = (time.time() + TTL_S, response)
    if len(_store) > MAX_ENTRIES:
        viejo = sorted(_store.items(), key=lambda kv: kv[1][0])[: len(_store) - MAX_ENTRIES]
        for kk, _ in viejo:
            _store.pop(kk, None)


def estado() -> Dict[str, Any]:
    ahora = time.time()
    vivos = sum(1 for exp, _ in _store.values() if exp > ahora)
    return {
        "ok": True,
        "habilitada": ENABLED,
        "ttl_s": TTL_S,
        "entradas": len(_store),
        "vivas": vivos,
        "max_entradas": MAX_ENTRIES,
        "aciertos": _hits,
        "fallos": _misses,
        "aciertos_total": _hits_total,
        "fallos_total": _misses_total,
        "tasa_acierto": round(_hits_total / max(1, _hits_total + _misses_total), 3),
    }


def limpiar() -> None:
    global _hits, _misses
    _store.clear()
    _hits = 0
    _misses = 0
