"""Router resilience for load peaks and provider problems (stdlib only).

Problems seen in real tests (2026-09-20) and the answer to each:
  * NVIDIA heavy models time out when many requests arrive together  -> adaptive concurrency (3 -> 10 slots), then
    ROUTER_SATURATED fast instead of hanging.
  * One NVIDIA key slow / 503 / 402                                   -> circuit breaker per key + healthiest-first order.
  * DeepSeek peak hours (01-04 and 06-10 UTC, Mon-Fri)                -> in peak only MiniMax for code/minor tasks.
  * Provider down or saturated                                        -> fallback chain per group, ONLY where the Director
    authorized it (default chat since 2026-09-29, g2, code, minor). A group WITHOUT authorization reports NEEDS_DIRECTOR_AUTH so the brain can ask.
Group 2 (Director's original rule: NVIDIA -> Groq -> local API -> DeepSeek V4 Flash) now reads Kimi K3 -> GLM 5.3 -> Groq -> local -> DeepSeek V4 Flash ->
Nemotron last: that rewrite of g2 was made by Claude on 2026-09-29 to follow the Nemotron-last rule and needs the Director's OK (red in the handoff).
2026-09-29 (Director, 05:15): the chat chain is Kimi K3 -> GLM 5.3 (NVIDIA) -> DeepSeek V4 Flash -> Qwen 3.8 (Groq) -> Nemotron LAST;
the chat falls to the next option by itself (authorized_fallback), asks each provider which models are available (model_pool.py) and
moves on after about RIU_CHAT_ATTEMPT_TIMEOUT seconds (default 30, times max_tokens/1024, never above 90) on an option that is not the last one (the last
option gets one 90 s budget for all its keys). Keys: NVIDIA 1-3 first, then 4 (pool order in providers.py); failures older than the cooldown are forgotten,
so keys 1-3 are preferred again after a blip. Health is per key AND model, so a dead model does not put keys in cooldown.
Once the time of an option is spent its remaining keys are not tried: the chain moves on at once (seen live: 30 s + 3 x 1 s of useless attempts on
keys 2-4 before this rule). A request error (400/422) is not the model's fault and never cools a model; a busy Router (ROUTER_SATURATED) neither: the limiter is
shared by every option, so a busy Router ends the request at once (503, retry later) instead of waiting 20 s once per option. The time spent waiting for a
free slot is not charged to the option's time limit. Any exception raised by one option (not only RuntimeError) moves the chain on.
"""
from __future__ import annotations

import hashlib
import math
import os
import threading
import time
from datetime import datetime, timezone
from typing import Any, Callable, Iterable, Mapping

from . import providers as prov

NO_FAILOVER = {400, 404, 410, 422}
PEAK_WINDOWS_UTC = ((1, 4), (6, 10))  # DeepSeek peak, verified in "Banco de claves/router_policy/peak.py" (source: DeepSeek docs)


class Saturated(RuntimeError):
    pass


class AllKeysFailed(RuntimeError):
    pass


class RouteFailed(RuntimeError):
    def __init__(self, message: str, trace: list[str]) -> None:
        super().__init__(message)
        self.trace = trace


def is_peak_utc(dt: datetime, holidays: Iterable[Any] = ()) -> bool:
    utc = dt.astimezone(timezone.utc)
    if utc.weekday() >= 5 or utc.date() in set(holidays):
        return False
    return any(start <= utc.hour < end for start, end in PEAK_WINDOWS_UTC)


def key_id(provider: str, key: str | None, model: str = "") -> str:
    """Health id of a key; with `model` the id is per (key, model): a model that times out must not put a healthy key in cooldown."""
    return provider + ":" + hashlib.sha256((key or "").encode()).hexdigest()[:8] + ("|" + model if model else "")


