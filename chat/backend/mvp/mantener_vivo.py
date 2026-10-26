"""Mantener encendido el Space mientras haya tareas largas: se pide /health por su URL publica cada LATIDO_S.
Hugging Face cuenta ese trafico y no lo duerme; sin tareas en curso el latido se detiene solo."""
import asyncio
import os
import time
import urllib.request

LATIDO_S = int(os.environ.get("RIU_LATIDO_S", "300"))
_tarea = None
ULTIMO = {"t": 0.0, "ok": None}
HASTA = {"t": 0.0}  # el Space se mantiene despierto hasta esta hora (epoch), haya o no tareas


def _ping(url):
    try:
        urllib.request.urlopen(url, timeout=20).read(1)
        return True
    except OSError:
        return False


async def _bucle(contar, ping):
    host = os.environ.get("SPACE_HOST", "")
    while contar() or time.time() < HASTA["t"]:
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
