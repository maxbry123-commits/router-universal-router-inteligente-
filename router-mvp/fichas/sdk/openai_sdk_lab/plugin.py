"""Plugin openai_sdk_lab: laboratorio TEMPORAL de pruebas del SDK de OpenAI dentro del Router (no toca el Router).
Entra por el Plugin Host (health_action = status). Las claves NO estan en el repo: salen del banco secreto ya abierto en
memoria (vault_hook.provider_keys openai). Motor: Laboratorio Code de pruebas.py (carpeta del laboratorio). status corre las
pruebas (maximo 1 vez cada 10 min), devuelve un resumen sin claves y sube el detalle saneado a RESULTADOS-OPENAI-SDK.json."""
from __future__ import annotations

import base64
import importlib.util
import json
import os
import re
import subprocess
import sys
import threading
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

LAB_DIR = "📂 laboratorio pruebas api sdk"
ENGINE = "Laboratorio Code de pruebas.py"
RESULTS = "RESULTADOS-OPENAI-SDK.json"
REPO = "maxbry123-commits/router-universal-router-inteligente-"
TTL_OK = 600
TTL_BLOCKED = 30

_lock = threading.Lock()
_state: dict[str, Any] = {"t": 0.0, "ttl": 0, "out": None, "running": False}
_SECRET = re.compile(r"(sk-[A-Za-z0-9_-]{8,}|gh[ps]_[A-Za-z0-9]{10,}|hf_[A-Za-z0-9]{10,})")


def _engine() -> Any:
    path = Path(__file__).resolve().parents[3] / LAB_DIR / ENGINE
    spec = importlib.util.spec_from_file_location("lab_openai_engine", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _ensure_sdk() -> None:
    try:
        import openai  # noqa: F401
    except ImportError:
        subprocess.run([sys.executable, "-m", "pip", "install", "-q", "openai"], check=False, timeout=100, capture_output=True)


def _rows(obj: Any) -> list[dict[str, Any]]:
    if isinstance(obj, list) and obj and all(isinstance(x, dict) and "key_index" in x for x in obj):
        return obj
    if isinstance(obj, dict):
        for value in obj.values():
            found = _rows(value)
            if found:
                return found
    return []


def _why(row: dict[str, Any]) -> str:
    for part in ("responses", "models"):
        blk = row.get(part) or {}
        if not blk.get("ok"):
            return str(blk.get("status_code") or blk.get("error_type") or "?")
    return "?"


def _summarize(res: Any) -> dict[str, Any]:
    rows = _rows(res)
    if not rows:
        why = res.get("reason") if isinstance(res, dict) else None
        return {"status": "degraded", "reason": "sin resultados: " + str(why or "desconocido")[:120]}
    good = [r for r in rows if (r.get("models") or {}).get("ok") and (r.get("responses") or {}).get("ok")]
    me_ok = sum(1 for r in rows if (r.get("me") or {}).get("ok"))
    bad = [str(r.get("key_index")) + ":" + _why(r) for r in rows if r not in good]
    text = "PASS %d/%d claves (models+responses); me %d/%d informativo" % (len(good), len(rows), me_ok, len(rows))
    if bad:
        text += "; FALLAN " + ",".join(bad)[:110]
    return {"status": "ok" if len(good) == len(rows) else "degraded", "reason": text}


def _clean(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {k: _clean(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_clean(v) for v in obj]
    if isinstance(obj, str):
        return _SECRET.sub("[REDACTADO]", obj)
    return obj


def _push(doc: dict[str, Any]) -> str:
    tok = os.environ.get("GITHUB_TOKEN")
    if not tok:
        return "sin GITHUB_TOKEN"
    api = "https://api.github.com/repos/" + REPO + "/contents/" + urllib.parse.quote(LAB_DIR + "/" + RESULTS)
    hdr = {"Authorization": "Bearer " + tok, "User-Agent": "riu-lab", "Accept": "application/vnd.github+json"}
    sha = None
    try:
        with urllib.request.urlopen(urllib.request.Request(api, headers=hdr), timeout=20) as r:
            sha = json.loads(r.read()).get("sha")
    except Exception:  # noqa: BLE001
        pass
    body = {"message": "lab: resultados OpenAI SDK (plugin openai_sdk_lab) [skip ci]", "branch": "main",
            "content": base64.b64encode(json.dumps(doc, ensure_ascii=False, indent=2).encode()).decode()}
    if sha:
        body["sha"] = sha
    req = urllib.request.Request(api, data=json.dumps(body).encode(), headers={**hdr, "Content-Type": "application/json"}, method="PUT")
    try:
        with urllib.request.urlopen(req, timeout=25):
            return "detalle subido al repo"
    except Exception as exc:  # noqa: BLE001
        return "no se pudo subir: " + type(exc).__name__


def _work() -> None:
    try:
        _ensure_sdk()
        res = _engine().run_all()
        out = _summarize(res)
        if _rows(res):
            ttl = TTL_OK
            doc = _clean({"fecha": datetime.now(timezone.utc).isoformat(timespec="seconds"), "plugin": "openai_sdk_lab", "resumen": out, "resultado": res})
            out = {"status": out["status"], "reason": (out["reason"] + " | " + _push(doc))[:280]}
        else:
            ttl = TTL_BLOCKED
    except Exception as exc:  # noqa: BLE001
        out, ttl = {"status": "degraded", "reason": "fallo del laboratorio: " + type(exc).__name__}, TTL_BLOCKED
    with _lock:
        _state.update(t=time.time(), ttl=ttl, out=out, running=False)


def handle(action: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    if action not in ("status", "invoke"):
        return {"status": "error", "reason": "accion desconocida: " + str(action)}
    force = action == "invoke" or bool((payload or {}).get("force"))
    with _lock:
        if _state["out"] is not None and not force and time.time() - _state["t"] < _state["ttl"]:
            return _state["out"]
        if not _state["running"]:
            _state["running"] = True
            threading.Thread(target=_work, daemon=True, name="openai_sdk_lab").start()
    end = time.time() + 105
    while time.time() < end:
        with _lock:
            if not _state["running"]:
                return _state["out"]
        time.sleep(0.5)
    return {"status": "degraded", "reason": "corriendo; consulta de nuevo en 1 minuto"}
