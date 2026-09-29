"""Model pool: which models each provider says are available, and which ones stopped answering (stdlib only).

Director 2026-09-29, 04:41 (verbatim, spelling as written): "El router debe pedir una lista de modelos disponibles así si si por algun motivo no
responde el modelo aunque tenga latencia es mejor así no se bloques y ya el router sabe la la prioridad de cuáles modelos darle prioridad".
Confirmed at 05:15 (verbatim): "Pero igual el router debe pedir a la api repuesta de modelos disponibles".
The PRIORITY is the chain of each group in resilience.DEFAULT_POLICY; this pool only says, right now, which
options of that chain are worth trying:
  * NOT_LISTED  the provider answered its /models list and the model is not there  -> skipped (cheap, no tokens spent).
  * COOLING     the model failed / timed out recently                              -> skipped for `cooldown` seconds.
    When the cooldown ends ONE request probes the model (a lease of PROBE_LEASE seconds); the others keep skipping it until that probe
    answers (mark_ok) or fails (mark_bad, new cooldown) or the lease runs out. Without this every waiting request would hit a dead model at once.
  * Unknown list (provider down, no key, empty list, or a provider whose ids are not checked) -> the model is TRIED anyway.
    (asking costs at most LIST_TIMEOUT = 6 s once per provider, then the answer is cached 5 min, or 60 s when unknown)
If every option is filtered out the caller tries the whole chain (a pool can never leave the chat without a route).
Health is per (provider, model): a dead model never puts a healthy key in cooldown (see resilience.key_id).
No network happens at import time or in `snapshot()`; `listed()` / `refresh()` do one short GET per provider and cache it.
Pending (marked red in the handoff): auto-discovery by model family when a provider renames an id (glm-5 -> glm-5.3).
"""
from __future__ import annotations

import math
import os
import threading
import time
from typing import Any, Callable, Iterable

from . import providers as prov

# Providers whose /models ids are the same ids used in the chains (verified live 2026-09-29: NVIDIA and Groq).
# hf (router.huggingface.co) is left out on purpose: its ids are checked by the certified gate (core.hf_gate), not by this list.
LISTABLE = ("nvidia", "groq")
LIST_TIMEOUT = 6.0
LIST_TTL = 300.0
UNKNOWN_RETRY = 60.0  # after a failed list, do not ask again for this long (the chat must not wait on it every turn)
MAX_KEYS_TRIED = 2
DEFAULT_COOLDOWN = 120.0
PROBE_LEASE = 30.0  # after a cooldown ends, this long only ONE request may probe the model (see cooling(..., probe=True))


def env_cooldown() -> float:
    """RIU_MODEL_COOLDOWN in seconds; a value that is not a finite number >= 0 falls back to 120 (a typo in an env var must not break the chat)."""
    try:
        value = float(os.getenv("RIU_MODEL_COOLDOWN") or DEFAULT_COOLDOWN)
    except ValueError:
        return DEFAULT_COOLDOWN
    return value if math.isfinite(value) and value >= 0 else DEFAULT_COOLDOWN


def _default_fetch(provider: str, key: str | None) -> list[str]:
    return prov.list_models(provider, key, fetch=lambda url, k: prov._http("GET", url, k, None, LIST_TIMEOUT))


