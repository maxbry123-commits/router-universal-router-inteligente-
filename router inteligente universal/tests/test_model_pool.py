"""Chat chain 2026-09-29 (Director 05:15): Kimi K3 -> GLM 5.3 -> DeepSeek V4 -> Qwen 3.8 (Groq) -> Nemotron LAST, list of available models,
fast jump when a model does not answer, NVIDIA keys 1-3 first then 4. Stdlib only (no fastapi / huggingface_hub needed)."""
from __future__ import annotations

import asyncio
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from integration.chat_mvp import model_pool as MP  # noqa: E402
from integration.chat_mvp import providers as P  # noqa: E402
from integration.chat_mvp import resilience as R  # noqa: E402

ENV = ("NVIDIA_API_KEY", "NVIDIA_API_KEY_1", "NVIDIA_API_KEY_2", "NVIDIA_API_KEY_3", "NVIDIA_API_KEY_4", "NVIDIA_API_KEY_5", "HF_TOKEN", "HF_TOKEN_1",
       "GROQ_API_KEY", "GROQ_API_KEY_1", "RIU_LOCAL_BASE_URL", "RIU_G2_GROQ_MODEL", "RIU_G2_LOCAL_MODEL",
       "RIU_CHAT_ATTEMPT_TIMEOUT", "RIU_MODEL_COOLDOWN")
MON_OFF = datetime(2026, 9, 21, 12, 0, tzinfo=timezone.utc)
MON_PEAK = datetime(2026, 9, 21, 7, 0, tzinfo=timezone.utc)
KIMI, GLM, DEEPSEEK, QWEN, NEMO = ("moonshotai/kimi-k3", "z-ai/glm-5.3", "deepseek-ai/DeepSeek-V4-Flash", "qwen/qwen3.8-27b",
                                   "nvidia/nemotron-3-super-120b-a12b")


@pytest.fixture(autouse=True)
def _clean(monkeypatch):
    for n in ENV:
        monkeypatch.delenv(n, raising=False)
    P._models_cache.clear()
    R.ROUTER.breaker._state.clear()
    yield
    P._models_cache.clear()
    R.ROUTER.breaker._state.clear()


class Clock:
    def __init__(self) -> None:
        self.t = 1000.0

    def __call__(self) -> float:
        return self.t


def all_keys(monkeypatch):
    for i in (1, 2, 3, 4):
        monkeypatch.setenv(f"NVIDIA_API_KEY_{i}", f"n{i}")
    monkeypatch.setenv("HF_TOKEN_1", "h")
    monkeypatch.setenv("GROQ_API_KEY_1", "g")


def test_default_chain_is_the_directors_order_with_nemotron_last(monkeypatch):
    all_keys(monkeypatch)
    pol = R.DEFAULT_POLICY["default"]
    assert pol["authorized_fallback"] is True  # the chat falls to the next option by itself
    ch, skipped = R.resolve_chain("default", MON_OFF)
    assert [c["model"] for c in ch] == [KIMI, GLM, DEEPSEEK, QWEN, NEMO] and [c["provider"] for c in ch] == ["nvidia", "nvidia", "hf", "groq", "nvidia"]
    ch, skipped = R.resolve_chain("default", MON_PEAK)  # DeepSeek peak hours: it is skipped, the rest keeps its order
    assert [c["model"] for c in ch] == [KIMI, GLM, QWEN, NEMO] and any("PEAK_HOUR" in s for s in skipped)
    ch, _ = R.resolve_chain("g2", MON_OFF, {"RIU_G2_GROQ_MODEL": "llama3.1-8b"})
    assert ch[-1]["model"] == NEMO  # Nemotron is the last option in g2 too


def test_pool_lists_only_listable_providers_and_never_raises():
    calls = []

    def fetch(provider, key):
        calls.append((provider, key))
        raise RuntimeError("provider down")

    pool = MP.ModelPool(fetch=fetch)
    assert pool.listed("hf") is None and pool.listed("local") is None and calls == []  # ids not checked against a list
    assert pool.listed("nvidia") is None  # no key configured -> unknown
    assert calls == []