class CircuitBreaker:
    """Opens after `threshold` failures inside one `cooldown` window; lets one probe through after `cooldown` seconds.

    Failures older than `cooldown` seconds are forgiven (a blip must not demote a key for ever: keys 1-3 are the priority, 4 the spare).
    Half-open: after `cooldown` seconds callers are let through again and the first failure re-opens it (the single-probe rule of the chat lives in
    model_pool.py, not here)."""

    def __init__(self, threshold: int = 3, cooldown: float = 120.0, clock: Callable[[], float] = time.monotonic) -> None:
        self.threshold, self.cooldown, self.clock = threshold, cooldown, clock
        self._state: dict[str, list[float]] = {}  # kid -> [failures, time it opened (0 = closed), time of the last failure]
        self._lock = threading.Lock()

    def _stale(self, st: list[float]) -> bool:
        return st[0] < self.threshold and st[2] > 0 and self.clock() - st[2] >= self.cooldown

    def allow(self, kid: str) -> bool:
        with self._lock:
            st = self._state.get(kid, [0, 0.0, 0.0])
            if st[0] < self.threshold:
                return True
            if self.clock() - st[1] >= self.cooldown:
                self._state[kid] = [self.threshold - 1, st[1], self.clock()]  # half-open: the next failure re-opens it
                return True
            return False

    def ok(self, kid: str) -> None:
        with self._lock:
            self._state.pop(kid, None)

    def fail(self, kid: str) -> None:
        with self._lock:
            st = self._state.get(kid, [0, 0.0, 0.0])
            fails = (0 if self._stale(st) else st[0]) + 1
            now = self.clock()
            self._state[kid] = [fails, now if fails >= self.threshold else 0.0, now]

    def fails(self, kid: str) -> int:
        """Recent failures (used to put the healthiest key first)."""
        st = self._state.get(kid)
        return 0 if st is None or self._stale(st) else int(st[0])


class AdaptiveLimiter:
    """Concurrency slots that grow tier by tier (default 3 -> 10) when requests wait, and refuse once saturated."""

    def __init__(self, tiers: tuple[int, ...] = (3, 10), expand_after: float = 5.0, refuse_after: float = 20.0,
                 clock: Callable[[], float] = time.monotonic) -> None:
        self.tiers, self.expand_after, self.refuse_after, self.clock = tiers, expand_after, refuse_after, clock
        self._cv = threading.Condition()
        self._inflight = 0
        self.tier = 0

    def acquire(self) -> None:
        start = self.clock()
        with self._cv:
            while True:
                if self._inflight < self.tiers[self.tier]:
                    self._inflight += 1
                    return
                waited = self.clock() - start
                if waited >= self.refuse_after:
                    raise Saturated("ROUTER_SATURATED")
                if waited >= self.expand_after and self.tier < len(self.tiers) - 1:
                    self.tier += 1
                    continue
                self._cv.wait(timeout=0.02)

    def release(self) -> None:
        with self._cv:
            self._inflight -= 1
            if self._inflight == 0:
                self.tier = 0
            self._cv.notify_all()


class Router:
    def __init__(self, breaker: CircuitBreaker | None = None, limiter: AdaptiveLimiter | None = None) -> None:
        self.breaker = breaker or CircuitBreaker()
        self.limiter = limiter or AdaptiveLimiter()
        self.latency: dict[str, float] = {}

    def _ordered(self, provider: str, keys: list[str | None], model: str = "") -> list[str | None]:
        allowed = [k for k in keys if self.breaker.allow(key_id(provider, k, model))]
        return sorted(allowed, key=lambda k: self.breaker.fails(key_id(provider, k, model)))  # stable: healthiest first

    def execute(self, provider: str, keys: list[str | None], model: str, messages: list[dict[str, str]], max_tokens: int,
                temperature: float | None, chat_fn: Callable[..., dict[str, Any]], errbox: dict[str, str] | None = None) -> dict[str, Any]:
        queued = time.monotonic()
        try:
            self.limiter.acquire()
        except Saturated:
            if errbox is not None:
                errbox["e"] = "ROUTER_SATURATED"  # core.call_via_router re-raises this text: run_policy must see that the Router was busy, not the model dead
            raise
        waited, token = time.monotonic() - queued, None
        option_deadline = prov.ATTEMPT_DEADLINE.get()
        if option_deadline is not None and waited > 0:
            token = prov.ATTEMPT_DEADLINE.set(option_deadline + waited)  # the wait for a free slot is not the model's time: a healthy model must not time out because of the queue
        try:
            ordered = self._ordered(provider, keys, model)
            if not ordered:
                if errbox is not None:
                    errbox["e"] = "ALL_KEYS_IN_COOLDOWN"
                raise AllKeysFailed("ALL_KEYS_IN_COOLDOWN")
            last: Exception | None = None
            for key in ordered:
                deadline = prov.ATTEMPT_DEADLINE.get()
                if last is not None and deadline is not None and time.monotonic() >= deadline:
                    break  # time of this chain option is spent: the other keys are left untouched (no 1 s attempts marked as failures)
                kid, t0 = key_id(provider, key, model), time.monotonic()
                try:
                    out = chat_fn(provider, key, model, messages, max_tokens, temperature=temperature)
                    self.breaker.ok(kid)
                    self.latency[provider + "/" + model] = 0.7 * self.latency.get(provider + "/" + model, time.monotonic() - t0) + 0.3 * (time.monotonic() - t0)
                    return out
                except Exception as exc:  # noqa: BLE001 - anything from a provider counts against that key
                    last = exc
                    if errbox is not None:
                        errbox["e"] = str(exc)
                    status = getattr(exc, "status", None)
                    if status in NO_FAILOVER:
                        raise
                    self.breaker.fail(kid)
            raise AllKeysFailed(str(last))
        finally:
            self.limiter.release()
            if token is not None:
                prov.ATTEMPT_DEADLINE.reset(token)


