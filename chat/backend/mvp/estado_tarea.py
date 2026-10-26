"""Estado de una tarea larga en el almacen permanente (bucket HF): el historial completo, con los resultados de las
herramientas, se guarda en cada pausa del Harness; si el Space se reinicia, el Router la retoma desde ahi."""
import base64
import json
import logging
import zlib
from mvp import hf_store

PEDAZO = 600_000  # caracteres por archivo (hf_store admite 1 MB cada uno)
INDICE = "tareas/pendientes.json"


def _t(banco):
    return banco.leer("HF_TOKEN") if banco else None


def _leer(banco, nombre):
    try:
        return hf_store.leer(_t(banco), nombre)["valor"]
    except (hf_store.NoExiste, ValueError, RuntimeError, TypeError, KeyError):
        return None


def guardar(banco, pid, estado):
    """Mejor esfuerzo: un fallo del almacen se avisa en el log y la tarea sigue. Las credenciales se tachan antes de escribir."""
    try:
        crudo = hf_store.PATRON_CLAVE.sub("[REDACTADO]", json.dumps(estado, ensure_ascii=False, default=str))
        datos = base64.b64encode(zlib.compress(crudo.encode("utf-8"), 6)).decode("ascii")
        trozos = [datos[i:i + PEDAZO] for i in range(0, len(datos), PEDAZO)] or [""]
        for i, t in enumerate(trozos):
            hf_store.guardar(_t(banco), "tareas/%s/%d.json" % (pid, i), t)
        hf_store.guardar(_t(banco), "tareas/%s/meta.json" % pid, json.dumps({"n": len(trozos)}))  # el meta va al final: sin el, el estado no se usa
        return True
    except (ValueError, RuntimeError, TypeError) as exc:
        logging.getLogger(__name__).warning("estado de la tarea %s no guardado: %s", pid, exc)
        return False


def leer(banco, pid):
    try:
        n = int(json.loads(_leer(banco, "tareas/%s/meta.json" % pid))["n"])
        datos = "".join(_leer(banco, "tareas/%s/%d.json" % (pid, i)) or "" for i in range(n))
        return json.loads(zlib.decompress(base64.b64decode(datos)).decode("utf-8"))
    except (ValueError, TypeError, KeyError, zlib.error):
        return None


def pendientes(banco):
    try:
        return dict(json.loads(_leer(banco, INDICE) or "{}"))
    except (ValueError, TypeError):
        return {}


def marcar(banco, pid, activa):
    d = pendientes(banco)
    if activa:
        d[pid] = 1
    else:
        d.pop(pid, None)
    try:
        hf_store.guardar(_t(banco), INDICE, json.dumps(d))
    except (ValueError, RuntimeError, TypeError) as exc:
        logging.getLogger(__name__).warning("indice de tareas no guardado: %s", exc)
