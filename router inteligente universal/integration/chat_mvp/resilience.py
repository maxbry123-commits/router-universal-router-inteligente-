"""Router resilience for load peaks and provider problems (stdlib only).

Problems seen in real tests (2026-09-20) and the answer to each:
  * NVIDIA heavy models time out when many requests arrive together  -> adaptive concurrency (3 -> 10 slots), then
    ROUTER_SATURATED fast instead of hanging.
  * One NVIDIA key slow / 503 / 402                                   -> circuit breaker per key + healthiest-first order.
  * DeepSeek peak hours (01-04 and 06-10 UTC, Mon-Fri)                -> in peak only MiniMax for code/minor tasks.
  * Provider down or saturated                                        -> fallback chain per group, ONLY where the Director
    authorized it (g2, code, minor). The default group does not fall back: it reports NEEDS_DIRECTOR_AUTH so the brain can ask.
Chains follow the Director's rule for group 2: NVIDIA -> Cerebras -> local API -> DeepSeek V4 Flash.
"""
from __future__ import annotations

import hashlib
import os
import threading
import time
from datetime import datetime, timezone
from typing import Any, Callable, Iterable, Mapping

from . import providers as prov

NO_FAILOVER = {400, 404, 410, 422}
PEAK_WINDOWS_UTC = ((1, 4), (6, 10))  # DeepSeek peak, verified in Chat Mvp/router_policy/peak.py (source: DeepSeek docs)


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


def key_id(provider: str, key: str | None) -> str:
    return provider + ":" + hashlib.sha256((key or "").encode()).hexdigest()[:8]


class CircuitBreaker:
    """Opens after `threshold` consecutive failures; lets one probe through after `cooldown` seconds."""

    def __init__(self, threshold: int = 3, cooldown: float = 120.0, clock: Callable[[], float] = time.monotonic) -> None:
        self.threshold, self.cooldown, self.clock = threshold, cooldown, clock
        self._state: dict[str, list[float]] = {}
        self._lock = threading.Lock()

    def allow(self, kid: str) -> bool:
        with self._lock:
            fails, opened = self._state.get(kid, [0, 0.0])
            if fails < self.threshold:
                return True
            if self.clock() - opened >= self.cooldown:
                self._state[kid] = [self.threshold - 1, opened]  # half-open: the next failure re-opens it
                return True
            return False

    def ok(self, kid: str) -> None:
        with self._lock:
            self._state.pop(kid, None)

    def fail(self, kid: str) -> None:
        with self._lock:
            fails = self._state.get(kid, [0, 0.0])[0] + 1
            self._state[kid] = [fails, self.clock() if fails >= self.threshold else 0.0]

    def fails(self, kid: str) -> int:
        return int(self._state.get(kid, [0, 0.0])[0])


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

    def _ordered(self, provider: str, keys: list[str | None]) -> list[str | None]:
        allowed = [k for k in keys if self.breaker.allow(key_id(provider, k))]
        return sorted(allowed, key=lambda k: self.breaker.fails(key_id(provider, k)))  # stable: healthiest first

    def execute(self, provider: str, keys: list[str | None], model: str, messages: list[dict[str, str]], max_tokens: int,
                temperature: float | None, chat_fn: Callable[..., dict[str, Any]], errbox: dict[str, str] | None = None) -> dict[str, Any]:
        self.limiter.acquire()
        try:
            ordered = self._ordered(provider, keys)
            if not ordered:
                raise AllKeysFailed("ALL_KEYS_IN_COOLDOWN")
            last: Exception | None = None
            for key in ordered:
                kid, t0 = key_id(provider, key), time.monotonic()
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


ROUTER = Router()

# --- policy: chains per group -----------------------------------------------------------------------------
MINIMAX = {"provider": "hf", "model": "MiniMaxAI/MiniMax-M3"}
DEEPSEEK_FLASH = {"provider": "hf", "model": "deepseek-ai/DeepSeek-V4-Flash", "deepseek": True}
NEMOTRON = {"provider": "nvidia", "model": "nvidia/nemotron-3-super-120b-a12b"}

DEFAULT_POLICY: dict[str, dict[str, Any]] = {
    "default": {"authorized_fallback": False, "chain": [NEMOTRON]},
    "code": {"authorized_fallback": True, "chain": [MINIMAX, NEMOTRON]},
    "minor": {"authorized_fallback": True, "peak_only_minimax": True, "chain": [DEEPSEEK_FLASH, NEMOTRON, MINIMAX]},
    "g2": {"authorized_fallback": True, "chain": [NEMOTRON,
                                                   {"provider": "cerebras", "model": "env:RIU_G2_CEREBRAS_MODEL"},
                                                   {"provider": "local", "model": "env:RIU_G2_LOCAL_MODEL"},
                                                   DEEPSEEK_FLASH]},
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


def run_policy(group: str, messages: list[dict[str, str]], max_tokens: int, *, temperature: float | None = None,
               now: datetime | None = None, call: Callable[..., dict[str, Any]], env: Mapping[str, str] | None = None) -> dict[str, Any]:
    """Run one request through the group's chain. `call(provider, key, model, messages, max_tokens, temperature)` does one route."""
    policy = DEFAULT_POLICY.get(group) or DEFAULT_POLICY["default"]
    chain, trace = resolve_chain(group, now or datetime.now(timezone.utc), env)
    if not chain:
        raise RouteFailed("ROUTER_NO_ROUTE_AVAILABLE", trace)
    for i, entry in enumerate(chain):
        if i > 0 and not policy["authorized_fallback"]:
            trace.append("FALLBACK_NOT_AUTHORIZED")
            raise RouteFailed("NEEDS_DIRECTOR_AUTH:" + trace[-2], trace)
        keys = prov.env_keys(entry["provider"]) or [None]
        try:
            out = call(entry["provider"], keys[0], entry["model"], messages, max_tokens, temperature)
            return {**out, "route": {**entry, "attempt": i + 1}, "trace": trace}
        except RuntimeError as exc:
            trace.append(f"{entry['provider']}/{entry['model']}:{str(exc)[:80]}")
    raise RouteFailed("ROUTER_ALL_ROUTES_FAILED", trace)
