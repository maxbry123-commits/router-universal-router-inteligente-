from __future__ import annotations

import sys
import threading
from datetime import datetime, timezone
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from integration.chat_mvp import providers as P  # noqa: E402
from integration.chat_mvp import resilience as R  # noqa: E402

ENV = ("NVIDIA_API_KEY", "NVIDIA_API_KEY_1", "NVIDIA_API_KEY_2", "NVIDIA_API_KEY_3", "NVIDIA_API_KEY_4", "NVIDIA_API_KEY_5", "HF_TOKEN", "HF_TOKEN_1",
       "CEREBRAS_API_KEY", "CEREBRAS_API_KEY_1", "RIU_LOCAL_BASE_URL", "RIU_G2_CEREBRAS_MODEL", "RIU_G2_LOCAL_MODEL")
MON_OFF = datetime(2026, 9, 21, 12, 0, tzinfo=timezone.utc)
MON_PEAK = datetime(2026, 9, 21, 7, 0, tzinfo=timezone.utc)


@pytest.fixture(autouse=True)
def _clean(monkeypatch):
    for n in ENV:
        monkeypatch.delenv(n, raising=False)


def test_deepseek_peak_windows_are_monday_to_friday_utc():
    assert R.is_peak_utc(datetime(2026, 9, 21, 2, 0, tzinfo=timezone.utc)) is True
    assert R.is_peak_utc(datetime(2026, 9, 21, 7, 0, tzinfo=timezone.utc)) is True
    assert R.is_peak_utc(MON_OFF) is False
    assert R.is_peak_utc(datetime(2026, 9, 20, 2, 0, tzinfo=timezone.utc)) is False  # Sunday


def test_circuit_breaker_opens_probes_and_closes():
    t = [0.0]
    b = R.CircuitBreaker(3, 10, lambda: t[0])
    for _ in range(3):
        b.fail("k")
    assert not b.allow("k")
    t[0] = 11
    assert b.allow("k")  # half-open probe
    b.fail("k")
    assert not b.allow("k")  # the failed probe re-opens it
    b.ok("k")
    assert b.allow("k")


def test_adaptive_limiter_grows_then_refuses_fast():
    lim = R.AdaptiveLimiter((2, 4), 0.05, 0.3)
    for _ in range(2):
        lim.acquire()
    got = []

    def take():
        try:
            lim.acquire()
            got.append("ok")
        except R.Saturated:
            got.append("sat")

    threads = [threading.Thread(target=take) for _ in range(4)]
    [t.start() for t in threads]
    [t.join() for t in threads]
    assert got.count("ok") == 2 and got.count("sat") == 2 and lim.tier == 1


def test_router_orders_healthiest_key_first_skips_open_keys_and_never_fails_over_request_errors():
    r = R.Router(R.CircuitBreaker(2, 60), R.AdaptiveLimiter((5,), 1, 2))
    calls = []

    def chat(provider, key, model, messages, max_tokens, temperature=None):
        calls.append(key)
        if key == "bad":
            raise P.ProviderError("TimeoutError", "x")
        if key == "gone":
            raise P.ProviderError(410, "retired")
        return {"message": {"content": "ok"}}

    assert r.execute("nvidia", ["bad", "good"], "m", [], 5, None, chat)["message"]["content"] == "ok" and calls == ["bad", "good"]
    calls.clear()
    r.execute("nvidia", ["bad", "good"], "m", [], 5, None, chat)
    assert calls == ["good"]  # the key with a recent failure goes last
    for _ in range(2):
        with pytest.raises(R.AllKeysFailed):
            r.execute("nvidia", ["bad"], "m", [], 5, None, chat)
    with pytest.raises(R.AllKeysFailed, match="COOLDOWN"):
        r.execute("nvidia", ["bad"], "m", [], 5, None, chat)
    with pytest.raises(P.ProviderError) as exc:
        r.execute("nvidia", ["gone", "good"], "m", [], 5, None, chat)
    assert exc.value.status == 410


def test_chains_follow_the_directors_rules(monkeypatch):
    monkeypatch.setenv("NVIDIA_API_KEY_1", "n")
    monkeypatch.setenv("HF_TOKEN_1", "h")
    ch, _ = R.resolve_chain("minor", MON_OFF)
    assert [c["model"] for c in ch] == ["deepseek-ai/DeepSeek-V4-Flash", "nvidia/nemotron-3-super-120b-a12b", "MiniMaxAI/MiniMax-M3"]
    ch, skipped = R.resolve_chain("minor", MON_PEAK)  # DeepSeek peak hour: only MiniMax
    assert [c["model"] for c in ch] == ["MiniMaxAI/MiniMax-M3"] and "PEAK_ONLY_MINIMAX" in skipped
    ch, skipped = R.resolve_chain("g2", MON_OFF)
    assert [c["provider"] for c in ch] == ["nvidia", "hf"] and "cerebras:NO_MODEL_CONFIGURED" in skipped and "local:NO_MODEL_CONFIGURED" in skipped
    monkeypatch.setenv("CEREBRAS_API_KEY_1", "c")
    env = {"RIU_G2_CEREBRAS_MODEL": "llama3.1-8b"}
    assert [c["provider"] for c in R.resolve_chain("g2", MON_OFF, env)[0]] == ["nvidia", "cerebras", "hf"]
    ch, skipped = R.resolve_chain("g2", MON_PEAK, env)
    assert [c["provider"] for c in ch] == ["nvidia", "cerebras"] and any("PEAK_HOUR" in s for s in skipped)


