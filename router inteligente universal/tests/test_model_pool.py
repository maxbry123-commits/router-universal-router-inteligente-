"""Chat chain 2026-09-29 (Director 05:15): Kimi K3 -> GLM 5.3 -> DeepSeek V4 -> Qwen 3.8 (Groq) -> Nemotron LAST, list of available models,
fast jump when a model does not answer, NVIDIA keys 1-3 first then 4. Stdlib only (no fastapi / huggingface_hub needed)."""
from __future__ import annotations

import asyncio
import sys
import threading
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


def test_pool_lists_only_listable_providers_and_never_raises(monkeypatch):
    calls = []

    def fetch(provider, key):
        calls.append((provider, key))
        raise RuntimeError("provider down")

    pool = MP.ModelPool(fetch=fetch)
    assert pool.listed("hf") is None and pool.listed("local") is None and calls == []  # ids not checked against a list
    assert pool.listed("nvidia") is None  # no key configured -> unknown, nothing asked
    assert calls == []
    monkeypatch.setenv("NVIDIA_API_KEY_1", "n1")
    assert pool.listed("nvidia", force=True) is None and calls == [("nvidia", "n1")]  # a key exists: it IS asked once, and the failure never raises


def test_pool_caches_lists_and_does_not_hammer_a_dead_provider(monkeypatch):
    monkeypatch.setenv("NVIDIA_API_KEY_1", "n1")
    monkeypatch.setenv("NVIDIA_API_KEY_2", "n2")
    monkeypatch.setenv("NVIDIA_API_KEY_3", "n3")
    clock, calls = Clock(), []

    def fetch(provider, key):
        calls.append(key)
        raise P.ProviderError(401, "invalid key")  # an HTTP answer: the next key may work

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


def test_a_slow_or_unreachable_provider_is_asked_only_once_per_turn(monkeypatch):
    """Asking the list must never cost the chat more than one LIST_TIMEOUT per provider: after a timeout no other key is tried."""
    monkeypatch.setenv("NVIDIA_API_KEY_1", "n1")
    monkeypatch.setenv("NVIDIA_API_KEY_2", "n2")
    calls = []

    def fetch(provider, key):
        calls.append(key)
        raise P.ProviderError("TimeoutError", "request failed")

    pool = MP.ModelPool(fetch=fetch)
    assert pool.listed("nvidia") is None and calls == ["n1"]
    chain = [{"provider": "nvidia", "model": KIMI}]
    assert pool.filter(chain) == (chain, []) and calls == ["n1"]  # unknown list -> the model is tried anyway, and nobody asks again for a while


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
    assert pool.cooling("nvidia", GLM)
    pool.mark_ok("nvidia", GLM)
    assert not pool.cooling("nvidia", GLM) and f"nvidia/{GLM}" not in pool.snapshot()["cooling"]


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


def test_every_option_has_a_time_limit_and_the_last_one_gets_the_full_provider_budget(monkeypatch):
    all_keys(monkeypatch)
    left = []

    def call(provider, key, model, messages, max_tokens, temperature):
        d = P.ATTEMPT_DEADLINE.get()
        left.append(None if d is None else d - time.monotonic())
        raise RuntimeError("PROVIDER_ERROR:503:x")

    with pytest.raises(R.RouteFailed):
        R.run_policy("default", [], 5, now=MON_OFF, call=call, attempt_timeout=30)
    assert len(left) == 5 and all(29 < x <= 30 for x in left[:-1])  # every option but the last: the per-option limit
    assert 88 < left[-1] <= 90 and P.ATTEMPT_DEADLINE.get() is None  # last option: ONE 90 s budget for all its keys; nothing leaks after the request
    left.clear()
    with pytest.raises(R.RouteFailed):
        R.run_policy("default", [], 5, now=MON_OFF, call=call, attempt_timeout=0)  # 0 = no limit at all
    assert left == [None] * 5


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
    left.clear()
    with pytest.raises(R.RouteFailed):
        R.run_policy("default", [], 8192, now=MON_OFF, call=call, attempt_timeout=30)
    assert 88 < left[0] <= 90  # 30 s x 8 = 240 s is cut to the 90 s provider timeout: a non-last option never holds the chat longer than that


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


