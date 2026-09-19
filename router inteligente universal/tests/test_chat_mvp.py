from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

try:  # keep the suite runnable where huggingface_hub is not installed
    import huggingface_hub  # noqa: F401
except ImportError:  # pragma: no cover
    import types

    sys.modules["huggingface_hub"] = types.SimpleNamespace(InferenceClient=object)

from integration.huggingface import chat_catalog as cat  # noqa: E402
from integration.huggingface import chat_executor as ex  # noqa: E402
from integration.huggingface import huggingface_openai_chat as adapter  # noqa: E402

REG = {
    "runtime_inference_verified_model_ids": ["Qwen/Qwen3-0.6B"],
    "remote20_provider_live_verified": {"models": [
        {"model_id": "moonshotai/Kimi-K3", "providers_live": ["together"]},
        {"model_id": "deepseek-ai/DeepSeek-V4-Flash", "providers_live": ["novita"]},
        {"model_id": "deepseek-ai/DeepSeek-V4-Flash-0731", "providers_live": ["novita"]},
        {"model_id": "deepseek-ai/DeepSeek-V4-Flash-Vision-Exp", "providers_live": ["novita"]},
        {"model_id": "deepseek-ai/DeepSeek-V4-Pro", "providers_live": ["baseten"]},
        {"model_id": "Qwen/Qwen3.8-27B", "providers_live": ["novita"]},
    ]},
}


@pytest.fixture(autouse=True)
def _fixture_registry(monkeypatch):
    monkeypatch.setattr(cat, "_registry", lambda: REG)
    monkeypatch.setattr(adapter, "_registry", lambda: REG)
    monkeypatch.setattr(cat, "_cache", {"at": None, "ids": []})


def rows(payload):
    return {r["model_id"]: r for r in payload["models"]}


def test_selector_has_requested_families_and_excludes_vision_variant():
    r = rows(cat.selector_models(registry=REG))
    assert "moonshotai/Kimi-K3" in r
    assert {"deepseek-ai/DeepSeek-V4-Flash", "deepseek-ai/DeepSeek-V4-Flash-0731", "deepseek-ai/DeepSeek-V4-Pro"} <= set(r)
    assert "deepseek-ai/DeepSeek-V4-Flash-Vision-Exp" not in r
    assert "Qwen/Qwen3.8-27B" not in r


def test_live_flag_controls_selectable_and_never_marks_certified():
    off = rows(cat.selector_models(registry=REG, live_enabled=False))
    on = rows(cat.selector_models(registry=REG, live_enabled=True))
    assert off["moonshotai/Kimi-K3"]["selectable"] is False
    assert off["moonshotai/Kimi-K3"]["reason"] == "LIVE_PROVIDER_INFERENCE_DISABLED"
    assert on["moonshotai/Kimi-K3"]["selectable"] is True
    assert on["moonshotai/Kimi-K3"]["certified"] is False
    assert on["Qwen/Qwen3-0.6B"]["certified"] is True and off["Qwen/Qwen3-0.6B"]["selectable"] is True


def test_minimax_is_hub_only_until_router_catalog_lists_it_and_is_never_invented():
    r = rows(cat.selector_models(registry=REG, live_enabled=True))
    m3 = r["MiniMaxAI/MiniMax-M3"]
    assert m3["state"] == cat.HUB_ONLY and m3["selectable"] is False
    r2 = rows(cat.selector_models(registry=REG, live_enabled=True, discovered=["MiniMaxAI/MiniMax-M3", "other/unrelated"]))
    assert r2["MiniMaxAI/MiniMax-M3"]["state"] == cat.ROUTER_LIVE
    assert r2["MiniMaxAI/MiniMax-M3"]["selectable"] is True
    assert "other/unrelated" not in r2


def test_discovery_is_fail_closed_and_negative_cache_expires():
    def boom():
        raise OSError("network down")

    assert cat.discover_catalog_ids(boom) == []
    assert cat.discover_catalog_ids(lambda: {"data": [{"id": "b/x"}, {"id": "a/y"}, {"bad": 1}]}) == ["a/y", "b/x"]
    clock = iter([0.0, 10.0, 31.0])
    calls = []

    def fetch():
        calls.append(1)
        raise OSError("down")

    now = lambda: next(clock)  # noqa: E731
    assert cat.cached_discovery(fetch=fetch, now=now) == []
    assert cat.cached_discovery(fetch=fetch, now=now) == []
    assert len(calls) == 1  # negative cache honoured at t=10
    assert cat.cached_discovery(fetch=fetch, now=now) == []
    assert len(calls) == 2  # expired at t=31


def test_executor_certified_path_and_flag_off_rejects_live_models(monkeypatch):
    monkeypatch.setattr(adapter, "chat_completion", lambda **kw: {"model": kw["model_id"], "message": {"role": "assistant", "content": "ok"}, "finish_reason": "stop"})
    run = ex.make_executor(allow_provider_live=False, discover=lambda: [])
    out = run(model_id="Qwen/Qwen3-0.6B", messages=[{"role": "user", "content": "hi"}], max_tokens=8)
    assert out["certified"] is True and out["message"]["content"] == "ok"
    with pytest.raises(ValueError, match="MODEL_NOT_IN_CERTIFIED_REGISTRY"):
        run(model_id="moonshotai/Kimi-K3", messages=[], max_tokens=8)


def test_executor_live_path_needs_flag_selector_family_and_token(monkeypatch):
    monkeypatch.delenv("HF_TOKEN", raising=False)
    run = ex.make_executor(allow_provider_live=True, discover=lambda: [])
    with pytest.raises(ValueError, match="MODEL_NOT_SELECTABLE"):
        run(model_id="Qwen/Qwen3.8-27B", messages=[], max_tokens=8)  # provider-live but not a requested family
    with pytest.raises(RuntimeError, match="HF_TOKEN_REQUIRED"):
        run(model_id="moonshotai/Kimi-K3", messages=[], max_tokens=8)
    monkeypatch.setenv("HF_TOKEN", "test-token-not-a-secret")
    seen = {}

    def fake_call(*, token, model_id, messages, max_tokens):
        seen.update(token=token, model=model_id)
        return {"model": model_id, "message": {"role": "assistant", "content": "kimi"}, "finish_reason": "stop"}

    monkeypatch.setattr(ex, "_call_inference", fake_call)
    out = run(model_id="moonshotai/Kimi-K3", messages=[{"role": "user", "content": "x"}], max_tokens=8)
    assert out["certified"] is False and out["message"]["content"] == "kimi" and seen["model"] == "moonshotai/Kimi-K3"
    live_minimax = ex.make_executor(allow_provider_live=True, discover=lambda: ["MiniMaxAI/MiniMax-M3"])
    assert live_minimax(model_id="MiniMaxAI/MiniMax-M3", messages=[], max_tokens=8)["certified"] is False
    with pytest.raises(ValueError, match="MODEL_NOT_SELECTABLE"):
        run(model_id="MiniMaxAI/MiniMax-M3", messages=[], max_tokens=8)  # not discovered -> not attempted
