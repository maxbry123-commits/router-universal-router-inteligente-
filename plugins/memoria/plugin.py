"""memoria: plugin de almacenamiento y memoria del sistema RIU.
Acciones: status, save, load, search, list.
Contrato identico a plugins/connectivity y plugins/deepseek_harness:
handle(action, payload) -> dict con status ok/degraded.
Integracion: deepseek_harness y puente_chat pueden llamar save/load
para persistir contexto entre pasos del bucle.
Env: RIU_MEMORIA_DIR (def ./state/memoria).
"""
from __future__ import annotations

import json
import os
import re
import time
from pathlib import Path
from typing import Any

_SAFE_KEY = re.compile(r"^[A-Za-z0-9_.-]{1,120}$")


def _dir() -> Path:
    d = Path(os.getenv("RIU_MEMORIA_DIR") or "./state/memoria")
    d.mkdir(parents=True, exist_ok=True)
    return d


def _degraded(reason: str) -> dict[str, Any]:
    return {"status": "degraded", "reason": reason}


def _valid_key(key: Any) -> bool:
    return isinstance(key, str) and bool(_SAFE_KEY.match(key)) and ".." not in key


def handle(action: str, payload: dict[str, Any] | None) -> dict[str, Any]:
    payload = payload or {}
    base = _dir()

    if action == "status":
        return {
            "status": "ok",
            "configured": True,
            "memoria_dir": str(base),
            "total_entries": len(list(base.glob("*.json"))),
        }

    if action == "save":
        key = payload.get("key")
        data = payload.get("data")
        if not _valid_key(key):
            return _degraded("save: key invalida (permitido [A-Za-z0-9_.-], max 120)")
        if data is None:
            return _degraded("save: falta 'data'")
        entry = {
            "key": key,
            "data": data,
            "timestamp": time.time(),
            "iso": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }
        path = base / f"{key}.json"
        tmp = path.with_suffix(".tmp")
        try:
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(entry, f, indent=2, ensure_ascii=False)
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp, path)
            return {"status": "ok", "key": key, "path": str(path)}
        except Exception as exc:  # noqa: BLE001
            return _degraded("save: " + type(exc).__name__)

    if action == "load":
        key = payload.get("key")
        if not _valid_key(key):
            return _degraded("load: key invalida")
        path = base / f"{key}.json"
        if not path.exists():
            return {"status": "ok", "key": key, "data": None, "exists": False}
        try:
            with open(path, "r", encoding="utf-8") as f:
                entry = json.load(f)
            return {"status": "ok", "key": key, "data": entry.get("data"),
                    "exists": True, "timestamp": entry.get("timestamp")}
        except Exception as exc:  # noqa: BLE001
            return _degraded("load: " + type(exc).__name__)

    if action == "search":
        query = str(payload.get("query", "")).lower()
        if not query:
            return _degraded("search: falta 'query'")
        limit = int(payload.get("limit", 20))
        results = []
        for path in sorted(base.glob("*.json")):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    entry = json.load(f)
                key = str(entry.get("key", ""))
                body = json.dumps(entry.get("data", {}), ensure_ascii=False).lower()
                if query in key.lower() or query in body:
                    results.append({
                        "key": key,
                        "timestamp": entry.get("timestamp"),
                        "preview": body[:200],
                    })
                    if len(results) >= limit:
                        break
            except Exception:  # noqa: BLE001
                continue
        return {"status": "ok", "query": query, "results": results,
                "count": len(results)}

    if action == "list":
        keys = []
        for path in base.glob("*.json"):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    entry = json.load(f)
                keys.append({"key": entry.get("key"),
                             "timestamp": entry.get("timestamp")})
            except Exception:  # noqa: BLE001
                continue
        keys.sort(key=lambda x: x.get("timestamp") or 0, reverse=True)
        return {"status": "ok", "keys": keys, "count": len(keys)}

    return _degraded("accion desconocida")
