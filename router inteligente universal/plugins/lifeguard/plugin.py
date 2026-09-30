"""lifeguard: plugin del salvavidas. Reutiliza agents-yaiwes/common/guardian.py (no duplica logica).

Acciones: status (solo lectura), plan (que haria), relaunch (DRY-RUN por defecto; dry_run=false para actuar).
payload: {"kind": "guardian"|"router" (def. guardian), "dry_run": bool (def. true), "force": bool (def. false)}
Sin force, relaunch solo actua si el plan lo pide. Tokens solo por env.
"""
from __future__ import annotations

import importlib.util
import os
import sys
import threading
from pathlib import Path
from typing import Any

ACTIONS = ("status", "plan", "relaunch")
_G_PATH = Path(os.getenv("LIFEGUARD_GUARDIAN_PATH", str(Path(__file__).resolve().parents[2] / "agents-yaiwes" / "common" / "guardian.py")))
_mod: Any = None
_state: Any = None
_watch: "threading.Thread | None" = None


def _guardian() -> Any:
    global _mod
    if _mod is None:
        spec = importlib.util.spec_from_file_location("riu_guardian", _G_PATH)
        _mod = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = _mod
        spec.loader.exec_module(_mod)  # type: ignore[union-attr]
    return _mod


def _ctx(payload: dict) -> tuple:
    """(g, cfg, api, http, state). Los tests inyectan payload['_api'] / payload['_http']."""
    global _state
    g = _guardian()
    cfg = g.Config.from_env()
    if _state is None:
        _state = g.State(cfg.state_path)
    api = payload.get("_api") or (g.hf_api(cfg) if cfg.hf_token else None)
    return g, cfg, api, payload.get("_http") or g.default_http, _state


def handle(action: str, payload: "dict | None" = None) -> dict:
    payload = payload or {}
    if action not in ACTIONS:
        return {"ok": False, "error": f"accion desconocida: {action}", "allowed": list(ACTIONS)}
    kind = payload.get("kind", "guardian")
    if kind not in ("router", "guardian"):
        return {"ok": False, "error": "kind debe ser router o guardian"}
    g, cfg, api, http, state = _ctx(payload)
    if api is None:
        return {"ok": False, "error": "falta HF_CONTROL_JOBS_TOKEN (solo por env)"}
    try:
        if action == "status":
            return {"ok": True, "router": g.gather("router", cfg, api, http, state, g.time.time()),
                    "guardian": g.gather("guardian", cfg, api, http, state, g.time.time()), "dry_run_default": True}
        info = g.gather(kind, cfg, api, http, state, g.time.time(), health_tries=3)
        if info.get("kind") == "router" and not info.get("health_ok"):
            info["fails"] = cfg.fail_limit  # 3 intentos rapidos fallidos
        decision = g.decide(info, cfg)
        if action == "plan":
            return {"ok": True, "info": info, "decision": decision, "would_run": g.describe_spec(g.build_spec(kind, cfg))}
        dry = payload.get("dry_run", True) is not False
        if decision["action"] != "relaunch" and not payload.get("force"):
            return {"ok": True, "skipped": True, "decision": decision, "info": info}
        return g.relaunch(kind, cfg, api, http, state, decision["reason"] if decision["action"] == "relaunch" else "force", dry_run=dry)
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "error": str(e)[:200]}


def start_peer_watch() -> bool:
    """Opcional: hilo en el Router que vigila al guardian cada GUARDIAN_INTERVAL (respeta GUARDIAN_DRY_RUN, def. 1)."""
    global _watch
    if _watch and _watch.is_alive():
        return False
    g = _guardian()
    cfg = g.Config.from_env()
    if not cfg.hf_token:
        return False
    _watch = threading.Thread(target=g.run_forever, args=(("guardian",), cfg), daemon=True, name="lifeguard-peer-watch")
    _watch.start()
    return True
