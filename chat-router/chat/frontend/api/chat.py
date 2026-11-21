"""api/chat.py — TRIGGER serverless de Vercel.

Por que es una app FastAPI y no un `handler(request)` suelto:
Vercel (docs "Python Runtime with Vercel Functions") exige un ENTRYPOINT
Python valido: un fichero con nombre soportado (app.py / index.py / main.py /
server.py / wsgi.py / asgi.py) que exponga una variable de nivel superior
`app` (ASGI o WSGI). Un `def handler(request)` NO es un entrypoint soportado
=> el build de la funcion falla => el deployment entero se marca "failed"
(pasado: dpl_7tYRECNiM7eGhjoTq2EgEffU8Ypn, 2026-11-20).

Que hace:
  1. Llama al proxy del Grupo 1 (3 espejos, rotando).
  2. Si el Space esta dormido o reiniciandose (404/503), espera y reintenta:
     la llamada es la que lo DESPIERTA.
  3. Acepta la clave del cliente (cabecera `x-api-key`) o la del entorno
     (`ROUTER_API_KEY` / `UNIVERSAL_KEY`).

Variables de entorno:
  ROUTER_BASE_URL    proxy del Grupo 1 (por defecto, el Space vivo)
  ROUTER_MIRRORS     lista de espejos separados por coma (opcional)
  ROUTER_API_KEY     clave del router (cabecera x-api-key)
  RIU_ROUTER_API_KEY como lo llama el panel de Vercel (mismo valor)
  UNIVERSAL_KEY      alternativa a ROUTER_API_KEY
  TRIGGER_INTENTOS   reintentos para despertar el Space (por defecto 10)
  TRIGGER_PAUSA_S    pausa entre reintentos, en segundos (por defecto 5)
  TRIGGER_TIMEOUT_S  timeout de cada peticion al Space (por defecto 45)
"""
import json
import os
import time
import urllib.error
import urllib.request

from fastapi import FastAPI, Request
from fastapi.responses import Response

BASE = os.environ.get(
    "ROUTER_BASE_URL",
    "https://comand-center-1-space-grupo-1-router-mvp-1.hf.space",
).rstrip("/")
KEY = (os.environ.get("ROUTER_API_KEY")
       or os.environ.get("RIU_ROUTER_API_KEY")   # como lo llama el panel de Vercel
       or os.environ.get("UNIVERSAL_KEY")
       or "")
MIRRORS = [
    m.strip() for m in os.environ.get(
        "ROUTER_MIRRORS",
        "https://comand-center-1-space-grupo-1-router-mvp-1.hf.space,"
        "https://comand-center-1-space-grupo-1-router-mvp-1-v2.hf.space,"
        "https://comand-center-1-space-grupo-1-router-mvp-1-v7.hf.space",
    ).split(",") if m.strip()
]
# Cuanto espera al Space dormido: HF necesita ~30-60 s para despertar el contenedor.
INTENTOS = int(os.environ.get("TRIGGER_INTENTOS", "8"))
PAUSA_S = float(os.environ.get("TRIGGER_PAUSA_S", "6"))
TIMEOUT_S = float(os.environ.get("TRIGGER_TIMEOUT_S", "20"))

CORS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "Content-Type, x-api-key",
    "Access-Control-Allow-Methods": "POST, OPTIONS",
    "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
}

app = FastAPI(title="YAIWES · trigger del router")


