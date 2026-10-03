"""OpenAI-compatible provider clients for the chat MVP (stdlib only).

Keys come from the unlocked Secret Bank (vault_hook), the server environment or, per request, a BYOK header.
They are never logged, stored or echoed back; error messages carry only the HTTP status and a short provider message.
NVIDIA is listed FIRST (principal provider) and has a pool of keys with failover (see core.py).
2026-09-27 (Director): Groq con pool GROQ_API_KEY_1..7 (la 1 es inválida hoy; se salta sola). Cerebras ELIMINADO (Director 2026-09-29).
2026-09-29 (Director, cadena de chat): ATTEMPT_DEADLINE limita el tiempo de UNA opción de la cadena para que un modelo lento no bloquee
  el chat (ver resilience.run_policy). Sin deadline (None) el tiempo por llamada sigue siendo 90 s como antes.
"""
from __future__ import annotations

import contextvars
import hashlib
import json
import os
import time
import urllib.error
import urllib.request
from typing import Any, Callable

from . import vault_hook

PROVIDERS: dict[str, dict[str, Any]] = {
    "nvidia": {"label": "NVIDIA NIM (principal)", "base": "https://integrate.api.nvidia.com/v1",
               "env": ("NVIDIA_API_KEY", "NVIDIA_API_KEY_1", "NVIDIA_API_KEY_2", "NVIDIA_API_KEY_3", "NVIDIA_API_KEY_4", "NVIDIA_API_KEY_5")},
    "hf": {"label": "Hugging Face Router", "base": "https://router.huggingface.co/v1", "env": ("HF_TOKEN", "HF_TOKEN_1")},
    "groq": {"label": "Groq", "base": "https://api.groq.com/openai/v1",
             "env": ("GROQ_API_KEY", "GROQ_API_KEY_1", "GROQ_API_KEY_2", "GROQ_API_KEY_3", "GROQ_API_KEY_4",
                     "GROQ_API_KEY_5", "GROQ_API_KEY_6", "GROQ_API_KEY_7")},
    "openai": {"label": "OpenAI (SDK, 14 claves rotativas)", "base": "https://api.openai.com/v1",
               "env": ("OPENAI_API_KEY", "OPENAI_API_KEY_1", "OPENAI_API_KEY_2", "OPENAI_API_KEY_3", "OPENAI_API_KEY_4", "OPENAI_API_KEY_5", "OPENAI_API_KEY_6", "OPENAI_API_KEY_7", "OPENAI_API_KEY_8", "OPENAI_API_KEY_9", "OPENAI_API_KEY_10", "OPENAI_API_KEY_11", "OPENAI_API_KEY_12", "OPENAI_API_KEY_13", "OPENAI_API_KEY_14")},
    "deepseek": {"label": "DeepSeek API directa (caché de contexto nativa)", "base": "https://api.deepseek.com/v1", "env": ("DEEPSEEK_API_KEY",)},
    "moonshot": {"label": "Moonshot / Kimi API directa (caché de contexto nativa)", "base": "https://api.moonshot.ai/v1", "env": ("MOONSHOT_API_KEY",)},
    "minimax": {"label": "MiniMax API directa", "base": "https://api.minimax.io/v1", "env": ("MINIMAX_API_KEY",)},
    "local": {"label": "API local (llama.cpp / Ollama / vLLM)", "base": None, "env": ("RIU_LOCAL_API_KEY",)},
}
MODELS_TTL = 300.0
_models_cache: dict[tuple[str, str], tuple[float, list[str]]] = {}
CHAT_TIMEOUT = 90.0
# Absolute time.monotonic() deadline for the chain option being tried (set by resilience.run_policy; travels through
# asyncio.run / asyncio.to_thread because both copy the context). None = no deadline.
ATTEMPT_DEADLINE: contextvars.ContextVar[float | None] = contextvars.ContextVar("riu_attempt_deadline", default=None)
# OpenAI tool calling (Harness/agents through /v1/router): extra request fields (tools, tool_choice, ...) for the current call.
# Set by openai_route; travels through asyncio.run / to_thread like ATTEMPT_DEADLINE. None = plain chat (old behaviour).
EXTRA_PAYLOAD: contextvars.ContextVar[dict[str, Any] | None] = contextvars.ContextVar("riu_extra_payload", default=None)


OPENAI_NO_TEMPERATURE = ("gpt-5", "gpt-6", "o1", "o3", "o4")  # solo temperatura por defecto


def chat_timeout() -> float:
    """Seconds one chat HTTP call may take: CHAT_TIMEOUT, cut to what is left of the current chain-option deadline (min 1 s)."""
    deadline = ATTEMPT_DEADLINE.get()
    if deadline is None:
        return CHAT_TIMEOUT
    return max(1.0, min(CHAT_TIMEOUT, deadline - time.monotonic()))


class ProviderError(RuntimeError):
    def __init__(self, status: int | str, message: str) -> None:
        super().__init__(f"PROVIDER_ERROR:{status}:{message}")
        self.status = status


