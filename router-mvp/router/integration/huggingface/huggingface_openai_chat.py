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
    """Model IDs cleared for chat_completion().

    Only `runtime_inference_verified_model_ids` qualifies: each of those IDs
    has real REMOTE_INFERENCE_SMOKE evidence inside an HF Job. The REMOTE20
    set (see `provider_live_model_ids`) is PROVIDER_LIVE_VERIFIED only and
    stays excluded here until its GAP_AUTH_REMOTE_INFERENCE gap closes with
    real authenticated evidence -- see Handoff RIU-0094 / CHECKPOINT
    RIU-0097. Never fabricate a "models" key: earlier versions of this
    function read registry()["models"], a key that stopped existing in V12
    and caused every call to raise KeyError (GAP_ADAPTER_REGISTRY_SCHEMA).
    """
    return set(_registry().get("runtime_inference_verified_model_ids", []))


def provider_live_model_ids() -> set[str]:
    """REMOTE20 model IDs with >=1 live Inference Provider (catalog-level).

    PROVIDER_LIVE_VERIFIED != REMOTE_INFERENCE_AUTHENTICATED_PASS. Do not
    pass these into chat_completion() until their individual
    REMOTE_INFERENCE_SMOKE + FAILURE_FALLBACK_TEST gates close with fresh
    evidence and they are moved into
    `runtime_inference_verified_model_ids` by an explicit, evidenced commit.
    """
    remote20 = _registry().get("remote20_provider_live_verified", {})
    return {m["model_id"] for m in remote20.get("models", [])}


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
