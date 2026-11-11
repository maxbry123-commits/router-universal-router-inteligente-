"""
registry_models.py — Generar/verificar registry.json con SHA-256 (Salida 3/3)
Ubicacion: control huggueface/registry_models.py
Rol: Objetivo 3.6 y 3.8. Fill-on-first-run: si sha256 es null, lo calcula y escribe.
"""
import hashlib
import json
import os
import logging

logger = logging.getLogger(__name__)


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def load_registry(path: str) -> dict:
    if not os.path.exists(path):
        return {"version": "1.0.0", "models": {}}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def verify_or_fill(registry_path: str, model_paths: dict) -> list:
    reg = load_registry(registry_path)
    models = reg.setdefault("models", {})
    results = []
    for space, path in model_paths.items():
        entry = models.setdefault(space, {})
        if not os.path.exists(path):
            results.append({"space": space, "status": "missing_file", "path": path})
            continue
        actual = sha256_file(path)
        expected = entry.get("sha256")
        if not expected:
            entry["sha256"] = actual
            entry["path"] = path
            models[space] = entry
            results.append({"space": space, "status": "filled", "sha256": actual})
        elif expected == actual:
            results.append({"space": space, "status": "ok", "sha256": actual})
        else:
            results.append({
                "space": space,
                "status": "mismatch",
                "expected": expected,
                "actual": actual,
            })
    with open(registry_path, "w", encoding="utf-8") as f:
        json.dump(reg, f, indent=2, ensure_ascii=False)
    return results