def registry() -> dict[str, dict[str, Any]]:
    """Built-in PROVIDERS + every OpenAI-compatible SDK declared in the Secret Bank providers file (vault_bridge providers.json /
    RIU_VAULT_PROVIDERS_FILE) with a base_url: a new API added to the bank works without touching this code (Director 2026-10-03)."""
    merged = dict(PROVIDERS)
    try:
        from .vault_bridge import load_providers
        for name, entry in load_providers().items():
            if name not in merged and entry.get("base_url"):
                merged[name] = {"label": name + " (banco)", "base": entry["base_url"].rstrip("/"),
                                "env": tuple(e for e in (entry.get("env"),) if e)}
    except Exception:  # noqa: BLE001 - a broken providers file never breaks the built-in providers
        pass
    return merged


def base_url(provider: str) -> str | None:
    if provider == "local":
        return (os.getenv("RIU_LOCAL_BASE_URL") or "").rstrip("/") or None
    entry = registry().get(provider)
    return entry["base"] if entry else None


def env_keys(provider: str) -> list[str]:
    """All distinct non-empty keys of the provider (pool order): unlocked Secret Bank first, then the server environment."""
    seen: list[str] = []
    entry = registry().get(provider) or {"env": ()}
    candidates = [*vault_hook.provider_keys(provider), *(os.getenv(name) for name in entry["env"])]
    for value in candidates:
        if value and value not in seen:
            seen.append(value)
    return seen


def resolve_key(provider: str, byok: str | None = None) -> str | None:
    if byok:
        return byok
    keys = env_keys(provider)
    return keys[0] if keys else None


def configured(provider: str) -> bool:
    if provider == "local":
        return base_url("local") is not None
    return resolve_key(provider) is not None


def _http(method: str, url: str, key: str | None, body: dict[str, Any] | None, timeout: float) -> dict[str, Any]:
    headers = {"Content-Type": "application/json", "Accept": "application/json", "User-Agent": "riu-chat-mvp"}
    if key:
        headers["Authorization"] = "Bearer " + key
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310 https URLs from the fixed registry
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = " ".join(exc.read().decode("utf-8", errors="replace").split())  # compact: the error code fits in the cut
        if key:
            detail = detail.replace(key, "***")  # mask BEFORE cutting: a cut through the key would leave a prefix of it
        raise ProviderError(exc.code, detail[:160]) from exc
    except Exception as exc:  # noqa: BLE001
        raise ProviderError(type(exc).__name__, "request failed") from exc


def list_models(provider: str, key: str | None, *, fetch: Callable[..., dict[str, Any]] | None = None,
                now: Callable[[], float] = time.monotonic) -> list[str]:
    base = base_url(provider)
    if not base:
        raise ProviderError("NO_BASE_URL", "RIU_LOCAL_BASE_URL not set" if provider == "local" else "unknown provider")
    ck = (provider, hashlib.sha256((key or "").encode()).hexdigest()[:8])
    hit = _models_cache.get(ck)
    if hit and now() - hit[0] < MODELS_TTL:
        return list(hit[1])
    body = (fetch or (lambda url, k: _http("GET", url, k, None, 20)))(base + "/models", key)
    ids = sorted({d["id"] for d in body.get("data", []) if isinstance(d, dict) and isinstance(d.get("id"), str)})
    _models_cache[ck] = (now(), ids)
    return ids


def chat(provider: str, key: str | None, model: str, messages: list[dict[str, str]], max_tokens: int,
         *, temperature: float | None = None, post: Callable[..., dict[str, Any]] | None = None) -> dict[str, Any]:
    base = base_url(provider)
    if not base:
        raise ProviderError("NO_BASE_URL", "provider has no base URL")
    # OpenAI: modelos gpt nuevos piden max_completion_tokens (no max_tokens) y los de razonamiento no admiten temperature (confirmado: 400 con 0.7).
    openai = provider == "openai"
    payload: dict[str, Any] = {"model": model, "messages": messages,
                               ("max_completion_tokens" if openai else "max_tokens"): max_tokens}
    if temperature is not None and not (openai and model.startswith(OPENAI_NO_TEMPERATURE)):
        payload["temperature"] = temperature
    extra = EXTRA_PAYLOAD.get()
    if extra:
        payload.update({k: v for k, v in extra.items() if k not in payload})
    data = (post or (lambda url, k, b: _http("POST", url, k, b, chat_timeout())))(base + "/chat/completions", key, payload)
    try:
        choice = data["choices"][0]
        content = choice["message"].get("content") or ""
    except (KeyError, IndexError, TypeError) as exc:
        raise ProviderError("BAD_RESPONSE", "no choices in provider response") from exc
    message: dict[str, Any] = {"role": "assistant", "content": content}
    if choice["message"].get("tool_calls"):
        message["tool_calls"] = choice["message"]["tool_calls"]
    elif not content.strip() and choice.get("finish_reason") != "length":
        # reasoning models (e.g. Kimi K3) sometimes spend the turn on reasoning only: an empty answer is a failed option,
        # so the chain moves to the next model instead of returning nothing to the client
        raise ProviderError("EMPTY_CONTENT", "model returned no content")
    return {"model": model, "message": message,
            "finish_reason": choice.get("finish_reason"), "usage": data.get("usage")}
