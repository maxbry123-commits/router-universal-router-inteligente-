"""Mantener encendido el Space mientras haya tareas largas: se pide /health por su URL publica cada LATIDO_S.
Hugging Face cuenta ese trafico y no lo duerme; sin tareas en curso el latido se detiene solo."""
import asyncio
import json
import os
import time
import urllib.request

from mvp import hf_store

LATIDO_S = int(os.environ.get("RIU_LATIDO_S", "300"))
GRACIA_S = int(os.environ.get("RIU_GRACIA_S", "300"))  # tras la ultima tarea el Space sigue despierto 5 min: da tiempo a que el chat se reconecte y recoja la respuesta
_tarea = None
ULTIMO = {"t": 0.0, "ok": None}
SIEMPRE_H = 24 * 365 * 10  # «hasta que yo lo apague»: 10 anos
SIEMPRE = {"on": False}
NOMBRE = "chat_estado/mantener.json"
HASTA = {"t": 0.0}  # el Space se mantiene despierto hasta esta hora (epoch), haya o no tareas


def _ping(url):
    try:
        urllib.request.urlopen(url, timeout=20).read(1)
        return True
    except OSError:
        return False


async def _bucle(contar, ping):
    host = os.environ.get("SPACE_HOST", "")
    gracia = 0.0
    while True:
        activo = contar()
        if activo:
            gracia = time.time() + GRACIA_S
        if not (activo or gracia > time.time() or time.time() < HASTA["t"]):
            break
        if host:
            ULTIMO.update(t=time.time(), ok=await asyncio.to_thread(ping, "https://%s/health" % host))
        await asyncio.sleep(LATIDO_S)


def asegurar(contar, ping=_ping):
    """Arranca el latido si no esta corriendo; devuelve True si lo arranco."""
    global _tarea
    if _tarea is not None and not _tarea.done():
        return False
    _tarea = asyncio.get_running_loop().create_task(_bucle(contar, ping))
    return True


def mantener(horas, contar, ping=_ping):
    """Mantiene el Space despierto `horas` desde ahora (aunque no haya tareas). Devuelve la hora limite (epoch)."""
    HASTA["t"] = time.time() + horas * 3600 if horas > 0 else 0.0
    if horas <= 0:
        return HASTA["t"]
    try:
        asegurar(contar, ping)
    except RuntimeError:  # sin bucle de eventos todavia: el arranque lo volvera a pedir con la primera tarea
        pass
    return HASTA["t"]


def guardar(banco, siempre):
    """Recuerda la eleccion del Director (sobrevive a reinicios). Mejor esfuerzo."""
    SIEMPRE["on"] = bool(siempre)
    try:
        hf_store.guardar(banco.leer("HF_TOKEN") if banco else None, NOMBRE, json.dumps({"siempre": bool(siempre)}))
    except (ValueError, RuntimeError, TypeError):
        pass


def leer(banco):
    """True/False si el Director ya eligio; None si nunca lo hizo (rige el plazo por defecto)."""
    try:
        v = json.loads(hf_store.leer(banco.leer("HF_TOKEN") if banco else None, NOMBRE)["valor"])["siempre"]
        return bool(v)
    except (ValueError, RuntimeError, TypeError, KeyError):
        return None
