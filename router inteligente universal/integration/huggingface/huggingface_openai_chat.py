"""Hugging Face OpenAI-compatible chat adapter for Router Inteligente Universal.

Fail-closed adapter: model IDs must be present in the certified registry and
credentials are read only from HF_TOKEN at runtime.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from huggingface_hub import InferenceClient

_REGISTRY = Path(__file__).with_name("model_registry.json")


def _registry() -> dict[str, Any]:
    return json.loads(_REGISTRY.read_text(encoding="utf-8"))


def allowed_model_ids() -> set[str]:
    return {m["model_id"] for m in _registry()["models"]}


def chat_completion(*, model_id: str, messages: list[dict[str, str]], max_tokens: int = 256) -> dict[str, Any]:
    if model_id not in allowed_model_ids():
        raise ValueError("MODEL_NOT_IN_CERTIFIED_REGISTRY")
    token = os.getenv("HF_TOKEN")
    if not token:
        raise RuntimeError("HF_TOKEN_REQUIRED")
    client = InferenceClient(token=token)
    out = client.chat_completion(model=model_id, messages=messages, max_tokens=max_tokens)
    choice = out.choices[0]
    return {
        "model": model_id,
        "message": {"role": choice.message.role, "content": choice.message.content},
        "finish_reason": choice.finish_reason,
    }