ROUTER = Router()

# --- policy: chains per group -----------------------------------------------------------------------------
MINIMAX = {"provider": "hf", "model": "MiniMaxAI/MiniMax-M3"}
DEEPSEEK_FLASH = {"provider": "hf", "model": "deepseek-ai/DeepSeek-V4-Flash", "deepseek": True}
NEMOTRON = {"provider": "nvidia", "model": "nvidia/nemotron-3-super-120b-a12b"}
# Ids verified live 2026-09-29 (run 36543892304): NVIDIA kimi-k3 200 in 0.8 s, glm-5.3 200 in 1.3 s (there is no plain glm-5);
# Groq qwen/qwen3.8-27b is served. z-ai/glm-5.3-flash and deepseek-ai/deepseek-v4.1-flash timed out on NVIDIA in that test (could be a cold start:
# UNCONFIRMED): NOT used until they are tested again.
KIMI_K3 = {"provider": "nvidia", "model": "moonshotai/kimi-k3"}
GLM_53 = {"provider": "nvidia", "model": "z-ai/glm-5.3"}
QWEN_GROQ = {"provider": "groq", "model": "qwen/qwen3.8-27b"}

DEFAULT_POLICY: dict[str, dict[str, Any]] = {
    "default": {"authorized_fallback": True, "chain": [KIMI_K3, GLM_53, DEEPSEEK_FLASH, QWEN_GROQ, NEMOTRON]},
    "code": {"authorized_fallback": True, "chain": [MINIMAX, NEMOTRON]},
    "minor": {"authorized_fallback": True, "peak_only_minimax": True, "chain": [DEEPSEEK_FLASH, NEMOTRON, MINIMAX]},
    "g2": {"authorized_fallback": True, "chain": [KIMI_K3, GLM_53,
                                                   {"provider": "groq", "model": "env:RIU_G2_GROQ_MODEL"},
                                                   {"provider": "local", "model": "env:RIU_G2_LOCAL_MODEL"},
                                                   DEEPSEEK_FLASH, NEMOTRON]},
}


def resolve_chain(group: str, now: datetime, env: Mapping[str, str] | None = None) -> tuple[list[dict[str, Any]], list[str]]:
    env = os.environ if env is None else env
    policy = DEFAULT_POLICY.get(group) or DEFAULT_POLICY["default"]
    peak, skipped, chain = is_peak_utc(now), [], []
    entries = [dict(e) for e in policy["chain"]]
    if peak and policy.get("peak_only_minimax"):
        entries = [e for e in entries if "minimax" in e["model"].lower()]
        skipped.append("PEAK_ONLY_MINIMAX")
    for e in entries:
        if e.get("deepseek") and peak:
            skipped.append(f"{e['model']}:PEAK_HOUR")
            continue
        model = e["model"]
        if model.startswith("env:"):
            model = env.get(model[4:], "")
            if not model:
                skipped.append(f"{e['provider']}:NO_MODEL_CONFIGURED")
                continue
        if not prov.configured(e["provider"]):
            skipped.append(f"{e['provider']}:NOT_CONFIGURED")
            continue
        chain.append({"provider": e["provider"], "model": model})
    return chain, skipped


REQUEST_ERRORS = ("PROVIDER_ERROR:400:", "PROVIDER_ERROR:422:")  # the request is the problem, not the model: never cool a model for these


def attempt_timeout_s() -> float:
    """Seconds one NON-last option of a chain may take before the chat moves on (RIU_CHAT_ATTEMPT_TIMEOUT, default 30; <= 0 = no limit).
    Text that is not a finite number (abc, nan, inf) falls back to 30: a typo must neither break the chat nor silently remove the limit."""
    try:
        value = float(os.getenv("RIU_CHAT_ATTEMPT_TIMEOUT") or 30)
    except ValueError:
        return 30.0
    return value if math.isfinite(value) else 30.0


