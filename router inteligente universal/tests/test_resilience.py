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
       "GROQ_API_KEY", "GROQ_API_KEY_1", "RIU_LOCAL_BASE_URL", "RIU_G2_GROQ_MODEL", "RIU_G2_LOCAL_MODEL",
       "RIU_CHAT_ATTEMPT_TIMEOUT", "RIU_MODEL_COOLDOWN")
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
    # 2026-09-29: Kimi K3 -> GLM 5.3 (NVIDIA) -> [Groq] -> [local] -> DeepSeek V4 Flash (HF) -> Nemotron LAST
    assert [c["model"] for c in ch] == ["moonshotai/kimi-k3", "z-ai/glm-5.3", "deepseek-ai/DeepSeek-V4-Flash", "nvidia/nemotron-3-super-120b-a12b"]
    assert "groq:NO_MODEL_CONFIGURED" in skipped and "local:NO_MODEL_CONFIGURED" in skipped
    monkeypatch.setenv("GROQ_API_KEY_1", "c")
    env = {"RIU_G2_GROQ_MODEL": "llama3.1-8b"}
    assert [c["provider"] for c in R.resolve_chain("g2", MON_OFF, env)[0]] == ["nvidia", "nvidia", "groq", "hf", "nvidia"]
    ch, skipped = R.resolve_chain("g2", MON_PEAK, env)
    assert [c["provider"] for c in ch] == ["nvidia", "nvidia", "groq", "nvidia"] and any("PEAK_HOUR" in s for s in skipped)


def test_policy_falls_back_only_where_authorized(monkeypatch):
    monkeypatch.setenv("NVIDIA_API_KEY_1", "n")
    monkeypatch.setenv("HF_TOKEN_1", "h")
    monkeypatch.setenv("GROQ_API_KEY_1", "c")
    env = {"RIU_G2_GROQ_MODEL": "llama3.1-8b"}
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
    assert out["message"]["content"] == "por groq" and seen == ["nvidia", "nvidia", "groq"] and out["trace"]  # Kimi, GLM fail -> Groq
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
    from integration.chat_mvp import core, model_pool
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
    monkeypatch.setitem(R.DEFAULT_POLICY, "onlykimi", {"authorized_fallback": True, "chain": [R.KIMI_K3]})
    monkeypatch.setitem(R.DEFAULT_POLICY, "nokeys", {"authorized_fallback": True, "chain": [R.QWEN_GROQ]})  # Groq has no key in this test: the chain is empty
    listing = {"nvidia": ["z-ai/glm-5.3", "nvidia/nemotron-3-super-120b-a12b"]}  # NVIDIA does not list Kimi in this test
    monkeypatch.setattr(model_pool, "POOL", model_pool.ModelPool(fetch=lambda p, k: listing.get(p, [])))
    rt.set_store(Store(tmp_path))
    client = TestClient(chat_app.app)
    H = {"X-API-Key": "k1"}
    try:
        assert client.get("/chat/router/status").status_code == 401
        st = client.get("/chat/router/status", headers=H).json()
        assert set(st["groups"]) >= {"default", "code", "minor", "g2"} and st["limiter"]["tiers"] == [3, 10]
        assert st["groups"]["default"]["authorized_fallback"] is True and st["attempt_timeout_s"] == 30.0 and "cooling" in st["model_pool"]
        ok = client.post("/chat/route", json={"group": "code", "message": "haz X"}, headers=H)
        assert ok.status_code == 200 and ok.json()["route"]["provider"] == "hf" and seen[-1] == ("hf", "MiniMaxAI/MiniMax-M3")
        dflt = client.post("/chat/route", json={"group": "default", "message": "hola"}, headers=H).json()
        assert dflt["route"]["provider"] == "nvidia" and dflt["route"]["model"] == "z-ai/glm-5.3"  # Kimi not listed -> GLM 5.3
        assert "nvidia/moonshotai/kimi-k3:NOT_LISTED" in dflt["trace"]
        listed = client.get("/chat/providers").json()["providers"]
        assert listed[0]["id"] == "auto" and listed[0]["configured"] is True and "hf" in [p["id"] for p in listed[1:]]  # "auto" first, the real providers after it
        assert client.get("/chat/providers/auto/models").status_code == 401  # like every other provider: needs the API key
        auto_models = client.get("/chat/providers/auto/models", headers=H).json()
        assert auto_models["provider"] == "auto" and [(m["model_id"], m["selectable"]) for m in auto_models["models"]] == [("auto", True)]
        models = client.get("/chat/router/models", headers=H).json()
        assert models["providers"]["nvidia"] == {"configured": True, "listed": 2} and models["providers"]["groq"]["configured"] is False
        assert [c["model"] for c in models["groups"]["default"]["try_order"]][:1] == ["z-ai/glm-5.3"]
        assert client.get("/chat/router/models").status_code == 401
        # same rules as run_policy: a group where the pool filters EVERYTHING out is tried whole; a group without authorization ignores the pool
        assert models["groups"]["onlykimi"] == {"try_order": [{"provider": "nvidia", "model": "moonshotai/kimi-k3"}], "pool_used": True,
                                                "skipped": ["nvidia/moonshotai/kimi-k3:NOT_LISTED", "POOL_EMPTY_TRY_ALL"]}
        assert models["groups"]["nokeys"] == {"try_order": [], "skipped": [], "pool_used": True}  # an empty chain is reported empty, not as "pool emptied it"
        assert models["groups"]["strict"]["pool_used"] is False and models["groups"]["strict"]["skipped"] == []
        assert [c["provider"] for c in models["groups"]["strict"]["try_order"]] == ["nvidia", "hf"]
        assert client.post("/chat/route", json={"group": "default", "message": "x", "agent_id": "nope"}, headers=H).status_code == 400
        monkeypatch.setattr(core, "call_via_router", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("PROVIDER_ERROR:TimeoutError:x")))
        auth = client.post("/chat/route", json={"group": "strict", "message": "hola"}, headers=H)
        assert auth.status_code == 409 and auth.json()["detail"]["error"].startswith("NEEDS_DIRECTOR_AUTH")
    finally:
        rt.set_store(None)


