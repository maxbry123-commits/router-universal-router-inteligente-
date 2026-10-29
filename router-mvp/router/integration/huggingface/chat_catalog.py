"""Selector catalog for the RIU chat MVP (stdlib only).

Model ids come ONLY from model_registry.json, the live Hugging Face router
catalog, or HUB_VERIFIED_CANDIDATES. Nothing is invented. Being selectable
here never promotes a model to READY: certification stays in the registry
(REGISTERED != PROVIDER_LIVE != REMOTE_INFERENCE_AUTHENTICATED_PASS != READY).
"""
from __future__ import annotations

import json
import re
import time
import urllib.request
from pathlib import Path
from typing import Any, Callable, Iterable

_REGISTRY = Path(__file__).with_name("model_registry.json")
CATALOG_URL = "https://router.huggingface.co/v1/models"
CACHE_TTL_SECONDS = 300.0
NEGATIVE_TTL_SECONDS = 30.0

CERTIFIED = "RUNTIME_INFERENCE_VERIFIED"
PROVIDER_LIVE = "PROVIDER_LIVE_VERIFIED"
ROUTER_LIVE = "ROUTER_CATALOG_LIVE"
HUB_ONLY = "HUB_REPO_VERIFIED_PROVIDER_DISCOVERY_PENDING"
PENDING = "REMOTE_PROVIDER_DISCOVERY_PENDING"
LIVE_STATES = frozenset({PROVIDER_LIVE, ROUTER_LIVE})

# Families requested by the Director for the chat selector.
SELECTOR_FAMILIES: tuple[dict[str, str], ...] = (
    {"family": "kimi-k3", "label": "Kimi K3", "pattern": r"kimi[-_ ]?k3"},
    {"family": "minimax", "label": "MiniMax", "pattern": r"minimax[-_ ]?m\d"},
    {"family": "deepseek-v4-flash", "label": "DeepSeek V4 Flash",
     "pattern": r"deepseek[-_ ]?v4(?:\.\d+)?[-_ ]?flash(?!.*vision)"},
    {"family": "deepseek-v4-pro", "label": "DeepSeek V4 Pro", "pattern": r"deepseek[-_ ]?v4(?:\.\d+)?[-_ ]?pro"},
)

# Hub repos that exist (hf_fs search 2026-09-19) but have NO recorded provider
# discovery yet: shown in the selector, never selectable until discovered live.
HUB_VERIFIED_CANDIDATES: dict[str, str] = {
    "MiniMaxAI/MiniMax-M3": "hub public, image-text-to-text, updated 2026-07-23",
    "MiniMaxAI/MiniMax-M2.7": "hub public, text-generation, updated 2026-04-20",
}


def _registry() -> dict[str, Any]:
    return json.loads(_REGISTRY.read_text(encoding="utf-8"))


def family_of(model_id: str) -> dict[str, str] | None:
    for fam in SELECTOR_FAMILIES:
        if re.search(fam["pattern"], model_id, re.I):
            return fam
    return None


def known_models(registry: dict[str, Any] | None = None) -> dict[str, dict[str, Any]]:
    reg = registry if registry is not None else _registry()
    out: dict[str, dict[str, Any]] = {}
    for m in reg.get("remote20_provider_live_verified", {}).get("models", []):
        out[m["model_id"]] = {"state": PROVIDER_LIVE, "providers_live": list(m.get("providers_live", []))}
    for mid in reg.get("runtime_inference_verified_model_ids", []):
        out[mid] = {"state": CERTIFIED, "providers_live": out.get(mid, {}).get("providers_live", [])}
    return out


def discover_catalog_ids(fetch: Callable[[], dict[str, Any]] | None = None, *, timeout: float = 8.0) -> list[str]:
    """Ids currently listed by the HF router catalog. Fail-closed: [] on any error."""
    try:
        if fetch is None:
            with urllib.request.urlopen(CATALOG_URL, timeout=timeout) as resp:  # noqa: S310 fixed https URL
                body = json.loads(resp.read().decode("utf-8"))
        else:
            body = fetch()
        return sorted({d["id"] for d in body.get("data", []) if isinstance(d, dict) and isinstance(d.get("id"), str)})
    except Exception:  # noqa: BLE001 - discovery is best-effort, never a gate by itself
        return []


_cache: dict[str, Any] = {"at": None, "ids": []}


def cached_discovery(*, fetch: Callable[[], dict[str, Any]] | None = None, now: Callable[[], float] = time.monotonic) -> list[str]:
    t = now()
    if _cache["at"] is not None and t - _cache["at"] < CACHE_TTL_SECONDS:
        return list(_cache["ids"])
    ids = discover_catalog_ids(fetch)
    # A failed discovery is remembered only NEGATIVE_TTL_SECONDS so a dead network never slows every request.
    _cache["at"] = t if ids else t - CACHE_TTL_SECONDS + NEGATIVE_TTL_SECONDS
    _cache["ids"] = ids
    return list(ids)


def selectable_live_ids(registry: dict[str, Any] | None = None, discovered: Iterable[str] = ()) -> set[str]:
    """Non-certified ids that may be ATTEMPTED when live provider inference is enabled."""
    ids = {i for i, v in known_models(registry).items() if v["state"] == PROVIDER_LIVE and family_of(i)}
    ids |= {i for i in discovered if family_of(i)}
    return ids


def selector_models(
    *, registry: dict[str, Any] | None = None, discovered: Iterable[str] = (), live_enabled: bool = False
) -> dict[str, Any]:
    known = known_models(registry)
    live_ids = set(discovered)
    rows: list[dict[str, Any]] = []
    for fam in SELECTOR_FAMILIES:
        ids = sorted(i for i in set(known) | live_ids | set(HUB_VERIFIED_CANDIDATES) if (family_of(i) or {}).get("family") == fam["family"])
        if not ids:
            rows.append({"family": fam["family"], "label": fam["label"], "model_id": None, "state": PENDING,
                         "providers_live": [], "certified": False, "selectable": False,
                         "reason": "NO_MODEL_ID_IN_REGISTRY_OR_CATALOG"})
            continue
        for mid in ids:
            if mid in known:
                state, providers = known[mid]["state"], known[mid]["providers_live"]
            elif mid in live_ids:
                state, providers = ROUTER_LIVE, []
            else:
                state, providers = HUB_ONLY, []
            certified = state == CERTIFIED
            selectable = certified or (live_enabled and state in LIVE_STATES)
            reason = "" if selectable else (
                "LIVE_PROVIDER_INFERENCE_DISABLED" if state in LIVE_STATES else "PROVIDER_DISCOVERY_PENDING")
            rows.append({"family": fam["family"], "label": fam["label"], "model_id": mid, "state": state,
                         "providers_live": providers, "certified": certified, "selectable": selectable,
                         "reason": reason})
    for mid in sorted(i for i, v in known.items() if v["state"] == CERTIFIED and not family_of(i)):
        rows.append({"family": "certified", "label": "Certificados (base)", "model_id": mid, "state": CERTIFIED,
                     "providers_live": known[mid]["providers_live"], "certified": True, "selectable": True,
                     "reason": ""})
    return {"live_provider_inference": live_enabled, "models": rows}