def run_policy(group: str, messages: list[dict[str, str]], max_tokens: int, *, temperature: float | None = None,
               now: datetime | None = None, call: Callable[..., dict[str, Any]], env: Mapping[str, str] | None = None,
               pool: Any = None, attempt_timeout: float | None = None) -> dict[str, Any]:
    """Run one request through the group's chain. `call(provider, key, model, messages, max_tokens, temperature)` does one route.

    `pool` (model_pool.ModelPool, optional) filters options the provider does not list or that failed recently and learns from each
    result; it is ignored for groups without authorized fallback (skipping an option there would be a silent fallback).
    Every option except the last gets a time limit so a slow model never blocks the chat; the last one gets one full provider budget (90 s)
    for ALL its keys together. The limit grows with the answer size (x max_tokens / 1024, never below the base) and never exceeds 90 s;
    <= 0 means no limit at all. A request error (400/422) or a busy Router does not cool a model (see REQUEST_ERRORS).
    """
    policy = DEFAULT_POLICY.get(group) or DEFAULT_POLICY["default"]
    chain, trace = resolve_chain(group, now or datetime.now(timezone.utc), env)
    if not chain:
        raise RouteFailed("ROUTER_NO_ROUTE_AVAILABLE", trace)
    use_pool = pool if (pool is not None and policy["authorized_fallback"]) else None
    leased: list[tuple[str, str, float]] = []  # probe leases this request took (given back below when the model was never really tried)
    settled: set[tuple[str, str]] = set()  # options whose result was written to the pool (mark_ok / mark_bad)
    if use_pool is not None:
        kept, skipped = use_pool.filter(chain, probe=True, leased=leased)  # a real request: may take the single probe lease of a model whose cooldown ended
        trace.extend(skipped)
        if kept:
            chain = kept
        else:
            trace.append("POOL_EMPTY_TRY_ALL")  # never leave the chat without a route because of the pool
    base = attempt_timeout_s() if attempt_timeout is None else attempt_timeout
    limit = min(prov.CHAT_TIMEOUT, base * max(1.0, max_tokens / 1024)) if base > 0 else 0.0
    try:
        for i, entry in enumerate(chain):
            if i > 0 and not policy["authorized_fallback"]:
                trace.append("FALLBACK_NOT_AUTHORIZED")
                raise RouteFailed("NEEDS_DIRECTOR_AUTH:" + trace[-2], trace)
            keys = prov.env_keys(entry["provider"]) or [None]
            is_last = i == len(chain) - 1
            budget = 0.0 if limit <= 0 else (prov.CHAT_TIMEOUT if is_last else limit)
            token = prov.ATTEMPT_DEADLINE.set(time.monotonic() + budget if budget > 0 else None)
            try:
                out = call(entry["provider"], keys[0], entry["model"], messages, max_tokens, temperature)
                if use_pool is not None:
                    use_pool.mark_ok(entry["provider"], entry["model"])
                    settled.add((entry["provider"], entry["model"]))
                return {**out, "route": {**entry, "attempt": i + 1}, "trace": trace}
            except Exception as exc:  # noqa: BLE001 - whatever one option raises, the chain moves on (only RuntimeError was caught before)
                text = str(exc) if isinstance(exc, RuntimeError) else f"{type(exc).__name__}:{exc}"
                if isinstance(exc, Saturated) or "ROUTER_SATURATED" in text:
                    # The limiter is shared by every option: trying the next one would wait another refuse_after (20 s) each. Stop now, the model is not dead.
                    trace.append(f"{entry['provider']}/{entry['model']}:ROUTER_SATURATED")
                    raise RouteFailed("ROUTER_SATURATED", trace) from exc
                if use_pool is not None and not text.startswith(REQUEST_ERRORS):
                    use_pool.mark_bad(entry["provider"], entry["model"], text)  # a bad request is not a dead model
                    settled.add((entry["provider"], entry["model"]))
                trace.append(f"{entry['provider']}/{entry['model']}:{text[:80]}")
            finally:
                prov.ATTEMPT_DEADLINE.reset(token)
        raise RouteFailed("ROUTER_ALL_ROUTES_FAILED", trace)
    finally:
        if use_pool is not None:
            for provider, model, until in leased:
                if (provider, model) not in settled:
                    use_pool.release(provider, model, until)  # never tried, or ended without a verdict: the next request may probe it at once
