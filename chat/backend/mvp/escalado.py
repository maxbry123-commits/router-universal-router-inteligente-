"""Escalado bajo demanda: maximo 3 servidores HF CPU 32 GB. Este Router es el destino local; los otros vienen de RIU_SCALE_TARGETS."""
import asyncio
import json
import os
import time
from urllib import error, request

MAX_DESTINOS, UMBRAL, SUENO, CAIDA, ESPERA_DESPERTAR = 3, 85.0, 300, 30, 180
_uso, _caida, _vuelo = {}, {}, {}  # url -> ultimo contacto / ultima caida / trabajos en curso
try:
    import psutil
    psutil.cpu_percent(None)  # primera lectura: las siguientes miden desde aqui sin bloquear
except ImportError:
    psutil = None


class DestinoError(RuntimeError):
    """El destino respondio con un error que reintentar no arregla (4xx) o no despierta a tiempo."""


def remotos():
    urls = []
    for u in os.environ.get("RIU_SCALE_TARGETS", "").split(","):
        u = u.strip().rstrip("/")
        if u.startswith("https://") and u not in urls:
            urls.append(u)
    return urls[:MAX_DESTINOS - 1]


def capacidad():
    return max(1, int(os.environ.get("RIU_SCALE_CAPACITY", "6")))


def cpu_local():
    """CPU real del servidor normalizada de 0 a 100 (no RAM)."""
    if psutil:
        return float(psutil.cpu_percent(None))
    return min(100.0, os.getloadavg()[0] / (os.cpu_count() or 1) * 100)


def despierto(url):
    return time.time() - _uso.get(url, 0) < SUENO - 10  # HF lo suspende a los 300 s sin uso


def _http(url, clave, cuerpo=None, timeout=60):
    cab = {"Content-Type": "application/json", "X-API-Key": clave, "X-RIU-Reenviado": "1"}
    sol = request.Request(url, data=None if cuerpo is None else json.dumps(cuerpo).encode(), headers=cab, method="GET" if cuerpo is None else "POST")
    with request.urlopen(sol, timeout=timeout) as r:
        return json.load(r)


async def sonda(url, clave):
    """CPU de un destino que ya esta despierto (nunca se sondea uno dormido)."""
    try:
        return float((await asyncio.to_thread(_http, url + "/health", clave, None, 5))["cpu"])
    except (OSError, ValueError, TypeError, KeyError):
        return None


async def elegir(clave):
    """'local', la URL del siguiente destino con capacidad, o None (todos ocupados: el trabajo espera en cola)."""
    if _vuelo.get("local", 0) < capacidad() and cpu_local() < UMBRAL:
        return "local"
    for url in remotos():
        if time.time() - _caida.get(url, 0) < CAIDA or _vuelo.get(url, 0) >= capacidad():
            continue
        if not despierto(url):
            return url  # dormido: despierta con el propio trabajo, sin consultas previas
        cpu = await sonda(url, clave)
        if cpu is None:
            _caida[url] = time.time()
        elif cpu < UMBRAL:
            return url
    return None


async def enviar(url, clave, accion, cuerpo):
    """POST al destino; reintenta mientras despierta. Con el mismo request_id un reintento nunca ejecuta dos veces."""
    limite = time.time() + ESPERA_DESPERTAR
    while True:
        try:
            r = await asyncio.to_thread(_http, url + "/plugins/puente_chat/call/" + accion, clave, cuerpo, 60)
            _uso[url] = time.time()
            return r.get("result", r)
        except error.HTTPError as exc:
            if exc.code < 500 and exc.code != 429:
                raise DestinoError("destino HTTP " + str(exc.code)) from None
        except (OSError, ValueError):
            pass
        if time.time() > limite:
            _caida[url] = time.time()
            raise DestinoError("destino no disponible")
        await asyncio.sleep(3)


def entrar(destino):
    _vuelo[destino] = _vuelo.get(destino, 0) + 1


def salir(destino):
    _vuelo[destino] = max(0, _vuelo.get(destino, 0) - 1)
