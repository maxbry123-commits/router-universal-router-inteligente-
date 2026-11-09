from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from integration.huggingface.huggingface_openai_chat import (  # noqa: E402
    allowed_model_ids,
    chat_completion,
    provider_live_model_ids,
)


def test_allowed_model_ids_does_not_raise_and_matches_runtime_verified() -> None:
    # Regression for GAP_ADAPTER_REGISTRY_SCHEMA: registry()["models"] never
    # existed in V12/V13 and raised KeyError on every call.
    ids = allowed_model_ids()
    assert ids == {
        "Qwen/Qwen3-0.6B",
        "openai-community/gpt2",
        "Qwen/Qwen3-8B",
    }


def test_provider_live_ids_are_separate_from_allowed_ids() -> None:
    live = provider_live_model_ids()
    allowed = allowed_model_ids()
    assert len(live) == 20
    assert "openai/gpt-oss-120b" in live
    # REMOTE20 stays PROVIDER_LIVE_VERIFIED only; GAP_AUTH_REMOTE_INFERENCE
    # is still open (0/20 authenticated PASS per Job 6aad981352d0dbd7f1d6b827),
    # so none of it may leak into the chat-completion allow-list.
    assert live.isdisjoint(allowed)


def test_chat_completion_rejects_remote20_model_not_yet_authenticated() -> None:
    with pytest.raises(ValueError, match="MODEL_NOT_IN_CERTIFIED_REGISTRY"):
        chat_completion(
            model_id="openai/gpt-oss-120b",
            messages=[{"role": "user", "content": "ping"}],
        )


def test_chat_completion_rejects_unknown_model_id() -> None:
    with pytest.raises(ValueError, match="MODEL_NOT_IN_CERTIFIED_REGISTRY"):
        chat_completion(
            model_id="not/a-real-model",
            messages=[{"role": "user", "content": "ping"}],
        )
