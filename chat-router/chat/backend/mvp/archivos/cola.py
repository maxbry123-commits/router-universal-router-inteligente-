"""Cola de trabajos: se corre en segundo plano (hilo), uno tras otro; el estado se puede consultar y sobrevive a reinicios."""
import json
import threading
import time
import uuid

from . import trabajo
from .seguridad import MotorError, raiz

_COLAS = {}
_LOCK = threading.Lock()
MAX_COLAS_VIVAS = 2


def _archivo(qid):
    d = raiz() / "_cola"
    d.mkdir(exist_ok=True)
    return d / (qid + ".json")


def _publico(q):
    q = {k: v for k, v in q.items() if not k.startswith("_")}
    hechos = sum(1 for t in q["trabajos"] if t["estado"] in ("ok", "error", "cancelado"))
    actual = next((t for t in q["trabajos"] if t["estado"] == "corriendo"), None)
    q["progreso"] = "%d/%d" % (hechos, len(q["trabajos"]))
    q["paso_actual"] = ("%d %s %s" % (actual["n"], actual["accion"], actual["origen"])) if actual else None
    return q


def _vista(q):
    q2 = dict(q)
    q2["trabajos"] = [{k: v for k, v in t.items() if k != "_job"} for t in q["trabajos"]]
    return _publico(q2)


def _guardar(q):
    _archivo(q["id"]).write_text(json.dumps(_vista(q), ensure_ascii=False), encoding="utf-8")


def _correr(q, token):
    q["estado"] = "corriendo"
    ctx = {"token": token, "cancelado": lambda: q["_cancelar"].is_set(), "notas": []}
    for t in q["trabajos"]:
        if q["_cancelar"].is_set():
            t["estado"] = "cancelado" if t["estado"] == "pendiente" else t["estado"]
            continue
        t["estado"] = "corriendo"
        _guardar(q)
        try:
            r = trabajo.ejecutar(t["_job"], ctx)
            t.update(estado="ok", archivos=r["archivos"], bytes=r["bytes"], resumen=r["resumen"], muestra=r["muestra"], destino=r.get("destino", t["destino"]))
        except MotorError as e:
            t.update(estado="error", error=str(e))
        except Exception as e:  # noqa: BLE001 - un trabajo roto no tumba la cola
            t.update(estado="error", error="%s: %s" % (type(e).__name__, str(e)[:300]))
    q["estado"] = "cancelado" if q["_cancelar"].is_set() else ("error" if any(t["estado"] == "error" for t in q["trabajos"]) else "terminado")
    q["fin"] = time.time()
    _guardar(q)


def ejecutar(jobs, token=None):
    """Valida todos los trabajos antes de empezar; devuelve el id de la cola (responde al instante)."""
    if not jobs:
        raise MotorError("COLA_VACIA")
    if len(jobs) > 200:
        raise MotorError("COLA_DEMASIADO_LARGA: maximo 200 trabajos")
    normales = [trabajo.normalizar(j) for j in jobs]
    with _LOCK:
        if sum(1 for q in _COLAS.values() if q["estado"] in ("en_cola", "corriendo")) >= MAX_COLAS_VIVAS:
            raise MotorError("COLAS_OCUPADAS: espera a que termine una cola")
        qid = "q-" + uuid.uuid4().hex[:8]
        q = {"id": qid, "estado": "en_cola", "raiz": str(raiz()), "inicio": time.time(), "_cancelar": threading.Event(),
             "trabajos": [{"n": i + 1, "accion": j["accion"], "origen": j["origen"], "destino": j.get("destino") or "", "estado": "pendiente", "_job": j} for i, j in enumerate(normales)]}
        _COLAS[qid] = q
    _guardar(q)
    threading.Thread(target=_correr, args=(q, token), name="motor-" + qid, daemon=True).start()
    return {"id": qid, "estado": "en_cola", "trabajos": len(normales)}


def estado(qid):
    q = _COLAS.get(qid)
    if q:
        return _vista(q)
    f = _archivo(qid)
    if not f.exists():
        raise MotorError("COLA_NO_EXISTE: " + str(qid))
    d = json.loads(f.read_text(encoding="utf-8"))
    if d.get("estado") in ("en_cola", "corriendo"):  # el servidor se reinicio con la cola a medias
        d["estado"] = "error"
        for t in d["trabajos"]:
            if t["estado"] in ("pendiente", "corriendo"):
                t.update(estado="error", error="INTERRUMPIDO_POR_REINICIO")
    return _publico(d | {"trabajos": [{k: v for k, v in t.items() if k != "_job"} for t in d["trabajos"]]})


def cancelar(qid):
    q = _COLAS.get(qid)
    if not q:
        raise MotorError("COLA_NO_EXISTE: " + str(qid))
    q["_cancelar"].set()
    return {"id": qid, "estado": "cancelado"}