def test_when_the_option_time_is_spent_the_other_keys_are_not_tried_or_blamed():
    """Seen live (2026-09-29): GLM timed out at 30 s and keys 2-4 then got 1 s attempts (+3 s, and marked as failures)."""
    r = R.Router(R.CircuitBreaker(3, 60), R.AdaptiveLimiter((5,), 1, 2))
    tried = []

    def chat(provider, key, model, messages, max_tokens, temperature=None):
        tried.append(key)
        time.sleep(0.15)  # slower than the option time below
        raise P.ProviderError("TimeoutError", "request failed")

    token = P.ATTEMPT_DEADLINE.set(time.monotonic() + 0.05)
    try:
        with pytest.raises(R.AllKeysFailed, match="TimeoutError"):
            r.execute("nvidia", ["a", "b", "c"], "slow-model", [], 5, None, chat)
    finally:
        P.ATTEMPT_DEADLINE.reset(token)
    assert tried == ["a"]  # the first key used the time; b and c were not tried ...
    assert r.breaker.fails(R.key_id("nvidia", "a", "slow-model")) == 1
    assert r.breaker.fails(R.key_id("nvidia", "b", "slow-model")) == 0 and r.breaker.fails(R.key_id("nvidia", "c", "slow-model")) == 0  # ... nor blamed
    tried.clear()
    with pytest.raises(R.AllKeysFailed):  # no deadline (last option of a chain): every key still gets its turn
        r.execute("nvidia", ["a", "b", "c"], "other-model", [], 5, None, chat)
    assert tried == ["a", "b", "c"]


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


# --- audit round 1 (2026-09-29): circuit breaker decay, request errors, probe lease, real hot path ---------------------------------------
def test_a_blip_is_forgiven_after_the_cooldown_so_key_1_is_preferred_again():
    """Keys 1-3 are the priority and 4 the spare: one failure must not demote key 1 for ever (only failures inside one cooldown count)."""
    clock = Clock()
    r = R.Router(R.CircuitBreaker(3, 60, clock), R.AdaptiveLimiter((5,), 1, 2))
    tried, blip = [], {"on": True}

    def chat(provider, key, model, messages, max_tokens, temperature=None):
        tried.append(key)
        if key == "n1" and blip["on"]:
            raise P.ProviderError(429, "blip")
        return {"message": {"content": "ok"}}

    keys = ["n1", "n2", "n3"]
    r.execute("nvidia", keys, "m", [], 5, None, chat)
    assert tried == ["n1", "n2"]
    tried.clear()
    blip["on"] = False
    r.execute("nvidia", keys, "m", [], 5, None, chat)
    assert tried == ["n2"]  # recent failure: n1 goes last
    clock.t += 61
    tried.clear()
    r.execute("nvidia", keys, "m", [], 5, None, chat)
    assert tried == ["n1"]  # forgiven after the cooldown: key 1 is first again


def test_three_failures_spread_over_time_do_not_open_the_breaker_but_three_close_together_do():
    clock = Clock()
    b = R.CircuitBreaker(3, 60, clock)
    for _ in range(3):
        b.fail("slow")
        clock.t += 61
    assert b.allow("slow") and b.fails("slow") == 0
    for _ in range(3):
        b.fail("fast")
    assert not b.allow("fast") and b.fails("fast") == 3
    clock.t += 61
    assert b.allow("fast")  # half-open: one probe
    b.fail("fast")
    assert not b.allow("fast")  # the failed probe re-opens it at once
    b.ok("fast")
    assert b.allow("fast") and b.fails("fast") == 0


def test_a_request_error_does_not_cool_a_model_but_a_model_error_does(monkeypatch):
    all_keys(monkeypatch)
    for text, cools in (("PROVIDER_ERROR:400:bad request", False), ("PROVIDER_ERROR:422:unprocessable", False),
                        ("PROVIDER_ERROR:404:model not found", True), ("PROVIDER_ERROR:429:busy", True),
                        ("PROVIDER_ERROR:503:x", True), ("PROVIDER_ERROR:TimeoutError:request failed", True)):
        pool = MP.ModelPool(fetch=lambda p, k: [], cooldown=100)

        def call(provider, key, model, messages, max_tokens, temperature, text=text):
            if model == KIMI:
                raise RuntimeError(text)
            return {"message": {"content": "ok"}}

        out = R.run_policy("default", [], 5, now=MON_OFF, call=call, pool=pool)
        assert out["route"]["model"] == GLM, text  # the chat always moves on ...
        assert pool.cooling("nvidia", KIMI) is cools, text  # ... but only a model that is really unwell is remembered as dead


