"""Cliente sin dependencias para el Harness remoto (edificio 2)."""
import json
import os
import time
from urllib import error, request

REINTENTABLES = {429, 502, 503, 504}


def _endpoint():
    base = os.environ.get("RIU_DEEPSEEK_HARNESS_URL", "").rstrip("/")
    if not base:
        raise RuntimeError("Harness no configurado")
    if not (base.startswith("https://") or base.startswith("http://127.0.0.1:")):
        raise ValueError("URL Harness requiere HTTPS")
    return base + "/invoke"


def _enviar(accion, datos, clave):
    if accion not in ("status", "invoke", "llm"):
        raise ValueError("accion Harness no permitida")
    if not isinstance(clave, str) or not clave:
        raise RuntimeError("credencial Harness ausente en banco")
    url = _endpoint()
    headers = {"Content-Type": "application/json", "X-API-Key": clave}
    cuerpo = json.dumps({"action": accion, **datos}).encode("utf-8")
    solicitud = request.Request(url, data=cuerpo, headers=headers, method="POST")
    for intento in range(3):
        try:
            with request.urlopen(solicitud, timeout=60) as respuesta:
                return json.load(respuesta)
        except error.HTTPError as exc:
            if exc.code not in REINTENTABLES or intento == 2:
                raise RuntimeError("Harness HTTP " + str(exc.code)) from None
        except (error.URLError, TimeoutError, OSError):
            raise RuntimeError("Harness no disponible") from None
        time.sleep(min(2 ** intento, 2))


def status(clave):
    return _enviar("status", {}, clave)


def guardar(clave, nombre, valor):
    return _enviar("invoke", {"tool": "guardar", "args": {"nombre": nombre, "valor": valor}}, clave)


def leer(clave, nombre):
    return _enviar("invoke", {"tool": "leer", "args": {"nombre": nombre}}, clave)


def computar(clave, tarea):
    return _enviar("invoke", {"tool": "computar", "args": {"tarea": tarea}}, clave)


def llm(clave, mensajes, modelo, opciones=None):
    return _enviar("llm", {"mensajes": mensajes, "modelo": modelo,
                          "opciones": opciones or {}}, clave)
