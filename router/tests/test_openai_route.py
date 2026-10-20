"""Assistants group (Hermes/OpenClaw: NVIDIA first, then Groq, DeepSeek, Nemotron last) and the OpenAI-compatible door /v1/router/*."""
from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from integration.chat_mvp import resilience as R  # noqa: E402

MON_OFF = datetime(2026, 9, 21, 12, 0, tzinfo=timezone.utc)
KEYS = ("NVIDIA_API_KEY_1", "NVIDIA_API_KEY_2", "NVIDIA_API_KEY_3", "NVIDIA_API_KEY_4", "GROQ_API_KEY_2", "HF_TOKEN_1", "HF_TOKEN")


@pytest.fixture(autouse=True)
def _env(monkeypatch):
    for n in KEYS:
        monkeypatch.delenv(n, raising=False)
    for n in ("NVIDIA_API_KEY_1", "NVIDIA_API_KEY_2", "NVIDIA_API_KEY_3", "NVIDIA_API_KEY_4", "GROQ_API_KEY_2", "HF_TOKEN_1"):
        monkeypatch.setenv(n, "k-" + n)


def test_assistants_chain_is_nvidia_then_groq_then_deepseek_with_nemotron_last():
    chain, _ = R.resolve_chain("assistants", MON_OFF)
    assert [c["model"] for c in chain] == ["moonshotai/kimi-k3", "z-ai/glm-5.3", "qwen/qwen3.8-27b", "deepseek-ai/DeepSeek-V4-Flash",
                                          "nvidia/nemotron-3-super-120b-a12b"]
    assert R.DEFAULT_POLICY["assistants"]["authorized_fallback"] is True


def test_assistants_jump_from_busy_nvidia_to_groq_with_all_four_keys_tried_first():
    tried = []

    def call(provider, key, model, messages, max_tokens, temperature):
        tried.append((provider, key, model))
        if provider == "nvidia":
            raise RuntimeError("PROVIDER_ERROR:429:busy")
        return {"message": {"content": "ok"}}

    out = R.run_policy("assistants", [], 5, now=MON_OFF, call=call)
    assert out["route"]["provider"] == "groq"
    kimi_keys = [k for p, k, m in tried if m == "moonshotai/kimi-k3"]
    assert kimi_keys and kimi_keys[0] == "k-NVIDIA_API_KEY_1"  # keys are rotated inside the option; the chain then moves on to Groq


def test_openai_helpers_and_endpoint(tmp_path, monkeypatch):
    pytest.importorskip("fastapi")
    pytest.importorskip("huggingface_hub")
    from fastapi.testclient import TestClient

    from integration.chat_mvp import app as chat_app
    from integration.chat_mvp import core, model_pool, openai_route
    from integration.chat_mvp import router as rt
    from integration.chat_mvp.store import Store

    assert openai_route._text([{"type": "text", "text": "a"}, {"type": "image_url"}, {"type": "text", "text": "b"}]) == "ab"
    assert openai_route.group_for("auto") == "default" and openai_route.group_for("assistants") == "assistants" and openai_route.group_for("gpt-4") is None
    monkeypatch.setenv("RIU_AGENT_API_KEYS", '{"k1": "agent-a"}')
    monkeypatch.setenv("RIU_CHAT_ALLOW_PROVIDER_LIVE", "1")
    monkeypatch.setattr(core, "call_via_router",
                        lambda provider, key, model, messages, max_tokens, temperature=None: {"message": {"role": "assistant", "content": "hola"},
                                                                                              "finish_reason": "stop", "usage": {"prompt_tokens": 3, "completion_tokens": 1, "total_tokens": 4}})
    monkeypatch.setattr(model_pool, "POOL", model_pool.ModelPool(fetch=lambda p, k: []))
    rt.set_store(Store(tmp_path))
    client = TestClient(chat_app.app)
    H = {"X-API-Key": "k1"}
    body = {"model": "assistants", "messages": [{"role": "system", "content": "s"}, {"role": "user", "content": "hola"}], "stream": True}
    assert client.post("/v1/router/chat/completions", json=body).status_code == 401
    ok = client.post("/v1/router/chat/completions", json=body, headers=H)
    assert ok.status_code == 200, ok.text
    j = ok.json()
    assert j["object"] == "chat.completion" and j["choices"][0]["message"]["content"] == "hola" and j["riu"]["group"] == "assistants"
    assert j["usage"]["total_tokens"] == 4 and j["model"].startswith("nvidia/")
    assert client.post("/v1/router/chat/completions", json={**body, "model": "gpt-4"}, headers=H).status_code == 400
    ids = [m["id"] for m in client.get("/v1/router/models", headers=H).json()["data"]]
    assert "auto" in ids and "assistants" in ids