def test_after_the_cooldown_only_one_request_probes_the_dead_model():
    clock = Clock()
    pool = MP.ModelPool(fetch=lambda p, k: [], clock=clock, cooldown=100)
    chain = [{"provider": "nvidia", "model": KIMI}, {"provider": "nvidia", "model": GLM}]
    pool.mark_bad("nvidia", KIMI, "timeout")
    assert [c["model"] for c in pool.filter(chain, probe=True)[0]] == [GLM]  # cooling
    clock.t += 101  # cooldown over
    assert pool.filter(chain)[0] == chain and pool.filter(chain)[0] == chain  # a report (/chat/router/models) never takes the lease
    kept, skipped = pool.filter(chain, probe=True)
    assert [c["model"] for c in kept] == [KIMI, GLM] and skipped == []  # the first real request probes Kimi ...
    kept, skipped = pool.filter(chain, probe=True)
    assert [c["model"] for c in kept] == [GLM] and skipped == [f"nvidia/{KIMI}:COOLING"]  # ... the others wait for its answer
    pool.mark_bad("nvidia", KIMI, "probe failed")  # the probe failed: a whole new cooldown
    assert pool.snapshot()["cooling"][f"nvidia/{KIMI}"]["seconds_left"] == 100.0
    clock.t += 101
    assert [c["model"] for c in pool.filter(chain, probe=True)[0]] == [KIMI, GLM]
    clock.t += MP.PROBE_LEASE + 1  # a probe that never reported back must not block the model for ever
    assert [c["model"] for c in pool.filter(chain, probe=True)[0]] == [KIMI, GLM]
    pool.mark_ok("nvidia", KIMI)  # the probe answered: everybody may use it again
    assert pool.filter(chain, probe=True)[0] == chain and pool.filter(chain, probe=True)[0] == chain


def test_two_requests_at_once_after_the_cooldown_send_only_one_to_the_dead_model(monkeypatch):
    all_keys(monkeypatch)
    clock = Clock()
    pool = MP.ModelPool(fetch=lambda p, k: [], clock=clock, cooldown=100)
    pool.mark_bad("nvidia", KIMI, "timeout")
    clock.t += 101
    gate, seen, first = threading.Event(), [], []

    def call(provider, key, model, messages, max_tokens, temperature):
        seen.append(model)
        if model == KIMI:
            gate.wait(10)  # the probe is still running while the second request arrives
            raise RuntimeError("PROVIDER_ERROR:TimeoutError:request failed")
        return {"message": {"content": "ok"}}

    worker = threading.Thread(target=lambda: first.append(R.run_policy("default", [], 5, now=MON_OFF, call=call, pool=pool)))
    worker.start()
    for _ in range(200):
        if KIMI in seen:
            break
        time.sleep(0.01)
    second = R.run_policy("default", [], 5, now=MON_OFF, call=call, pool=pool)
    gate.set()
    worker.join(10)
    assert second["route"]["model"] == GLM and f"nvidia/{KIMI}:COOLING" in second["trace"]
    assert seen.count(KIMI) == 1 and first[0]["route"]["model"] == GLM  # only one request paid for the probe


def test_a_bad_cooldown_setting_does_not_break_the_chat(monkeypatch):
    for bad in ("abc", "-5", "nan", "inf", "1e999"):
        monkeypatch.setenv("RIU_MODEL_COOLDOWN", bad)
        assert MP.ModelPool().cooldown == 120.0, bad
    monkeypatch.setenv("RIU_MODEL_COOLDOWN", "45")
    assert MP.ModelPool().cooldown == 45.0
    monkeypatch.setenv("RIU_MODEL_COOLDOWN", "")
    assert MP.ModelPool().cooldown == 120.0
    assert MP.ModelPool(cooldown=7).cooldown == 7


