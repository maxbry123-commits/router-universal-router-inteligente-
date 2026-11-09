from __future__ import annotations

import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from integration.chat_mvp import providers as P  # noqa: E402
from integration.chat_mvp import resilience as R  # noqa: E402

ENV = ("NVIDIA_API_KEY", "NVIDIA_API_KEY_1", "HF_TOKEN", "HF_TOKEN_1", "GROQ_API_KEY", "GROQ_API_KEY_1", "RIU_LOCAL_BASE_URL",
       "RIU_G2_GROQ_MODEL", "RIU_G2_LOCAL_MODEL", "RIU_CHAT_ATTEMPT_TIMEOUT", "RIU_MODEL_COOLDOWN")
MON_OFF = datetime(2026, 9, 21, 12, 0, tzinfo=timezone.utc)
MON_PEAK = datetime(2026, 9, 21, 7, 0, tzinfo=timezone.utc)
MODELS = ["moonshotai/kimi-k3", "z-ai/glm-5.3", "deepseek-ai/DeepSeek-V4-Flash", "qwen/qwen3.8-27b"]


@pytest.fixture(autouse=True)
def _clean(monkeypatch):
    for n in ENV:
        monkeypatch.delenv(n, raising=False)


def _keys(monkeypatch):
    monkeypatch.setenv("NVIDIA_API_KEY", "k")
    monkeypatch.setenv("HF_TOKEN", "k")
    monkeypatch.setenv("GROQ_API_KEY", "k")


def test_json_file_loads_and_matches_code_policy_for_old_groups():
    loaded = R.load_policy()
    assert loaded == R.CODE_POLICY
    assert R.DEFAULT_POLICY == R.CODE_POLICY
    assert set(loaded) >= {"default", "code", "minor", "g2", "chat_nvidia", "sdk"}
    assert loaded["default"]["chain"][0] == R.KIMI_K3 and loaded["default"]["chain"][-1] == R.NEMOTRON


def test_chat_nvidia_chain_order_timeouts_and_no_nemotron():
    chain = R.DEFAULT_POLICY["chat_nvidia"]["chain"]
    assert [e["model"] for e in chain] == MODELS
    assert [e["provider"] for e in chain] == ["nvidia", "nvidia", "hf", "groq"]
    assert all(e["timeout"] == 90 for e in chain)
    assert chain[2]["deepseek"] is True
    assert not any("nemotron" in e["model"].lower() for e in chain)


def test_missing_or_invalid_json_falls_back_to_code(tmp_path):
    assert R.load_policy(tmp_path / "nope.json") == R.CODE_POLICY
    bad = tmp_path / "bad.json"
    bad.write_text("{not json", encoding="utf-8")
    assert R.load_policy(bad) == R.CODE_POLICY
    bad.write_text(json.dumps({"groups": [1, 2]}), encoding="utf-8")
    assert R.load_policy(bad) == R.CODE_POLICY
    bad.write_text("[]", encoding="utf-8")
    assert R.load_policy(bad) == R.CODE_POLICY


def test_invalid_group_is_skipped_valid_group_overrides(tmp_path):
    f = tmp_path / "p.json"
    f.write_text(json.dumps({"groups": {
        "code": {"authorized_fallback": True, "chain": [{"provider": "nvidia"}]},  # no model: invalid, code version stays
        "mine": {"authorized_fallback": False, "chain": [{"provider": "hf", "model": "x/y", "timeout": 12}]},
        "badtimeout": {"authorized_fallback": True, "chain": [{"provider": "hf", "model": "x/y", "timeout": "90"}]},
        "default": {"authorized_fallback": True, "chain": [{"provider": "groq", "model": "a/b"}]}}}), encoding="utf-8")
    pol = R.load_policy(f)
    assert pol["code"] == R.CODE_POLICY["code"]
    assert pol["mine"]["chain"][0]["timeout"] == 12
    assert "badtimeout" not in pol
    assert pol["default"]["chain"] == [{"provider": "groq", "model": "a/b"}]
    assert pol["chat_nvidia"] == R.CODE_POLICY["chat_nvidia"]


def test_chat_nvidia_resolves_and_skips_deepseek_in_peak(monkeypatch):
    _keys(monkeypatch)
    chain, skipped = R.resolve_chain("chat_nvidia", MON_OFF)
    assert [e["model"] for e in chain] == MODELS and skipped == []
    chain, skipped = R.resolve_chain("chat_nvidia", MON_PEAK)
    assert [e["model"] for e in chain] == [MODELS[0], MODELS[1], MODELS[3]]
    assert any("PEAK_HOUR" in s for s in skipped)


def test_chat_nvidia_gives_each_option_its_own_90s_not_the_30s_base(monkeypatch):
    _keys(monkeypatch)
    monkeypatch.setenv("RIU_CHAT_ATTEMPT_TIMEOUT", "5")
    seen = []

    def call(provider, key, model, messages, max_tokens, temperature):
        left = P.ATTEMPT_DEADLINE.get()
        seen.append((model, None if left is None else left - time.monotonic()))
        if model != MODELS[2]:
            raise RuntimeError("PROVIDER_ERROR:503:busy")
        return {"message": {"content": "ok"}}

    out = R.run_policy("chat_nvidia", [], 5, now=MON_OFF, call=call)
    assert out["route"]["model"] == MODELS[2] and out["route"]["attempt"] == 3
    want = min(90.0, P.CHAT_TIMEOUT)
    assert [m for m, _ in seen] == MODELS[:3]
    assert all(left is not None and want - 5 < left <= want for _, left in seen)


def test_other_groups_keep_base_timeout(monkeypatch):
    _keys(monkeypatch)
    monkeypatch.setenv("RIU_CHAT_ATTEMPT_TIMEOUT", "5")
    seen = []

    def call(provider, key, model, messages, max_tokens, temperature):
        left = P.ATTEMPT_DEADLINE.get()
        seen.append(None if left is None else left - time.monotonic())
        if len(seen) == 1:
            raise RuntimeError("PROVIDER_ERROR:503:busy")
        return {"message": {"content": "ok"}}

    R.run_policy("default", [], 5, now=MON_OFF, call=call)
    assert seen[0] is not None and seen[0] <= 5.0  # first (not last) option: base limit, unchanged behaviour


def test_sdk_group_is_empty_and_does_not_break(monkeypatch):
    _keys(monkeypatch)
    assert R.resolve_chain("sdk", MON_OFF) == ([], [])
    with pytest.raises(R.RouteFailed):
        R.run_policy("sdk", [], 5, now=MON_OFF, call=lambda *a: {})
    assert R.resolve_chain("unknown_group", MON_OFF)[0] == R.resolve_chain("default", MON_OFF)[0]
