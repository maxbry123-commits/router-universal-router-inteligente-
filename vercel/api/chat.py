"""api/chat.py — Funcion serverless de Vercel: el TRIGGER que despierta el router.

Por que existe: los Spaces de HF se duermen y mientras duermen HF devuelve 404.
El chat no puede vivir en un Space dormido, asi que la UI va servida por Vercel
(sin coste de CPU) y esta funcion es la que:

  1. llama al proxy del Grupo 1 (3 espejos, rotando)
  2. si el Space esta dormido o reiniciandose (404/503), ESPERA y reintenta
     (la llamada al Space lo despierta: HF despierta al primer visitante)
  3. devuelve la respuesta tal cual, sin inventar nada

Variables de entorno (Vercel):
  ROUTER_BASE_URL   por defecto https://comand-center-1-space-grupo-1-router-mvp-1.hf.space
  ROUTER_API_KEY    la clave del router (cabecera x-api-key)
  ROUTER_MIRRORS    lista de espejos separados por coma (opcional)
"""
import json
import os
import time
import urllib.error
import urllib.request

BASE = os.environ.get(
    "ROUTER_BASE_URL",
    "https://comand-center-1-space-grupo-1-router-mvp-1.hf.space",
).rstrip("/")
KEY = os.environ.get("ROUTER_API_KEY", "") or os.environ.get("UNIVERSAL_KEY", "")
MIRRORS = [
    m.strip() for m in os.environ.get(
        "ROUTER_MIRRORS",
        "https://comand-center-1-space-grupo-1-router-mvp-1.hf.space,"
        "https://comand-center-1-space-grupo-1-router-mvp-1-v2.hf.space,"
        "https://comand-center-1-space-grupo-1-router-mvp-1-v7.hf.space",
    ).split(",") if m.strip()
]
# Cuanto espera al Space dormido: HF necesita ~30-60 s para despertar el contenedor.
INTENTOS = int(os.environ.get("TRIGGER_INTENTOS", "14"))
PAUSA_S = float(os.environ.get("TRIGGER_PAUSA_S", "5"))
TIMEOUT_S = float(os.environ.get("TRIGGER_TIMEOUT_S", "120"))

CORS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "Content-Type, x-api-key",
    "Access-Control-Allow-Methods": "POST, OPTIONS",
    "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
}


def _post(url, payload, timeout, key):
    datos = json.dumps(payload).encode()
    req = urllib.request.Request(
        url + "/v1/chat/completions", data=datos, method="POST",
        headers={"Content-Type": "application/json", "x-api-key": key},
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        crudo = r.read().decode("utf-8", "replace")
        try:
            return r.status, json.loads(crudo)
        except Exception:
            return r.status, {"raw": crudo[:2000]}


def handler(request):
    if request.method == "OPTIONS":
        return (204, CORS, "")

    # La clave puede venir de las dos fuentes: la que teclea el usuario en el
    # chat (cabecera x-api-key) o la variable de entorno de Vercel. Con una de
    # las dos basta; no hace falta tocar el panel de Vercel.
    key = ""
    cabeceras = getattr(request, "headers", None) or {}
    try:
        key = cabeceras.get("x-api-key") or cabeceras.get("X-API-Key") or ""
    except Exception:
        key = ""
    key = key or KEY
    if not key:
        return (401, CORS, json.dumps({"error": {
            "message": "falta la clave del router: tecleala en el chat o define ROUTER_API_KEY en Vercel",
            "http": 401}}))

    try:
        body = json.loads(request.body or b"{}")
    except Exception:
        body = {}
    messages = body.get("messages") or []
    if not messages:
        return (400, CORS, json.dumps({"error": {"message": "messages vacio"}}))

    payload = {
        "model": body.get("model") or "auto",
        "messages": messages,
    }
    if body.get("max_tokens"):
        payload["max_tokens"] = int(body["max_tokens"])
    if body.get("temperature") is not None:
        payload["temperature"] = float(body["temperature"])

    ultimo = {"error": {"message": "sin respuesta del router"}}
    for intento in range(INTENTOS):
        base = MIRRORS[intento % len(MIRRORS)] if MIRRORS else BASE
        try:
            status, data = _post(base.rstrip("/"), payload, TIMEOUT_S, key)
            if status == 200:
                data = dict(data)
                data.setdefault("trigger", {})["vacio"] = False
                data["trigger"]["intento"] = intento + 1
                data["trigger"]["espejo"] = base
                return (200, CORS, json.dumps(data, ensure_ascii=False))
            ultimo = data
        except urllib.error.HTTPError as e:
            try:
                crudo = e.read().decode("utf-8", "replace")[:300]
            except Exception:
                crudo = "HTTP %s" % e.code
            # 404/503 = Space dormido o reiniciandose: se reintenta (el trigger lo despierta)
            if e.code in (404, 429, 500, 502, 503, 504):
                ultimo = {"error": {"code": "ESPACIO_DORMIDO", "http": e.code, "detalle": crudo}}
            else:
                return (e.code, CORS, json.dumps({"error": {"http": e.code, "detalle": crudo}}))
        except Exception as e:  # timeout, red, DNS
            ultimo = {"error": {"code": "ESPACIO_NO_RESPONDE", "detalle": repr(e)[:200]}}
        time.sleep(PAUSA_S)

    return (503, CORS, json.dumps(dict(ultimo, trigger={"despertado": False, "intentos": INTENTOS})))