def test_pool_caches_lists_and_does_not_hammer_a_dead_provider(monkeypatch):
    monkeypatch.setenv("NVIDIA_API_KEY_1", "n1")
    monkeypatch.setenv("NVIDIA_API_KEY_2", "n2")
    monkeypatch.setenv("NVIDIA_API_KEY_3", "n3")
    clock, calls = Clock(), []

    def fetch(provider, key):
        calls.append(key)
        raise RuntimeError("timeout")

    pool = MP.ModelPool(fetch=fetch, clock=clock)
    assert pool.listed("nvidia") is None and calls == ["n1", "n2"]  # at most 2 keys are tried
    assert pool.listed("nvidia") is None and len(calls) == 2  # remembered as unknown, not asked again at once
    clock.t += MP.UNKNOWN_RETRY + 1
    pool.listed("nvidia")
    assert len(calls) == 4
    good = MP.ModelPool(fetch=lambda p, k: [KIMI, GLM], clock=clock)
    assert good.listed("nvidia") == frozenset({KIMI, GLM})
    good._fetch = lambda p, k: (_ for _ in ()).throw(RuntimeError("must not be asked again"))
    assert good.listed("nvidia") == frozenset({KIMI, GLM})  # cached for LIST_TTL
    assert MP.ModelPool(fetch=lambda p, k: []).listed("nvidia") is None  # an empty list means unknown, not "nothing is available"


def test_filter_drops_unlisted_and_cooling_but_keeps_order_and_unknowns(monkeypatch):
    all_keys(monkeypatch)
    clock = Clock()
    pool = MP.ModelPool(fetch=lambda p, k: [GLM, NEMO] if p == "nvidia" else [], clock=clock, cooldown=100)
    chain, _ = R.resolve_chain("default", MON_OFF)
    kept, skipped = pool.filter(chain)
    # Kimi is not in NVIDIA's list; DeepSeek (hf) is unknown -> tried; Qwen (groq) list is empty -> unknown -> tried
    assert [c["model"] for c in kept] == [GLM, DEEPSEEK, QWEN, NEMO] and skipped == [f"nvidia/{KIMI}:NOT_LISTED"]
    pool.mark_bad("nvidia", GLM, "timeout")
    kept, skipped = pool.filter(chain)
    assert [c["model"] for c in kept] == [DEEPSEEK, QWEN, NEMO] and f"nvidia/{GLM}:COOLING" in skipped
    assert pool.snapshot()["cooling"][f"nvidia/{GLM}"]["seconds_left"] == 100.0
    clock.t += 101  # cooldown over: tried again
    assert [c["model"] for c in pool.filter(chain)[0]][0] == GLM
    pool.mark_bad("nvidia", GLM)
    pool.mark_ok("nvidia", GLM)
    assert not pool.cooling("nvidia", GLM)


def test_run_policy_learns_a_dead_model_and_the_next_request_skips_it(monkeypatch):
    all_keys(monkeypatch)
    pool = MP.ModelPool(fetch=lambda p, k: [], cooldown=100)
    seen = []

    def call(provider, key, model, messages, max_tokens, temperature):
        seen.append(model)
        if model == KIMI:
            raise RuntimeError("PROVIDER_ERROR:TimeoutError:request failed")
        return {"message": {"content": "hola desde " + model}}

    out = R.run_policy("default", [], 5, now=MON_OFF, call=call, pool=pool)
    assert out["route"]["model"] == GLM and out["route"]["attempt"] == 2 and seen == [KIMI, GLM]
    assert pool.cooling("nvidia", KIMI)
    seen.clear()
    out = R.run_policy("default", [], 5, now=MON_OFF, call=call, pool=pool)
    assert out["route"]["model"] == GLM and seen == [GLM] and f"nvidia/{KIMI}:COOLING" in out["trace"]  # no time lost on Kimi


def test_nemotron_is_used_only_when_everything_before_it_failed(monkeypatch):
    all_keys(monkeypatch)
    seen = []

    def call(provider, key, model, messages, max_tokens, temperature):
        seen.append(model)
        if model != NEMO:
            raise RuntimeError("PROVIDER_ERROR:503:busy")
        return {"message": {"content": "ok"}}

    out = R.run_policy("default", [], 5, now=MON_OFF, call=call, pool=MP.ModelPool(fetch=lambda p, k: []))
    assert seen == [KIMI, GLM, DEEPSEEK, QWEN, NEMO] and out["route"]["model"] == NEMO
    with pytest.raises(R.RouteFailed, match="ROUTER_ALL_ROUTES_FAILED"):
        R.run_policy("default", [], 5, now=MON_OFF, call=lambda *a: (_ for _ in ()).throw(RuntimeError("PROVIDER_ERROR:503:busy")))


