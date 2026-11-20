"""llm_local_swe_code: conecta los LLM locales (Space HF `llm system HF`, llama-server) a SWE CODE.

Mismo metodo que deepseek_harness: wrapper removible, sin dependencia dura, sin URL -> degraded.
Acciones: status, invoke.
Env: RIU_LLM_LOCAL_SWE_URL (base del Space, p. ej. https://<space>.hf.space),
     RIU_LLM_LOCAL_SWE_API_KEY (ROUTER_API_KEY del Space; se envia en cabecera X-API-Key),
     RIU_LLM_LOCAL_SWE_TIMEOUT (segundos, def 120).
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any

_PATH = "/v1/chat/completions"
_NO_URL = "sin RIU_LLM_LOCAL_SWE_URL: LLM local SWE CODE no configurado"


def _url() -> str:
    return (os.getenv("RIU_LLM_LOCAL_SWE_URL") or "").strip().rstrip("/")


def _timeout() -> float:
    try:
        return float(os.getenv("RIU_LLM_LOCAL_SWE_TIMEOUT") or 120)
    except ValueError:
        return 120.0


def _degraded(reason: str) -> dict[str, Any]:
    return {"status": "degraded", "reason": reason}


def handle(action: str, payload: dict[str, Any] | None) -> dict[str, Any]:
    payload = payload or {}
    base = _url()
    if action == "status":
        if not base:
            return _degraded(_NO_URL)
        return {"status": "ok", "configured": True, "url": base.split("?")[0]}
    if action != "invoke":
        return _degraded("accion desconocida")
    if not base:
        return _degraded(_NO_URL)
    messages = payload.get("messages")
    if not isinstance(messages, list) or not messages:
        return _degraded("payload sin messages")
    body: dict[str, Any] = {"messages": messages, "stream": False}
    if payload.get("model"):
        body["model"] = payload["model"]
    if payload.get("max_tokens"):
        body["max_tokens"] = payload["max_tokens"]
    headers = {"Content-Type": "application/json"}
    key = os.getenv("RIU_LLM_LOCAL_SWE_API_KEY")
    if key:
        headers["X-API-Key"] = key
    req = urllib.request.Request(base + _PATH, data=json.dumps(body).encode(), headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=_timeout()) as resp:  # noqa: S310 (URL fijada por el operador via env)
            raw = resp.read(1_000_000).decode("utf-8", "replace")
    except urllib.error.HTTPError as exc:
        return _degraded(f"LLM local respondio HTTP {exc.code}")
    except Exception as exc:
        return _degraded(f"LLM local inalcanzable: {type(exc).__name__}")
    try:
        data: Any = json.loads(raw)
        content = data["choices"][0]["message"]["content"]
    except (ValueError, KeyError, IndexError, TypeError):
        return _degraded("respuesta sin choices[0].message.content")
    return {"status": "ok", "content": content}
