"""cola_grupo1.py — COLA del Grupo 1 (compute: HTTP + MCP + almacenamiento/memoria).

El Grupo 1 son 3 Spaces ESPEJO con la MISMA funcion (proxy + HTTP + MCP +
memoria). Este modulo les pone COLA:

  · 1 peticion en vuelo por Space (limite: GRUPO1_MAX_INFLIGHT, por defecto 4)
  · si se alcanza el limite -> 429 con la lista de los OTROS espejos, para que
    el cliente rote y la peticion ESPERE en la cola en vez de caer
  · GET /v1/queue -> el estado real de los 3 espejos (el propio + los otros)

REGLA DE ARQUITECTURA: el Grupo 2 (LLM local) NO participa de esta cola y no
comparte MCP, HTTP ni almacenamiento con el Grupo 1. Cada grupo sirve su
funcion y nada mas.
"""
import os
import threading
import time
from typing import Any, Dict, List

MAX_INFLIGHT = int(os.getenv("GRUPO1_MAX_INFLIGHT", "4"))
ESPACIOS = tuple(x.strip() for x in os.getenv(
    "GRUPO1_SPACES",
    "space-grupo-1-router-mvp-1,space-grupo-1-router-mvp-1-v2,space-grupo-1-router-mvp-1-v7",
).split(",") if x.strip())
BASE = "https://comand-center-1-{}.hf.space"

_lock = threading.Lock()
_inflight = 0
_peak = 0
_started = time.time()


def _me() -> str:
    """SPACE_ID llega como 'COMAND-CENTER-1/space-x': nos quedamos con el nombre."""
    v = os.getenv("SPACE_ID", "") or ""
    if "/" in v:
        v = v.split("/")[-1]
    return v or (ESPACIOS[0] if ESPACIOS else "desconocido")


def try_acquire() -> bool:
    """Entra en la cola. False si el Space esta al limite (-> 429)."""
    global _inflight
    with _lock:
        if _inflight >= MAX_INFLIGHT:
            return False
        _inflight += 1
        return True


def release() -> None:
    global _inflight
    with _lock:
        if _inflight > 0:
            _inflight -= 1


def estado_local() -> Dict[str, Any]:
    with _lock:
        inflight = _inflight
        peak = _peak
    return {
        "espacio": _me(),
        "url": BASE.format(_me()),
        "in_flight": inflight,
        "max_in_flight": MAX_INFLIGHT,
        "libre": inflight < MAX_INFLIGHT,
        "peak": peak,
        "uptime_s": round(time.time() - _started, 1),
    }


def otros_mirrors() -> List[str]:
    me = _me()
    return [BASE.format(s) for s in ESPACIOS if s != me]


async def estado_agregado(timeout_s: float = 4.0) -> Dict[str, Any]:
    """Estado de los 3 espejos: el propio + lo que respondan los otros."""
    import httpx
    propio = estado_local()
    propio["responde"] = True
    otros = []
    for url in otros_mirrors():
        fila = {"url": url, "responde": False, "in_flight": None, "max_in_flight": MAX_INFLIGHT}
        try:
            async with httpx.AsyncClient(timeout=timeout_s) as c:
                r = await c.get(url + "/v1/queue")
            if r.status_code == 200:
                j = r.json()
                fila.update({"responde": True, "in_flight": j.get("in_flight"),
                             "max_in_flight": j.get("max_in_flight"),
                             "libre": j.get("libre")})
        except Exception as e:
            fila["error"] = repr(e)[:90]
        otros.append(fila)
    libres = [f["url"] for f in otros if f.get("libre") and f.get("responde")]
    if propio.get("libre"):
        libres.insert(0, propio["url"])
    return {
        "ok": True,
        "grupo": "grupo_1_compute_proxy",
        "funcion": "HTTP + MCP + almacenamiento/memoria (cola de 3 espejos)",
        "desvinculado_de": "grupo_2_router_llm_hf (solo LLM, no comparte HTTP/MCP/memoria)",
        "este": propio,
        "espejos": otros,
        "libres": libres,
        "siguiente": libres[0] if libres else None,
    }
