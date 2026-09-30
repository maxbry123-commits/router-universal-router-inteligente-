"""hf_compute: politica de computo por tramos (config.json) sobre el pool de GPT (integration/hf_worker_pool.py).

No reescribe el pool: lo importa perezosamente (POOL.status / POOL.launch / POOL.invoke).
ensure es DRY-RUN salvo payload apply=true (lanzar un worker cuesta dinero).
"""
from __future__ import annotations

import asyncio
import importlib
import inspect
import json
import os
import threading
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

CONFIG_PATH = Path(os.getenv("HF_COMPUTE_CONFIG", str(Path(__file__).with_name("config.json"))))
INVOKE_NAME = "invoke"
ACTIONS = ("status", "ensure", "invoke")


def _http(method, url, headers=None, data=None, timeout=30):
    """HTTP minimo (stdlib). Devuelve (status, bytes). Los tests lo reemplazan por un mock."""
    req = urllib.request.Request(url, data=data, method=method, headers=headers or {})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()
    except Exception as e:  # red caida, DNS, timeout
        return 0, str(e).encode()


def _json(body):
    try:
        return json.loads(body.decode("utf-8", "replace"))
    except ValueError:
        return None


def load_config() -> dict[str, Any]:
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def _pool() -> Any | None:
    try:
        return importlib.import_module("integration.hf_worker_pool").POOL
    except Exception:
        return None


def _num(v: Any) -> float | None:
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def plan(cfg: dict[str, Any], cpu: float | None, ram: float | None, workers: list[dict[str, Any]]) -> dict[str, Any]:
    """Decision pura: que tramo activar segun metricas y workers activos."""
    thr = float(cfg["umbral_pct"])
    vals = [v for v in (cpu, ram) if v is not None]
    if not vals:
        return {"decision": "sin_metricas", "launch": None}
    if max(vals) < thr:
        return {"decision": "ninguna", "launch": None, "umbral_pct": thr}
    _, t16, t32 = cfg["tramos"][:3]
    if not any(w.get("flavor") == t16["flavor"] for w in workers):
        return {"decision": "activar_siguiente", "launch": t16["flavor"], "tramo": t16["id"], "ram_gb": t16["ram_gb"], "umbral_pct": thr}
    if not any(w.get("flavor") == t32["flavor"] for w in workers):
        return {"decision": "saltar_a_32", "launch": t32["flavor"], "tramo": t32["id"], "ram_gb": t32["ram_gb"], "umbral_pct": thr}
    return {"decision": "tope_alcanzado", "launch": None, "umbral_pct": thr}


def _metrics(pool: Any, payload: dict[str, Any]) -> tuple[float | None, float | None, list[dict[str, Any]], dict[str, Any]]:
    st = pool.status() if pool is not None else {}
    cpu = _num(payload.get("cpu_percent", st.get("cpu_percent")))
    ram = _num(payload.get("ram_percent", st.get("ram_percent")))
    return cpu, ram, list(st.get("workers") or []), st


def _probe_users(cfg: dict[str, Any]) -> list[dict[str, Any]]:
    out = []
    for u in cfg.get("usuarios", []):
        base = os.getenv(u.get("url_env", ""), "").strip()
        if not base:
            out.append({"id": u["id"], "activo": None, "motivo": "sin_url_configurada (%s)" % u.get("url_env")})
            continue
        st, _ = _http("GET", base.rstrip("/") + u.get("health_path", "/health"), None, None, 8)
        out.append({"id": u["id"], "activo": 200 <= st < 300, "http_status": st})
    return out


def _run(coro: Any) -> Any:
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)
    box: dict[str, Any] = {}
    t = threading.Thread(target=lambda: box.setdefault("r", asyncio.run(coro)))
    t.start()
    t.join()
    return box.get("r")


def handle(action: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or {}
    try:
        cfg = load_config()
        pool = _pool()
        if action == "status":
            cpu, ram, workers, _ = _metrics(pool, payload)
            return {"status": "ok", "pool_disponible": pool is not None, "tramos": cfg["tramos"], "umbral_pct": cfg["umbral_pct"],
                    "umbral_pool_gpt": os.getenv("HF_AUTOSCALE_THRESHOLD", "85 (defecto GPT)"),
                    "cpu_percent": cpu, "ram_percent": ram, "workers_activos": workers, "usuarios": _probe_users(cfg), "nota_ram": cfg.get("nota_ram")}
        if pool is None:
            return {"status": "error", "error": "integration.hf_worker_pool no disponible"}
        if action == "ensure":
            cpu, ram, workers, _ = _metrics(pool, payload)
            p = plan(cfg, cpu, ram, workers)
            if payload.get("apply") is True and p.get("launch"):
                w = pool.launch(p["launch"], "hf_compute " + p["decision"])
                return {"status": "ok", "applied": True, "plan": p, "worker": w.public() if hasattr(w, "public") else str(w)}
            return {"status": "ok", "applied": False, "dry_run": True, "plan": p}
        if action == "invoke":
            res = getattr(pool, INVOKE_NAME)(payload.get("body") or {})
            return {"status": "ok", "result": _run(res) if inspect.isawaitable(res) else res}
        return {"status": "error", "error": "accion no permitida", "allowed": list(ACTIONS)}
    except Exception as exc:
        return {"status": "error", "error": str(exc)[:300]}
