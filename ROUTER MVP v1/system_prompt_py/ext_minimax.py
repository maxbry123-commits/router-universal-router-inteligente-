"""ext_minimax.py — proveedor MiniMax (opcional, aditivo) del router YAIWES.

Este modulo NO toca el nucleo del proxy: se registra con `register_minimax(app)`
dentro de un try/except en `openai_compatible_proxy.py`. Si el modulo falta o
falla al importar, el router sigue arrancando igual (solo se pierde la ruta
/v1/minimax/*).

Que resuelve:
  - MiniMax tiene DOS APIs historicas:
      * LEGADA: https://api.minimax.chat/v1/text/chatcompletion_v2?GroupId=...
        (modelos antiguos tipo `abab6.5s-chat`, payload con `sender_type`/`text`)
      * ACTUAL: https://api.minimax.io/v1  (OpenAI-compatible, /chat/completions)
    Este modulo detecta cual usar: si llega `GroupId` o el modelo empieza por
    `abab`/`abab6` usa la legada; si no, la actual.
  - El grupo (`MINIMAX_GROUP_ID`) solo hace falta para la API legada.
  - Sin claves NO se rompe nada: responde 503 con un mensaje claro.

Variables de entorno:
  MINIMAX_API_KEY   clave de MiniMax (o MINIMAX_KEYS con varias separadas por coma)
  MINIMAX_GROUP_ID  GroupId (solo API legada)
  MINIMAX_MODEL     modelo por defecto (por defecto `MiniMax-M2`)
  MINIMAX_BASE_URL  base URL (si no, se elige sola: api.minimax.io | api.minimax.chat)
  MINIMAX_TIMEOUT_S timeout por peticion (por defecto 60)
"""
import json
import os
import time
import urllib.error
import urllib.request

from fastapi import Request
from fastapi.responses import JSONResponse

TIMEOUT_S = float(os.environ.get("MINIMAX_TIMEOUT_S", "60"))
MODEL_DEFAULT = os.environ.get("MINIMAX_MODEL", "MiniMax-M2")
LEGACY_MODELOS = ("abab", "abab6", "abab5")


def _claves():
    crudo = os.environ.get("MINIMAX_KEYS", "") or os.environ.get("MINIMAX_API_KEY", "")
    return [k.strip() for k in crudo.split(",") if k.strip()]


def _group_id():
    return (os.environ.get("MINIMAX_GROUP_ID") or "").strip()


def _es_legado(model):
    m = (model or "").lower()
    return any(m.startswith(p) or p in m for p in LEGACY_MODELOS)


def _base_legada():
    base = os.environ.get("MINIMAX_BASE_URL_LEGACY", "https://api.minimax.chat/v1/text/chatcompletion_v2")
    gid = _group_id()
    if gid and "?" not in base:
        base = f"{base}?GroupId={gid}"
    return base


def _base_actual():
    return os.environ.get("MINIMAX_BASE_URL", "https://api.minimax.io/v1").rstrip("/")


def _post(url, payload, key, timeout):
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {key}"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        crudo = resp.read().decode("utf-8", "replace")
    try:
        return json.loads(crudo)
    except Exception:
        return {"raw": crudo[:4000]}


def _normaliza_legado(data):
    """La API legada devuelve {reply, total_tokens, base_resp}."""
    if data.get("base_resp") and data["base_resp"].get("status_code", 0) not in (0, None):
        raise RuntimeError(data["base_resp"].get("status_msg") or "minimax: error interno")
    texto = data.get("reply")
    if texto is None:
        raise RuntimeError("minimax: respuesta sin campo 'reply'")
    return {
        "id": "chatcmpl-minimax",
        "object": "chat.completion",
        "model": data.get("model", MODEL_DEFAULT),
        "choices": [{
            "index": 0,
            "message": {"role": "assistant", "content": texto},
            "finish_reason": "stop",
        }],
        "usage": {
            "prompt_tokens": data.get("total_tokens", 0),
            "completion_tokens": data.get("total_tokens", 0),
            "total_tokens": data.get("total_tokens", 0),
        },
    }


def _a_openai(mensajes, modelo, max_tokens, temperatura):
    return {
        "id": "chatcmpl-minimax",
        "object": "chat.completion",
        "model": modelo,
        "choices": [{
            "index": 0,
            "message": {"role": "assistant", "content": ""},
            "finish_reason": "stop",
        }],
        "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
        "_minimax_request": {"messages": mensajes, "max_tokens": max_tokens,
                             "temperature": temperatura},
    }


def registrar(app):
    """Registra las rutas MiniMax en la app del router."""

    @app.get("/v1/minimax/health")
    def minimax_health():
        claves = _claves()
        return {
            "id": "minimax",
            "configured": bool(claves),
            "claves": len(claves),
            "group_id": bool(_group_id()),
            "modelo_por_defecto": MODEL_DEFAULT,
            "api": "legada" if _es_legado(MODEL_DEFAULT) else "actual",
            "base": _base_legada() if _es_legado(MODEL_DEFAULT) else _base_actual(),
        }

    @app.post("/v1/minimax/chat")
    async def minimax_chat(request: Request):
        claves = _claves()
        if not claves:
            return JSONResponse(
                status_code=503,
                content={"error": {
                    "code": "NO_PROVIDER_KEYS",
                    "message": "configura MINIMAX_API_KEY (o MINIMAX_KEYS) en el Space",
                }},
            )
        try:
            body = json.loads((await request.body()) or b"{}")
        except Exception:
            body = {}
        mensajes = body.get("messages") or []
        if not mensajes:
            return JSONResponse(
                status_code=400,
                content={"error": {"code": "EMPTY_MESSAGES", "message": "messages vacio"}},
            )
        modelo = body.get("model") or MODEL_DEFAULT
        max_tokens = int(body.get("max_tokens") or 1024)
        temperatura = body.get("temperature", 0.7)
        grupo = _group_id()
        if _es_legado(modelo) or (grupo and not modelo.startswith("MiniMax")):
            url = _base_legada()
            payload = {
                "model": modelo,
                "messages": [{"sender_type": "USER", "text": _texto(m)} for m in mensajes],
                "tokens_to_generate": max_tokens,
                "temperature": temperatura,
                "top_p": body.get("top_p", 0.95),
                "reply_constraints": {"sender_type": "BOT"},
            }
        else:
            url = _base_actual() + "/chat/completions"
            payload = {
                "model": modelo,
                "messages": mensajes,
                "max_tokens": max_tokens,
                "temperature": temperatura,
                "stream": False,
            }
        ultimo = None
        for clave in claves:
            try:
                data = _post(url, payload, clave, TIMEOUT_S)
                if _es_legado(modelo) or (grupo and not modelo.startswith("MiniMax")):
                    return _normaliza_legado(data)
                return data
            except urllib.error.HTTPError as e:
                ultimo = {"http": e.code, "detalle": e.read().decode("utf-8", "replace")[:300]}
            except Exception as e:
                ultimo = {"http": 0, "detalle": repr(e)[:300]}
            time.sleep(0.4)
        return JSONResponse(
            status_code=502,
            content={"error": {"code": "MINIMAX_DOWN", "detalle": ultimo}},
        )

    return app


# Alias compatible con el resto de modulos del router.
register_minimax = registrar


def _texto(m):
    if isinstance(m, dict):
        if m.get("text"):
            return m["text"]
        if m.get("content"):
            c = m["content"]
            return c if isinstance(c, str) else json.dumps(c, ensure_ascii=False)
    return str(m)