def test_policy_falls_back_only_where_authorized(monkeypatch):
    monkeypatch.setenv("NVIDIA_API_KEY_1", "n")
    monkeypatch.setenv("HF_TOKEN_1", "h")
    monkeypatch.setenv("CEREBRAS_API_KEY_1", "c")
    env = {"RIU_G2_CEREBRAS_MODEL": "llama3.1-8b"}
    seen = []

    def call(provider, key, model, messages, max_tokens, temperature):
        seen.append(provider)
        if provider == "nvidia":
            raise RuntimeError("PROVIDER_ERROR:TimeoutError:x")
        return {"message": {"content": "por " + provider}}

    out = R.run_policy("code", [], 5, now=MON_OFF, call=call)
    assert out["route"]["provider"] == "hf" and seen == ["hf"]  # MiniMax first for code
    seen.clear()
    out = R.run_policy("g2", [], 5, now=MON_OFF, call=call, env=env)
    assert out["message"]["content"] == "por cerebras" and seen == ["nvidia", "cerebras"] and out["trace"]
    monkeypatch.setitem(R.DEFAULT_POLICY, "strict", {"authorized_fallback": False, "chain": [R.NEMOTRON, R.MINIMAX]})
    with pytest.raises(R.RouteFailed) as exc:
        R.run_policy("strict", [], 5, now=MON_OFF, call=call)
    assert str(exc.value).startswith("NEEDS_DIRECTOR_AUTH") and "FALLBACK_NOT_AUTHORIZED" in exc.value.trace


def test_no_route_when_nothing_is_configured():
    with pytest.raises(R.RouteFailed, match="ROUTER_NO_ROUTE_AVAILABLE"):
        R.run_policy("minor", [], 5, now=MON_PEAK, call=lambda *a: {})


def test_route_endpoints(tmp_path, monkeypatch):
    pytest.importorskip("fastapi")
    pytest.importorskip("huggingface_hub")
    from fastapi.testclient import TestClient

    from integration.chat_mvp import app as chat_app
    from integration.chat_mvp import core
    from integration.chat_mvp import router as rt
    from integration.chat_mvp.store import Store

    monkeypatch.setenv("RIU_AGENT_API_KEYS", '{"k1": "agent-a"}')
    monkeypatch.setenv("RIU_CHAT_ALLOW_PROVIDER_LIVE", "1")
    monkeypatch.setenv("NVIDIA_API_KEY_1", "n")
    monkeypatch.setenv("HF_TOKEN_1", "h")
    monkeypatch.setattr(core, "cached_discovery", lambda: ["MiniMaxAI/MiniMax-M3"])
    seen = []

    def fake(provider, key, model, messages, max_tokens, temperature=None):
        seen.append((provider, model))
        return {"message": {"role": "assistant", "content": "listo"}, "finish_reason": "stop", "usage": {"prompt_tokens": 2, "completion_tokens": 1}}

    monkeypatch.setattr(core, "call_via_router", fake)
    monkeypatch.setitem(R.DEFAULT_POLICY, "strict", {"authorized_fallback": False, "chain": [R.NEMOTRON, R.MINIMAX]})
    rt.set_store(Store(tmp_path))
    client = TestClient(chat_app.app)
    H = {"X-API-Key": "k1"}
    try:
        assert client.get("/chat/router/status").status_code == 401
        st = client.get("/chat/router/status", headers=H).json()
        assert set(st["groups"]) >= {"default", "code", "minor", "g2"} and st["limiter"]["tiers"] == [3, 10]
        ok = client.post("/chat/route", json={"group": "code", "message": "haz X"}, headers=H)
        assert ok.status_code == 200 and ok.json()["route"]["provider"] == "hf" and seen[-1] == ("hf", "MiniMaxAI/MiniMax-M3")
        assert client.post("/chat/route", json={"group": "default", "message": "hola"}, headers=H).json()["route"]["provider"] == "nvidia"
        assert client.post("/chat/route", json={"group": "default", "message": "x", "agent_id": "nope"}, headers=H).status_code == 400
        monkeypatch.setattr(core, "call_via_router", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("PROVIDER_ERROR:TimeoutError:x")))
        auth = client.post("/chat/route", json={"group": "strict", "message": "hola"}, headers=H)
        assert auth.status_code == 409 and auth.json()["detail"]["error"].startswith("NEEDS_DIRECTOR_AUTH")
    finally:
        rt.set_store(None)