def test_send_auto_uses_the_default_chain_and_keeps_the_conversation(tmp_path, monkeypatch):
    """/chat/send with provider=auto: the Router picks the model (Kimi K3 -> GLM 5.3 -> ... -> Nemotron) and the chat keeps its history."""
    pytest.importorskip("fastapi")
    pytest.importorskip("huggingface_hub")
    from fastapi.testclient import TestClient

    from integration.chat_mvp import app as chat_app
    from integration.chat_mvp import core, model_pool
    from integration.chat_mvp import router as rt
    from integration.chat_mvp.store import Store

    kimi, glm, qwen, nemo = "moonshotai/kimi-k3", "z-ai/glm-5.3", "qwen/qwen3.8-27b", "nvidia/nemotron-3-super-120b-a12b"
    monkeypatch.setenv("RIU_AGENT_API_KEYS", '{"k1": "agent-a"}')
    monkeypatch.setenv("RIU_CHAT_ALLOW_PROVIDER_LIVE", "1")
    monkeypatch.setenv("NVIDIA_API_KEY_1", "n")
    monkeypatch.setenv("GROQ_API_KEY_1", "g")
    monkeypatch.setattr(core, "cached_discovery", lambda: [])
    dead: set[str] = set()
    seen = []

    def fake(provider, key, model, messages, max_tokens, temperature=None):
        seen.append((provider, model, [m["role"] for m in messages]))
        if model in dead:
            raise RuntimeError("PROVIDER_ERROR:TimeoutError:request failed")
        return {"message": {"role": "assistant", "content": "listo desde " + model}, "finish_reason": "stop",
                "usage": {"prompt_tokens": 2, "completion_tokens": 1}}

    monkeypatch.setattr(core, "call_via_router", fake)
    listing = {"nvidia": [kimi, glm, nemo], "groq": [qwen]}
    monkeypatch.setattr(model_pool, "POOL", model_pool.ModelPool(fetch=lambda p, k: listing.get(p, []), cooldown=100))
    rt.set_store(Store(tmp_path))
    client = TestClient(chat_app.app)
    H = {"X-API-Key": "k1"}
    try:
        first = client.post("/chat/send", json={"message": "hola", "provider": "auto"}, headers=H)
        j1 = first.json()
        assert first.status_code == 200 and j1["provider"] == "nvidia" and j1["model"] == kimi and j1["auto"] is True and not any("kimi-k3" in t for t in j1["trace"])
        assert j1["reply"] == "listo desde " + kimi and j1["cached"] is False and j1["conversation_id"]
        dead.add(kimi)  # Kimi stops answering: the chat moves on by itself and still sends the history
        second = client.post("/chat/send", json={"message": "sigue", "provider": "auto", "conversation_id": j1["conversation_id"]}, headers=H).json()
        assert second["model"] == glm and second["conversation_id"] == j1["conversation_id"] and any("kimi-k3:PROVIDER_ERROR" in t for t in second["trace"])
        assert seen[-1] == ("nvidia", glm, ["user", "assistant", "user"])
        third = client.post("/chat/send", json={"message": "otra", "provider": "auto"}, headers=H).json()
        assert third["model"] == glm and f"nvidia/{kimi}:COOLING" in third["trace"]  # Kimi is remembered as dead: no time lost on it
        dead.update({glm, nemo})  # only Groq's Qwen is left before Nemotron... which is dead too
        fourth = client.post("/chat/send", json={"message": "x", "provider": "auto"}, headers=H).json()
        assert fourth["provider"] == "groq" and fourth["model"] == qwen
        dead.add(qwen)
        allfail = client.post("/chat/send", json={"message": "x", "provider": "auto"}, headers=H)
        assert allfail.status_code == 502 and allfail.json()["detail"]["error"] == "ROUTER_ALL_ROUTES_FAILED" and allfail.json()["detail"]["trace"]
        assert client.post("/chat/send", json={"message": "x", "provider": "nvidia"}, headers=H).json()["detail"] == "MODEL_REQUIRED"
        assert client.post("/chat/send", json={"message": "x", "provider": "nope", "model": "m"}, headers=H).json()["detail"] == "PROVIDER_UNKNOWN"
    finally:
        rt.set_store(None)


