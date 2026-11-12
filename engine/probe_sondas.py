"""probe_sondas.py — Sondas reales para pares pending_audit (C5-01, regla R7).
R7: evidence valida = {kind, detail, commit, ts} de sonda real
(http_status / mcp_initialize / file_exists). Import NO cuenta.
Nunca marca active: solo produce evidencia; la promocion es decision del
owner y el registry de main NO se escribe desde esta rama.
Uso: python engine/probe_sondas.py [--registry connections/registry.yaml]
     [--out docs/SONDAS_EVIDENCIA.json]
Si el registry no existe local, lo lee en solo-lectura desde main (RAW).
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
import urllib.request
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
RAW_MAIN = ("https://raw.githubusercontent.com/maxbry123-commits/"
            "router-universal-router-inteligente-/main/connections/registry.yaml")


def _now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _head_commit() -> str | None:
    try:
        r = subprocess.run(["git", "rev-parse", "HEAD"], cwd=str(ROOT),
                           capture_output=True, text=True, timeout=10)
        return r.stdout.strip() if r.returncode == 0 else None
    except Exception:  # noqa: BLE001
        return None


def _load_registry(path: str) -> list[dict[str, Any]]:
    import yaml
    p = Path(path)
    if p.is_file():
        text = p.read_text(encoding="utf-8")
    else:
        with urllib.request.urlopen(RAW_MAIN, timeout=30) as r:  # noqa: S310
            text = r.read().decode("utf-8")
    data = yaml.safe_load(text)
    return data if isinstance(data, list) else []


def _probe_file_exists(pair: dict[str, Any]) -> dict[str, Any] | None:
    paths = pair.get("observed_paths") or []
    checked: list[dict[str, Any]] = []
    ok = 0
    for par in paths[:5]:
        if not isinstance(par, (list, tuple)) or len(par) != 2:
            continue
        a, b = ROOT / str(par[0]), ROOT / str(par[1])
        existe = a.is_file() and b.is_file()
        checked.append({"a": str(par[0]), "b": str(par[1]),
                        "both_exist": existe})
        ok += 1 if existe else 0
    if not checked or ok == 0:
        return None
    return {"kind": "file_exists",
            "detail": f"{ok}/{len(checked)} pares de rutas existen en el arbol",
            "paths": checked}


def _probe_http(pair: dict[str, Any]) -> dict[str, Any] | None:
    ep = pair.get("endpoint")
    if not ep or not str(ep).startswith("http"):
        return None
    try:
        req = urllib.request.Request(str(ep), method="GET")
        with urllib.request.urlopen(req, timeout=5) as r:  # noqa: S310
            return {"kind": "http_status",
                    "detail": f"GET {ep} -> {r.status}"}
    except Exception:  # noqa: BLE001
        return None


def run_probes(registry_path: str, out_path: str) -> int:
    commit = _head_commit()
    try:
        pairs = _load_registry(registry_path)
    except Exception as exc:  # noqa: BLE001
        print("FATAL registry: " + type(exc).__name__)
        return 2
    results: list[dict[str, Any]] = []
    con_evidencia = 0
    for pair in pairs:
        ev = _probe_http(pair) or _probe_file_exists(pair)
        row: dict[str, Any] = {
            "id": pair.get("id", "?"), "name": pair.get("name"),
            "status_original": pair.get("status"), "ts": _now(),
        }
        if ev and commit:
            ev["commit"] = commit
            ev["ts"] = _now()
            row["evidence"] = ev
            row["resultado"] = "EVIDENCIA_REAL"
            con_evidencia += 1
        else:
            row["evidence"] = None
            row["resultado"] = "SIN_EVIDENCIA"
            row["flag"] = ("sin_commit_HEAD" if ev and not commit
                           else "sonda_no_evaluable")
        results.append(row)
    report = {
        "ts": _now(), "branch": "ccr-f01c3de9-bmry0s",
        "head_commit": commit, "total_pares": len(pairs),
        "con_evidencia_real": con_evidencia,
        "sin_evidencia": len(pairs) - con_evidencia,
        "nota": "registry de main no se modifica; promocion a active es decision del owner",
        "pares": results,
    }
    p = Path(out_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(report, indent=2, ensure_ascii=False),
                 encoding="utf-8")
    print("=" * 72)
    for r in results:
        print(f"{r['id']:<10} {r['resultado']:<16} {r.get('flag', '')}")
    print("=" * 72)
    print(f"pares: {len(pairs)} | evidencia real: {con_evidencia} "
          f"| sin evidencia: {len(pairs) - con_evidencia}")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--registry", default="connections/registry.yaml")
    ap.add_argument("--out", default="docs/SONDAS_EVIDENCIA.json")
    a = ap.parse_args()
    sys.exit(run_probes(a.registry, a.out))