class ModelPool:
    def __init__(self, fetch: Callable[[str, str | None], Iterable[str]] | None = None,
                 clock: Callable[[], float] = time.monotonic, cooldown: float | None = None,
                 listable: Iterable[str] = LISTABLE) -> None:
        self._fetch = fetch or _default_fetch
        self.clock = clock
        self.cooldown = env_cooldown() if cooldown is None else cooldown
        self.listable = tuple(listable)
        self._bad: dict[tuple[str, str], tuple[float, str]] = {}
        self._listed: dict[str, tuple[float, frozenset[str] | None]] = {}
        self._lock = threading.Lock()

    # --- what the provider lists -----------------------------------------------------------------
    def listed(self, provider: str, *, force: bool = False) -> frozenset[str] | None:
        """Model ids the provider lists right now, or None when unknown (never raises, never blocks longer than LIST_TIMEOUT x keys)."""
        if provider not in self.listable:
            return None
        now = self.clock()
        with self._lock:
            hit = self._listed.get(provider)
            if hit and now < hit[0] and not force:
                return hit[1]
        if force:  # providers.list_models keeps its own 5-minute cache: drop it so "ask again" really asks again
            for stale in [k for k in prov._models_cache if k[0] == provider]:
                prov._models_cache.pop(stale, None)
        ids: frozenset[str] | None = None
        for key in prov.env_keys(provider)[:MAX_KEYS_TRIED]:
            try:
                found = frozenset(self._fetch(provider, key))
            except Exception as exc:  # noqa: BLE001 - a list that cannot be read means "unknown", not "empty"
                if not isinstance(getattr(exc, "status", None), int):
                    break  # timeout / no connection (not an HTTP answer): the provider is slow or down, another key will not help (and costs LIST_TIMEOUT again)
                continue  # HTTP error (bad key, 429...): the next key may work
            if found:
                ids = found
                break
        with self._lock:
            self._listed[provider] = (now + (LIST_TTL if ids is not None else UNKNOWN_RETRY), ids)
        return ids

    # --- what stopped answering ------------------------------------------------------------------
    def cooling(self, provider: str, model: str, *, probe: bool = False) -> bool:
        """True while the model must be skipped. With probe=True the FIRST caller after the cooldown gets False and takes a PROBE_LEASE-second
        lease (the others still get True); mark_ok / mark_bad settle it. probe=False never changes anything (used for reports)."""
        with self._lock:
            hit = self._bad.get((provider, model))
            if not hit:
                return False
            now = self.clock()
            if now < hit[0]:
                return True
            if probe:
                self._bad[(provider, model)] = (now + PROBE_LEASE, hit[1])
            return False

    def mark_bad(self, provider: str, model: str, why: str = "") -> None:
        with self._lock:
            self._bad[(provider, model)] = (self.clock() + self.cooldown, why[:80])

    def mark_ok(self, provider: str, model: str) -> None:
        with self._lock:
            self._bad.pop((provider, model), None)

    # --- use --------------------------------------------------------------------------------------
    def filter(self, chain: list[dict[str, Any]], *, probe: bool = False) -> tuple[list[dict[str, Any]], list[str]]:
        """Keep the chain order; drop options that are cooling or not listed. Returns (kept, trace lines).
        probe=True is for a real request (it may take the single probe lease of a model whose cooldown ended); reports use the default."""
        kept: list[dict[str, Any]] = []
        skipped: list[str] = []
        for entry in chain:
            provider, model = entry["provider"], entry["model"]
            if self.cooling(provider, model, probe=probe):
                skipped.append(f"{provider}/{model}:COOLING")
                continue
            ids = self.listed(provider)
            if ids is not None and model not in ids:
                skipped.append(f"{provider}/{model}:NOT_LISTED")
                continue
            kept.append(entry)
        return kept, skipped

    def refresh(self, providers: Iterable[str] | None = None) -> dict[str, Any]:
        """Ask the providers again (network). Returns {provider: {"listed": n | None, "configured": bool}}."""
        out: dict[str, Any] = {}
        for provider in (providers or self.listable):
            ids = self.listed(provider, force=True) if prov.configured(provider) else None
            out[provider] = {"configured": prov.configured(provider), "listed": None if ids is None else len(ids)}
        return out

    def snapshot(self) -> dict[str, Any]:
        """What is known right now. No network."""
        now = self.clock()
        with self._lock:
            listed = {p: (None if ids is None else len(ids)) for p, (until, ids) in self._listed.items()}
            cooling = {f"{p}/{m}": {"seconds_left": round(until - now, 1), "why": why}
                       for (p, m), (until, why) in self._bad.items() if until > now}
        return {"listable": list(self.listable), "listed": listed, "cooling": cooling, "cooldown_s": self.cooldown}


POOL = ModelPool()
