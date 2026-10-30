"""deepseek_harness: wrapper removible de la regla Fables s8. Sin dependencia dura: sin URL -> degraded.

Acciones: status, invoke. Env: RIU_DEEPSEEK_HARNESS_URL (base), RIU_DEEPSEEK_HARNESS_API_KEY (opcional), RIU_DEEPSEEK_HARNESS_PATH (def /invoke).
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any


def _url() -> str:
    return (os.getenv("RIU_DEEPSEEK_HARNESS_URL") or "").strip().rstrip("/")


def _degraded(reason: str) -> dict[str, Any]:
    return {"status": "degraded", "reason": reason}


# Manual canonico (Riu + OpenClaw): chat-router/SWE CODE free/INSTRUCCIONES.md -> system.
_MANUAL = os.path.join(os.path.dirname(__file__), "..", "..", "chat-router", "SWE CODE free", "INSTRUCCIONES.md")


def _with_manual(payload: dict[str, Any]) -> dict[str, Any]:
    path = os.getenv("RIU_INSTRUCCIONES_PATH") or _MANUAL
    try:
        with open(path, encoding="utf-8") as fh:
            manual = fh.read()
    except OSError:
        return payload
    p = dict(payload)
    p.setdefault("system", manual)
    msgs = p.get("messages")
    if isinstance(msgs, list) and not any(isinstance(m, dict) and m.get("role") == "system" for m in msgs):
        p["messages"] = [{"role": "system", "content": manual}] + msgs
    return p


def handle(action: str, payload: dict[str, Any] | None) -> dict[str, Any]:
    payload = _with_manual(payload or {})
    base = _url()
    if action == "status":
        if not base:
            return _degraded("sin RIU_DEEPSEEK_HARNESS_URL: harness no configurado")
        return {"status": "ok", "configured": True, "url": base.split("?")[0]}
    if action == "llm":
        # DeepSeek Harness -> HTTP -> /plugins/fichas_qwen/call/llm -> Ficha 4 -> modelo.
        # Reutiliza la misma puerta LLM que Graphiti (llm_call); nunca llama directo a un proveedor.
        try:
            from plugins.puente_chat.plugin import llm_call
            p2 = dict(payload)
            p2.setdefault("caller_id", "deepseek_harness")
            p2.setdefault("plugin_id", "deepseek_harness")
            return llm_call(p2)
        except Exception as exc:  # noqa: BLE001
            return {"status": "degraded", "reason": "llm_call: " + type(exc).__name__}
    if action != "invoke":
        return _degraded("accion desconocida")
    if not base:
        return _degraded("sin RIU_DEEPSEEK_HARNESS_URL: harness no configurado")
    path = os.getenv("RIU_DEEPSEEK_HARNESS_PATH") or "/invoke"
    headers = {"Content-Type": "application/json"}
    key = os.getenv("RIU_DEEPSEEK_HARNESS_API_KEY") or os.getenv("RIU_API_KEY")
    if key:
        headers["X-API-Key"] = key
    req = urllib.request.Request(base + path, data=json.dumps(payload).encode(), headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=None) as resp:  # sin tope de tiempo por orden del Director  # noqa: S310 (URL fijada por el operador via env)
            raw = resp.read(1_000_000).decode("utf-8", "replace")
            try:
                body: Any = json.loads(raw)
            except ValueError:
                body = raw
            return {"status": "ok", "http_status": resp.status, "response": body}
    except urllib.error.HTTPError as exc:
        return _degraded(f"harness respondio HTTP {exc.code}")
    except Exception as exc:
        return _degraded(f"harness inalcanzable: {type(exc).__name__}")