def test_default_fetch_uses_the_short_timeout_and_refresh_really_asks_again(monkeypatch):
    monkeypatch.setenv("NVIDIA_API_KEY_1", "n1")
    calls = []

    def fake_http(method, url, key, body, timeout):
        calls.append((method, url, key, timeout))
        return {"data": [{"id": KIMI}, {"id": GLM}, {"nope": 1}]}

    monkeypatch.setattr(P, "_http", fake_http)
    pool = MP.ModelPool()  # the real fetch (providers.list_models with the 6 s list timeout)
    assert pool.listed("nvidia") == frozenset({KIMI, GLM})
    assert calls == [("GET", P.base_url("nvidia") + "/models", "n1", MP.LIST_TIMEOUT)] and MP.LIST_TIMEOUT < 10
    pool.listed("nvidia")
    assert len(calls) == 1  # cached
    out = pool.refresh(["nvidia", "groq"])
    assert len(calls) == 2  # refresh asks the provider again (providers.list_models has its own cache: it was dropped)
    assert out == {"nvidia": {"configured": True, "listed": 2}, "groq": {"configured": False, "listed": None}}


# The next three go through the REAL hot path (core.call_via_router -> Enchufe/RedUniversal -> resilience.ROUTER -> providers.chat, only the
# HTTP call is replaced). They need huggingface_hub (CI installs it; the hot path module imports it).
def test_a_saturated_router_through_the_real_hot_path_is_not_a_dead_model(monkeypatch):
    pytest.importorskip("huggingface_hub")
    from integration.chat_mvp import core

    all_keys(monkeypatch)
    limiter = R.AdaptiveLimiter((1,), 0.01, 0.05)
    monkeypatch.setattr(R, "ROUTER", R.Router(R.CircuitBreaker(), limiter))
    monkeypatch.setattr(P, "chat", lambda *a, **k: (_ for _ in ()).throw(AssertionError("must never be reached: every slot is taken")))
    pool = MP.ModelPool(fetch=lambda p, k: [], cooldown=100)
    limiter.acquire()  # the only slot is busy
    try:
        with pytest.raises(R.RouteFailed) as exc:
            R.run_policy("default", [], 5, now=MON_OFF, call=core.call_via_router, pool=pool)
    finally:
        limiter.release()
    assert any("ROUTER_SATURATED" in t for t in exc.value.trace)  # the text survived the hot path (it used to become HF_ROUTER_HOT_PATH_FAILED)
    assert pool.snapshot()["cooling"] == {}  # busy router != dead models: nothing is remembered as dead


def test_the_option_deadline_reaches_the_provider_call_through_the_real_hot_path(monkeypatch):
    pytest.importorskip("huggingface_hub")
    from integration.chat_mvp import core

    all_keys(monkeypatch)
    seen = []

    def fake_chat(provider, key, model, messages, max_tokens, temperature=None):
        seen.append((model, P.chat_timeout()))
        return {"message": {"role": "assistant", "content": "ok"}, "finish_reason": "stop"}

    monkeypatch.setattr(P, "chat", fake_chat)
    out = R.run_policy("default", [], 5, now=MON_OFF, call=core.call_via_router, attempt_timeout=10)
    assert out["route"]["model"] == KIMI and seen[0][0] == KIMI
    assert 8 < seen[0][1] <= 10  # asyncio.run + executor threads of the hot path keep the deadline: the HTTP timeout is ~10 s, not 90 s


def test_nvidia_keys_1_2_3_then_4_through_the_real_hot_path(monkeypatch):
    pytest.importorskip("huggingface_hub")
    from integration.chat_mvp import core

    for i in (4, 2, 1, 3):
        monkeypatch.setenv(f"NVIDIA_API_KEY_{i}", f"n{i}")
    monkeypatch.setattr(R, "ROUTER", R.Router(R.CircuitBreaker(3, 120), R.AdaptiveLimiter((5,), 1, 2)))
    tried = []

    def fake_chat(provider, key, model, messages, max_tokens, temperature=None):
        tried.append((key, model))
        if key in ("n1", "n2", "n3"):
            raise P.ProviderError(429, "busy")
        return {"message": {"role": "assistant", "content": "ok"}, "finish_reason": "stop"}

    monkeypatch.setattr(P, "chat", fake_chat)
    out = R.run_policy("default", [], 5, now=MON_OFF, call=core.call_via_router)
    assert out["route"]["model"] == KIMI and tried == [("n1", KIMI), ("n2", KIMI), ("n3", KIMI), ("n4", KIMI)]  # 1-3 first, 4 only when they are busy
    tried.clear()
    out = R.run_policy("default", [], 5, now=MON_OFF, call=core.call_via_router)
    assert tried == [("n4", KIMI)]  # keys 1-3 have a recent failure for this model: the healthy one goes first