def test_pool_never_leaves_the_chat_without_a_route(monkeypatch):
    all_keys(monkeypatch)
    pool = MP.ModelPool(fetch=lambda p, k: ["some/other-model"])  # nothing of the chain is listed by NVIDIA / Groq
    seen = []
    out = R.run_policy("default", [], 5, now=MON_OFF, pool=pool,
                       call=lambda p, k, m, msgs, mt, t: (seen.append(m), {"message": {"content": "ok"}})[1])
    assert out["route"]["model"] == DEEPSEEK and "POOL_EMPTY_TRY_ALL" not in out["trace"]  # hf is unknown -> still tried
    monkeypatch.delenv("HF_TOKEN_1")
    seen.clear()
    out = R.run_policy("default", [], 5, now=MON_OFF, pool=pool,
                       call=lambda p, k, m, msgs, mt, t: (seen.append(m), {"message": {"content": "ok"}})[1])
    assert "POOL_EMPTY_TRY_ALL" in out["trace"] and seen == [KIMI]  # everything filtered -> the whole chain is tried


def test_pool_is_ignored_where_fallback_is_not_authorized(monkeypatch):
    all_keys(monkeypatch)
    monkeypatch.setitem(R.DEFAULT_POLICY, "strict", {"authorized_fallback": False, "chain": [R.NEMOTRON, R.MINIMAX]})
    pool = MP.ModelPool(fetch=lambda p, k: ["some/other-model"])
    seen = []
    with pytest.raises(R.RouteFailed) as exc:
        R.run_policy("strict", [], 5, now=MON_OFF, pool=pool,
                     call=lambda p, k, m, msgs, mt, t: (seen.append(m), (_ for _ in ()).throw(RuntimeError("PROVIDER_ERROR:503:x")))[1])
    assert seen == [NEMO] and str(exc.value).startswith("NEEDS_DIRECTOR_AUTH")  # no silent fallback, the pool did not skip anything
    assert not pool.cooling("nvidia", NEMO)


def test_a_busy_router_is_not_a_dead_model(monkeypatch):
    all_keys(monkeypatch)
    pool = MP.ModelPool(fetch=lambda p, k: [])

    def call(provider, key, model, messages, max_tokens, temperature):
        if model == KIMI:
            raise R.Saturated("ROUTER_SATURATED")
        return {"message": {"content": "ok"}}

    R.run_policy("default", [], 5, now=MON_OFF, call=call, pool=pool)
    assert not pool.cooling("nvidia", KIMI)


def test_only_the_last_option_keeps_the_full_provider_timeout(monkeypatch):
    all_keys(monkeypatch)
    deadlines = []

    def call(provider, key, model, messages, max_tokens, temperature):
        deadlines.append(P.ATTEMPT_DEADLINE.get())
        raise RuntimeError("PROVIDER_ERROR:503:x")

    with pytest.raises(R.RouteFailed):
        R.run_policy("default", [], 5, now=MON_OFF, call=call, attempt_timeout=30)
    assert all(d is not None and d > time.monotonic() for d in deadlines[:-1]) and len(deadlines) == 5
    assert deadlines[-1] is None and P.ATTEMPT_DEADLINE.get() is None  # last option: full timeout; nothing leaks after the request
    deadlines.clear()
    with pytest.raises(R.RouteFailed):
        R.run_policy("default", [], 5, now=MON_OFF, call=call, attempt_timeout=0)  # 0 = no limit at all
    assert deadlines == [None] * 5


def test_the_option_time_limit_grows_with_the_answer_size(monkeypatch):
    all_keys(monkeypatch)
    left = []

    def call(provider, key, model, messages, max_tokens, temperature):
        if P.ATTEMPT_DEADLINE.get() is not None:
            left.append(P.ATTEMPT_DEADLINE.get() - time.monotonic())
        raise RuntimeError("PROVIDER_ERROR:503:x")

    with pytest.raises(R.RouteFailed):
        R.run_policy("default", [], 4096, now=MON_OFF, call=call, attempt_timeout=10)
    assert 38 < left[0] <= 40  # 10 s x (4096 / 1024)
    left.clear()
    with pytest.raises(R.RouteFailed):
        R.run_policy("default", [], 100, now=MON_OFF, call=call, attempt_timeout=10)
    assert 8 < left[0] <= 10  # a short answer never gets less than the base limit


def test_deadline_cuts_the_http_timeout_and_travels_through_asyncio_and_threads():
    assert P.chat_timeout() == 90.0
    seen = []

    async def main():
        await asyncio.to_thread(lambda: seen.append(P.chat_timeout()))  # same shape as core.call_via_router -> hot path executor

    token = P.ATTEMPT_DEADLINE.set(time.monotonic() + 5)
    try:
        asyncio.run(main())
        assert 1.0 <= seen[0] <= 5.0 and P.chat_timeout() <= 5.0
    finally:
        P.ATTEMPT_DEADLINE.reset(token)
    token = P.ATTEMPT_DEADLINE.set(time.monotonic() - 10)  # already expired: still one second so the call can fail cleanly
    try:
        assert P.chat_timeout() == 1.0
    finally:
        P.ATTEMPT_DEADLINE.reset(token)