def test_router_models_report_does_not_take_the_probe_lease(tmp_path, monkeypatch):
    """GET /chat/router/models is only a report: a model whose cooldown ended must stay free for the next REAL request, however often the report is read."""
    pytest.importorskip("fastapi")
    pytest.importorskip("huggingface_hub")
    from fastapi.testclient import TestClient

    from integration.chat_mvp import app as chat_app
    from integration.chat_mvp import model_pool
    from integration.chat_mvp import router as rt
    from integration.chat_mvp.store import Store

    kimi = "moonshotai/kimi-k3"
    monkeypatch.setenv("RIU_AGENT_API_KEYS", '{"k1": "agent-a"}')
    monkeypatch.setenv("NVIDIA_API_KEY_1", "n")
    now = [0.0]
    pool = model_pool.ModelPool(fetch=lambda p, k: [kimi, "z-ai/glm-5.3", "nvidia/nemotron-3-super-120b-a12b"], clock=lambda: now[0], cooldown=10)
    monkeypatch.setattr(model_pool, "POOL", pool)
    rt.set_store(Store(tmp_path))
    client = TestClient(chat_app.app)
    H = {"X-API-Key": "k1"}
    try:
        pool.mark_bad("nvidia", kimi, "test")
        now[0] = 11.0  # the cooldown is over: the next real request may probe Kimi
        for _ in range(2):
            body = client.get("/chat/router/models", headers=H).json()
            assert [c["model"] for c in body["groups"]["default"]["try_order"]][:1] == [kimi]
        assert pool._bad[("nvidia", kimi)][0] == 10.0  # the reports took no lease (a lease would have moved this to 11 + 30)
    finally:
        rt.set_store(None)


def test_auto_is_listed_but_not_configured_when_no_provider_has_a_key(monkeypatch):
    pytest.importorskip("fastapi")
    pytest.importorskip("huggingface_hub")
    from fastapi.testclient import TestClient

    from integration.chat_mvp import app as chat_app

    for spec in P.PROVIDERS.values():  # whatever keys the machine running the test has
        for name in spec["env"]:
            monkeypatch.delenv(name, raising=False)
    first = TestClient(chat_app.app).get("/chat/providers").json()["providers"][0]
    assert first["id"] == "auto" and first["configured"] is False
