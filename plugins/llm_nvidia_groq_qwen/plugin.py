"""llm_nvidia_groq_qwen: selectores NVIDIA, Groq y Qwen para el Router.

Mismo metodo que deepseek_harness: wrapper removible, sin dependencia dura, sin URL o llave -> degraded.
Acciones: status, invoke (HTTP OpenAI-compatible), llm (puerta llm_call de puente_chat, como deepseek_harness).

Env (solo nombres; los valores viven en el entorno del operador, nunca en el repo):
  RIU_NVIDIA_API_KEY, RIU_NVIDIA_BASE_URL (def https://integrate.api.nvidia.com/v1)
  RIU_GROQ_API_KEY,   RIU_GROQ_BASE_URL   (def https://api.groq.com/openai/v1)
  RIU_QWEN_URL (base del Qwen local, debe incluir /v1; sin defecto), RIU_QWEN_API_KEY (opcional)
  RIU_LLM_TIMEOUT (segundos, def 60)

Pendiente (p3 / A-4): catalogo de modelos NVIDIA y modelos locales Qwen. Hasta entonces payload.model es obligatorio.
Pendiente (p2 / A-3): la ruta llm aun no esta verificada contra puente_chat.llm_call.
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any

_PROVEEDORES: dict[str, dict[str, str]] = {
    "nvidia": {"key_env": "RIU_NVIDIA_API_KEY", "base_env": "RIU_NVIDIA_BASE_URL", "base_def": "https://integrate.api.nvidia.com/v1", "key_req": "1"},
    "groq": {"key_env": "RIU_GROQ_API_KEY", "base_env": "RIU_GROQ_BASE_URL", "base_def": "https://api.groq.com/openai/v1", "key_req": "1"},
    "qwen": {"key_env": "RIU_QWEN_API_KEY", "base_env": "RIU_QWEN_URL", "base_def": "", "key_req": ""},
}
_PATH = "/chat/completions"


def _degraded(reason: str) -> dict[str, Any]:
    return {"status": "degraded", "reason": reason}


def _timeout() -> float:
    try:
        return float(os.getenv("RIU_LLM_TIMEOUT") or 60)
    except ValueError:
        return 60.0


def _base(prov: str) -> str:
    spec = _PROVEEDORES[prov]
    return (os.getenv(spec["base_env"]) or spec["base_def"]).strip().rstrip("/")


def _key(prov: str) -> str:
    return (os.getenv(_PROVEEDORES[prov]["key_env"]) or "").strip()


def _status() -> dict[str, Any]:
    info = {}
    for prov in _PROVEEDORES:
        info[prov] = {"base_configurada": bool(_base(prov)), "llave_configurada": bool(_key(prov))}
    if not any(v["base_configurada"] for v in info.values()):
        return _degraded("sin bases configuradas: NVIDIA, Groq y Qwen no configurados")
    return {"status": "ok", "configured": True, "proveedores": info}


def _invoke(payload: dict[str, Any]) -> dict[str, Any]:
    prov = str(payload.get("proveedor") or "").strip().lower()
    if prov not in _PROVEEDORES:
        return _degraded("proveedor desconocido (nvidia|groq|qwen)")
    spec = _PROVEEDORES[prov]
    base = _base(prov)
    if not base:
        return _degraded("sin " + spec["base_env"] + ": " + prov + " no configurado")
    key = _key(prov)
    if spec["key_req"] and not key:
        return _degraded("sin " + spec["key_env"] + ": llave no configurada")
    messages = payload.get("messages")
    if not isinstance(messages, list) or not messages:
        return _degraded("payload sin messages")
    model = payload.get("model")
    if not model:
        return _degraded("payload sin model (catalogo pendiente de p3 / A-4)")
    body: dict[str, Any] = {"model": model, "messages": messages, "stream": False}
    if payload.get("max_tokens"):
        body["max_tokens"] = payload["max_tokens"]
    headers = {"Content-Type": "application/json"}
    if key:
        headers["Authorization"] = "Bearer " + key
    req = urllib.request.Request(base + _PATH, data=json.dumps(body).encode(), headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=_timeout()) as resp:  # noqa: S310 (URL fijada por el operador via env)
            raw = resp.read(1_000_000).decode("utf-8", "replace")
    except urllib.error.HTTPError as exc:
        return _degraded(prov + " respondio HTTP " + str(exc.code))
    except Exception as exc:
        return _degraded(prov + " inalcanzable: " + type(exc).__name__)
    try:
        data: Any = json.loads(raw)
        content = data["choices"][0]["message"]["content"]
    except (ValueError, KeyError, IndexError, TypeError):
        return _degraded("respuesta sin choices[0].message.content")
    return {"status": "ok", "proveedor": prov, "model": model, "content": content}


def _llm(payload: dict[str, Any]) -> dict[str, Any]:
    # Misma puerta que deepseek_harness: nunca llama directo a un proveedor desde aqui.
    try:
        from plugins.puente_chat.plugin import llm_call
        p2 = dict(payload)
        p2.setdefault("caller_id", "llm_nvidia_groq_qwen")
        p2.setdefault("plugin_id", "llm_nvidia_groq_qwen")
        return llm_call(p2)
    except Exception as exc:  # noqa: BLE001
        return _degraded("llm_call: " + type(exc).__name__)


def handle(action: str, payload: dict[str, Any] | None) -> dict[str, Any]:
    payload = payload or {}
    if action == "status":
        return _status()
    if action == "invoke":
        return _invoke(payload)
    if action == "llm":
        return _llm(payload)
    return _degraded("accion desconocida")
