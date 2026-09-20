from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

pytest.importorskip("huggingface_hub")

from integration.chat_mvp import core  # noqa: E402
from integration.chat_mvp import providers as prov  # noqa: E402

NAMES = ("NVIDIA_API_KEY", "NVIDIA_API_KEY_1", "NVIDIA_API_KEY_2", "NVIDIA_API_KEY_3", "NVIDIA_API_KEY_4", "NVIDIA_API_KEY_5")


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch):
    for n in NAMES:
        monkeypatch.delenv(n, raising=False)


def test_nvidia_is_listed_first_and_pool_dedupes_env_keys(monkeypatch):
    assert list(prov.PROVIDERS)[0] == "nvidia"
    monkeypatch.setenv("NVIDIA_API_KEY_1", "a")
    monkeypatch.setenv("NVIDIA_API_KEY_2", "b")
    monkeypatch.setenv("NVIDIA_API_KEY_3", "a")
    assert prov.env_keys("nvidia") == ["a", "b"] and prov.resolve_key("nvidia") == "a"
    assert core.key_pool("nvidia", "a") == ["a", "b"]
    assert core.key_pool("nvidia", "byok-x") == ["byok-x"]  # a BYOK key never expands to the pool
    assert core.key_pool("nvidia", None) == [None]


def test_slow_or_failing_key_falls_over_to_the_next_one(monkeypatch):
    monkeypatch.setenv("NVIDIA_API_KEY_1", "a")
    monkeypatch.setenv("NVIDIA_API_KEY_2", "b")
    tried = []

    def fake_chat(provider, key, model, messages, max_tokens, *, temperature=None, post=None):
        tried.append(key)
        if key == "a":
            raise prov.ProviderError("TimeoutError", "request failed")
        return {"model": model, "message": {"role": "assistant", "content": "ok"}, "finish_reason": "stop", "usage": None}

    monkeypatch.setattr(prov, "chat", fake_chat)
    out = core.call_via_router("nvidia", "a", "m", [{"role": "user", "content": "x"}], 5)
    assert out["message"]["content"] == "ok" and tried == ["a", "b"]


def test_request_errors_do_not_fail_over(monkeypatch):
    monkeypatch.setenv("NVIDIA_API_KEY_1", "a")
    monkeypatch.setenv("NVIDIA_API_KEY_2", "b")
    tried = []

    def fake_chat(provider, key, model, messages, max_tokens, *, temperature=None, post=None):
        tried.append(key)
        raise prov.ProviderError(410, "model retired")

    monkeypatch.setattr(prov, "chat", fake_chat)
    with pytest.raises(RuntimeError, match="410"):
        core.call_via_router("nvidia", "a", "retired-model", [{"role": "user", "content": "x"}], 5)
    assert tried == ["a"]
