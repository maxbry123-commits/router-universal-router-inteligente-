"""OpenAI-compatible provider clients for the chat MVP (stdlib only).

Keys come from the server environment or, per request, from a BYOK header. They are never logged,
stored or echoed back; error messages carry only the HTTP status and a short provider message.
"""
from __future__ import annotations

import hashlib
import json
import os
import time
import urllib.error
import urllib.request
from typing import Any, Callable

PROVIDERS: dict[str, dict[str, Any]] = {
    "hf": {"label": "Hugging Face Router", "base": "https://router.huggingface.co/v1", "env": ("HF_TOKEN", "HF_TOKEN_1")},
    "cerebras": {"label": "Cerebras", "base": "https://api.cerebras.ai/v1", "env": ("CEREBRAS_API_KEY", "CEREBRAS_API_KEY_1")},
    "nvidia": {"label": "NVIDIA NIM", "base": "https://integrate.api.nvidia.com/v1", "env": ("NVIDIA_API_KEY", "NVIDIA_API_KEY_1")},
    "groq": {"label": "Groq", "base": "https://api.groq.com/openai/v1", "env": ("GROQ_API_KEY", "GROQ_API_KEY_1")},
    "local": {"label": "API local (llama.cpp / Ollama / vLLM)", "base": None, "env": ("RIU_LOCAL_API_KEY",)},
}
MODELS_TTL = 300.0
_models_cache: dict[tuple[str, str], tuple[float, list[str]]] = {}


class ProviderError(RuntimeError):
    def __init__(self, status: int | str, message: str) -> None:
        super().__init__(f"PROVIDER_ERROR:{status}:{message}")
        self.status = status


def base_url(provider: str) -> str | None:
    if provider == "local":
        return (os.getenv("RIU_LOCAL_BASE_URL") or "").rstrip("/") or None
    return PROVIDERS[provider]["base"]


def resolve_key(provider: str, byok: str | None = None) -> str | None:
    if byok:
        return byok
    for name in PROVIDERS[provider]["env"]:
        value = os.getenv(name)
        if value:
            return value
    return None


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
        detail = exc.read().decode("utf-8", errors="replace")[:160].replace("\n", " ")
        raise ProviderError(exc.code, detail.replace(key, "***") if key else detail) from exc
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
    payload: dict[str, Any] = {"model": model, "messages": messages, "max_tokens": max_tokens}
    if temperature is not None:
        payload["temperature"] = temperature
    data = (post or (lambda url, k, b: _http("POST", url, k, b, 90)))(base + "/chat/completions", key, payload)
    try:
        choice = data["choices"][0]
        content = choice["message"].get("content") or ""
    except (KeyError, IndexError, TypeError) as exc:
        raise ProviderError("BAD_RESPONSE", "no choices in provider response") from exc
    return {"model": model, "message": {"role": "assistant", "content": content},
            "finish_reason": choice.get("finish_reason"), "usage": data.get("usage")}
