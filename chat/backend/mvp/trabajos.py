"""Registro persistente de trabajos asincronos: cualquier proceso puede iniciar o consultar un trabajo (usa el mismo /almacen HF)."""
import json
import logging
import re
from mvp import hf_store


def identificador(request_id, azar):
    limpio = re.sub(r"[^A-Za-z0-9_-]", "-", str(request_id or ""))[:64]
    return "p-" + (limpio or azar)


def _nombre(pid):
    return "trabajos/" + pid + ".json"


def guardar(banco, pid, doc):
    """Mejor esfuerzo: si HF falla el trabajo sigue en memoria y se avisa en el log."""
    try:
        hf_store.guardar(banco.leer("HF_TOKEN") if banco else None, _nombre(pid), json.dumps(doc, ensure_ascii=False))
    except (ValueError, RuntimeError, TypeError) as exc:
        logging.getLogger(__name__).warning("trabajo %s no persistido: %s", pid, exc)


def leer(banco, pid):
    try:
        return json.loads(hf_store.leer(banco.leer("HF_TOKEN") if banco else None, _nombre(pid))["valor"])
    except (ValueError, RuntimeError, TypeError, KeyError):
        return None