def _post(base, payload, timeout, key):
    req = urllib.request.Request(
        base + "/v1/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "x-api-key": key,
                 "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                               "(KHTML, like Gecko) Chrome/120.0 Safari/537.36",
                 "Accept": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            crudo = resp.read().decode("utf-8", "replace")
            try:
                return resp.status, json.loads(crudo)
            except Exception:
                return resp.status, {"raw": crudo[:2000]}
    except urllib.error.HTTPError as e:
        try:
            texto = e.read().decode("utf-8", "replace")[:2000]
        except Exception:
            texto = "HTTP %s" % e.code
        return e.code, {"raw": texto}
    except Exception as e:
        raise


# ===== FALLBACK DIRECTO A LOS PROVEEDORES (sin depender de los Spaces de HF) =====
# Si el Space del router esta PAUSED (sin credito prepago), el chat sigue
# funcionando para NVIDIA y Groq: son APIs externas y solo necesitan su clave.
# Las claves vienen del sello del banco (NVIDIA_KEYS / GROQ_KEYS en el servidor).
DIRECTO = {
    "nvidia": ("https://integrate.api.nvidia.com/v1/chat/completions", "NVIDIA_KEYS"),
    "groq": ("https://api.groq.com/openai/v1/chat/completions", "GROQ_KEYS"),
}


def _fallback_directo(modelo, payload):
    """Llama a NVIDIA o Groq directamente. Devuelve (status, datos) o None."""
    m = str(modelo or "").lower()
    if m.startswith("nvidia/"):
        prov = "nvidia"
    elif m.startswith(("openai/", "groq/")):
        prov = "groq"
    else:
        return None
    url, var = DIRECTO[prov]
    claves = [k.strip() for k in os.environ.get(var, "").split(",") if k.strip()]
    if not claves:
        return None
    cuerpo = {"model": modelo, "messages": payload.get("messages") or []}
    if payload.get("max_tokens"):
        cuerpo["max_tokens"] = int(payload["max_tokens"])
    if payload.get("temperature") is not None:
        cuerpo["temperature"] = float(payload["temperature"])
    ultimo = None
    for clave in claves:
        req = urllib.request.Request(
            url, data=json.dumps(cuerpo).encode("utf-8"),
            headers={"Content-Type": "application/json", "Authorization": "Bearer " + clave,
                     # Groq (Cloudflare) bloquea el UA de urllib con 403/1010:
                     # hay que enviar un UA de navegador.
                     "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                                   "(KHTML, like Gecko) Chrome/120.0 Safari/537.36",
                     "Accept": "application/json"},
            method="POST")
        try:
            with urllib.request.urlopen(req, timeout=TIMEOUT_S) as resp:
                crudo = resp.read().decode("utf-8", "replace")
                try:
                    return resp.status, json.loads(crudo)
                except Exception:
                    return resp.status, {"raw": crudo[:2000]}
        except urllib.error.HTTPError as e:
            ultimo = {"http": e.code, "detalle": e.read().decode("utf-8", "replace")[:300]}
        except Exception as e:
            ultimo = {"http": 0, "detalle": repr(e)[:200]}
        time.sleep(0.4)
    return ( ultimo.get("http", 0) if ultimo else 0, {"error": ultimo} )


async def _core(request: Request):
    """Logica del trigger. Devuelve (status, headers, cuerpo JSON)."""
    if request.method == "OPTIONS":
        return (204, CORS, "")

    # La clave puede venir de las dos fuentes: la que teclea el usuario en el
    # chat (cabecera x-api-key) o la variable de entorno de Vercel. Con una de
    # las dos basta; no hace falta tocar el panel de Vercel.
    key = ""
    try:
        key = request.headers.get("x-api-key") or request.headers.get("X-API-Key") or ""
    except Exception:
        key = ""
    key = key or KEY
    if not key:
        return (401, CORS, json.dumps({"error": {
            "message": "falta la clave del router: tecleala en el chat o define ROUTER_API_KEY en Vercel",
            "http": 401}}))

    crudo = b""
    try:
        crudo = await request.body()
    except Exception:
        crudo = b""
    try:
        body = json.loads(crudo or b"{}")
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

    # --- PRIMERO: el Space. Si no responde (PAUSED / 503 / sin credito), se va
    # DIRECTO al proveedor externo (NVIDIA/Groq) para que el chat no se caiga.
    try:
        base0 = (MIRRORS[0] if MIRRORS else BASE).rstrip("/")
        st0, d0 = _post(base0, payload, 12, key)
        if st0 == 200:
            d0 = dict(d0)
            d0.setdefault("trigger", {})["vacio"] = False
            d0["trigger"]["ruta"] = "space"
            return (200, CORS, json.dumps(d0, ensure_ascii=False))
        if st0 in (503, 502, 404, 0):
            fb = _fallback_directo(payload.get("model"), payload)
            if fb:
                sfb, dfb = fb
                if sfb == 200:
                    dfb = dict(dfb)
                    dfb.setdefault("trigger", {})["vacio"] = False
                    dfb["trigger"]["ruta"] = "directo (sin Space)"
                    return (200, CORS, json.dumps(dfb, ensure_ascii=False))
    except Exception:
        pass
    fb = _fallback_directo(payload.get("model"), payload)
    if fb:
        sfb, dfb = fb
        if sfb == 200:
            dfb = dict(dfb)
            dfb.setdefault("trigger", {})["vacio"] = False
            dfb["trigger"]["ruta"] = "directo (sin Space)"
            return (200, CORS, json.dumps(dfb, ensure_ascii=False))

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
            # 404/503 = Space dormido o reiniciandose: se reintenta (el trigger lo despierta)
            detalle = (data.get("raw") if isinstance(data, dict) else None) or str(data)[:300]
            if status in (404, 429, 500, 502, 503, 504):
                ultimo = {"error": {"code": "ESPACIO_DORMIDO", "http": status,
                                    "detalle": str(detalle)[:300]}}
            else:
                return (status, CORS, json.dumps({"error": {"http": status,
                                                            "detalle": str(detalle)[:300]}}))
        except Exception as e:  # timeout, red, DNS
            ultimo = {"error": {"code": "ESPACIO_NO_RESPONDE", "detalle": repr(e)[:200]}}
        if intento < INTENTOS - 1:
            time.sleep(PAUSA_S)

    return (503, CORS, json.dumps(dict(ultimo, trigger={"despertado": False, "intentos": INTENTOS})))


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "rol": "trigger",
        "base": BASE,
        "espejos": MIRRORS,
        "intentos": INTENTOS,
    }


@app.api_route("/", methods=["POST", "OPTIONS"])
@app.api_route("/api/chat", methods=["POST", "OPTIONS"])
async def chat(request: Request):
    status, headers, cuerpo = await _core(request)
    return Response(content=cuerpo, status_code=status, headers=headers)
