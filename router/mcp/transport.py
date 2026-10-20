"""Unico punto de salida a red (HTTP). Los tests lo reemplazan por un falso: no hay red en pruebas."""
from __future__ import annotations
import json
import urllib.error
import urllib.request


def http(metodo: str, url: str, headers: dict | None = None, cuerpo=None, espera: float = 40):
    """Devuelve (status, json_o_texto). Un fallo de red lanza OSError (nunca se disfraza de exito)."""
    datos = None
    h = dict(headers or {})
    if cuerpo is not None:
        datos = json.dumps(cuerpo).encode("utf-8")
        h["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=datos, method=metodo, headers=h)
    try:
        with urllib.request.urlopen(req, timeout=espera) as r:
            raw = r.read().decode("utf-8", "replace")
            status = r.status
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", "replace")
        status = e.code
    try:
        return status, (json.loads(raw) if raw else {})
    except ValueError:
        return status, raw


# Reemplazable en pruebas.
enviar = http