def test_a_dead_model_does_not_put_a_healthy_key_in_cooldown():
    r = R.Router(R.CircuitBreaker(2, 60), R.AdaptiveLimiter((5,), 1, 2))

    def chat(provider, key, model, messages, max_tokens, temperature=None):
        if model == "dead":
            raise P.ProviderError("TimeoutError", "x")
        return {"message": {"content": "ok"}}

    for _ in range(2):
        with pytest.raises(R.AllKeysFailed):
            r.execute("nvidia", ["a"], "dead", [], 5, None, chat)
    with pytest.raises(R.AllKeysFailed, match="COOLDOWN"):
        r.execute("nvidia", ["a"], "dead", [], 5, None, chat)  # (key, dead model) is in cooldown ...
    assert r.execute("nvidia", ["a"], "alive", [], 5, None, chat)["message"]["content"] == "ok"  # ... the key is fine for other models


def test_nvidia_keys_are_tried_1_2_3_then_4_and_a_busy_key_goes_last(monkeypatch):
    for i in (4, 2, 1, 3):  # set in mixed order on purpose: the pool order is 1, 2, 3, 4
        monkeypatch.setenv(f"NVIDIA_API_KEY_{i}", f"n{i}")
    assert P.env_keys("nvidia") == ["n1", "n2", "n3", "n4"]
    r = R.Router(R.CircuitBreaker(3, 60), R.AdaptiveLimiter((5,), 1, 2))
    tried = []

    def chat(provider, key, model, messages, max_tokens, temperature=None):
        tried.append(key)
        if key in ("n1", "n2", "n3"):
            raise P.ProviderError(429, "busy")
        return {"message": {"content": "ok"}}

    assert r.execute("nvidia", P.env_keys("nvidia"), "m", [], 5, None, chat)["message"]["content"] == "ok"
    assert tried == ["n1", "n2", "n3", "n4"]  # keys 1-3 first; only when they are busy, key 4
    tried.clear()
    r.execute("nvidia", P.env_keys("nvidia"), "m", [], 5, None, chat)
    assert tried == ["n4"]  # 1-3 have a recent failure: the healthy key 4 goes first now (they are retried after their cooldown)


def test_a_slow_model_does_not_block_the_chat_real_socket(monkeypatch):
    """Real HTTP server that answers model "slow" only after 8 s: the chat must move on after the per-option limit (2 s here; 30 s by
    default, and 90 s would be the provider timeout), and remember that model as cooling."""
    import http.server
    import json
    import threading

    class Handler(http.server.BaseHTTPRequestHandler):
        def do_POST(self):  # noqa: N802
            body = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))) or b"{}")
            if body.get("model") == "slow":
                time.sleep(8)
            data = json.dumps({"choices": [{"message": {"role": "assistant", "content": "hola de " + str(body.get("model"))},
                                            "finish_reason": "stop"}]}).encode()
            try:
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)
            except OSError:
                pass  # the client gave up on the slow option: expected

        def log_message(self, *args):
            pass

    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    server.daemon_threads = True
    threading.Thread(target=server.serve_forever, daemon=True).start()
    monkeypatch.setenv("RIU_LOCAL_BASE_URL", f"http://127.0.0.1:{server.server_address[1]}/v1")
    monkeypatch.setitem(R.DEFAULT_POLICY, "slowtest", {"authorized_fallback": True, "chain": [{"provider": "local", "model": "slow"},
                                                                                             {"provider": "local", "model": "fast"}]})
    pool = MP.ModelPool(fetch=lambda p, k: [], cooldown=100)

    def call(provider, key, model, messages, max_tokens, temperature):
        return R.ROUTER.execute(provider, [key], model, messages, max_tokens, temperature, P.chat)

    t0 = time.monotonic()
    try:
        out = R.run_policy("slowtest", [{"role": "user", "content": "hola"}], 5, now=MON_OFF, call=call, attempt_timeout=2, pool=pool)
    finally:
        server.shutdown()
        server.server_close()
    elapsed = time.monotonic() - t0
    assert out["route"]["model"] == "fast" and out["message"]["content"] == "hola de fast" and out["route"]["attempt"] == 2
    assert elapsed < 6.5, elapsed  # holding on to the slow option would have taken 8 s here (90 s in production)
    assert any(t.startswith("local/slow:") for t in out["trace"]) and pool.cooling("local", "slow")
