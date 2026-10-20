"""Chat MVP executor: certified path unchanged; live-provider attempts only when enabled."""
from __future__ import annotations

import os
from typing import Any, Callable

from . import huggingface_openai_chat as adapter
from .chat_catalog import cached_discovery, selectable_live_ids


def _call_inference(*, token: str, model_id: str, messages: list[dict[str, str]], max_tokens: int) -> dict[str, Any]:
    from huggingface_hub import InferenceClient

    out = InferenceClient(token=token, timeout=60).chat_completion(model=model_id, messages=messages, max_tokens=max_tokens)
    choice = out.choices[0]
    return {
        "model": model_id,
        "message": {"role": choice.message.role, "content": choice.message.content},
        "finish_reason": choice.finish_reason,
    }


def make_executor(*, allow_provider_live: bool, discover: Callable[[], list[str]] = cached_discovery) -> Callable[..., dict[str, Any]]:
    """Return an executor with the same signature as adapter.chat_completion."""

    def executor(*, model_id: str, messages: list[dict[str, str]], max_tokens: int = 256) -> dict[str, Any]:
        if model_id in adapter.allowed_model_ids():
            out = adapter.chat_completion(model_id=model_id, messages=messages, max_tokens=max_tokens)
            return {**out, "certified": True}
        if not allow_provider_live:
            raise ValueError("MODEL_NOT_IN_CERTIFIED_REGISTRY")
        if model_id not in selectable_live_ids(discovered=discover()):
            raise ValueError("MODEL_NOT_SELECTABLE")
        token = os.getenv("HF_TOKEN")
        if not token:
            raise RuntimeError("HF_TOKEN_REQUIRED")
        out = _call_inference(token=token, model_id=model_id, messages=messages, max_tokens=max_tokens)
        return {**out, "certified": False}

    return executor
