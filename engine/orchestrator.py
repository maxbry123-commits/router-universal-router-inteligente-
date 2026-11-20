"""orchestrator.py — Orquestador unico determinista F1->F10 (cierre-v1, G8).
Sin LLM ni razonamiento: cada etapa es una sonda real con PASS/FAIL.
Fail-closed: lo que no se puede evaluar es FAIL, nunca PASS.
Uso: python engine/orchestrator.py [--json docs/ORCHESTRATOR_REPORT.json]
Exit 0 si todas PASS; exit 1 si alguna FAIL (se reportan todas, no detiene).
"""
from __future__ import annotations

import argparse
import json
import os
import py_compile
import sys
import time
from pathlib import Path
from typing import Any, Callable, Dict, List, Tuple

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _r(stage: str, status: str, detail: str) -> Dict[str, Any]:
    return {"stage": stage, "status": status, "detail": detail[:300], "ts": _now()}


def f1_memoria() -> Dict[str, Any]:
    try:
        from plugins.memoria.plugin import handle
        r = handle("status", {})
        return _r("F1_memoria", "PASS" if r.get("status") == "ok" else "FAIL",
                  json.dumps(r, ensure_ascii=False))
    except Exception as exc:  # noqa: BLE001
        return _r("F1_memoria", "FAIL", type(exc).__name__ + ": " + str(exc))


def f2_busqueda() -> Dict[str, Any]:
    try:
        from plugins.memoria.plugin import handle
        key = "_orch_probe"
        s = handle("save", {"key": key, "data": {"probe": "orquestador"}})
        if s.get("status") != "ok":
            return _r("F2_busqueda", "FAIL", "save: " + json.dumps(s, ensure_ascii=False))
        q = handle("search", {"query": "orquestador"})
        ok = q.get("status") == "ok" and q.get("count", 0) >= 1
        p = Path(s.get("path", ""))
        if p.exists():
            p.unlink()
        return _r("F2_busqueda", "PASS" if ok else "FAIL",
                  json.dumps(q, ensure_ascii=False))
    except Exception as exc:  # noqa: BLE001
        return _r("F2_busqueda", "FAIL", type(exc).__name__ + ": " + str(exc))


def f3_ligas() -> Dict[str, Any]:
    try:
        import yaml
        p = ROOT / "connections" / "wiring_registry.yaml"
        if not p.is_file():
            return _r("F3_ligas", "FAIL", "no existe connections/wiring_registry.yaml")
        data = yaml.safe_load(p.read_text(encoding="utf-8"))
        n = len((data or {}).get("services", {}))
        return _r("F3_ligas", "PASS" if n >= 1 else "FAIL", f"services={n}")
    except Exception as exc:  # noqa: BLE001
        return _r("F3_ligas", "FAIL", type(exc).__name__ + ": " + str(exc))


def f4_harness() -> Dict[str, Any]:
    try:
        from plugins.deepseek_harness.plugin import handle
        r = handle("status", {})
        return _r("F4_harness", "PASS" if r.get("status") == "ok" else "FAIL",
                  json.dumps(r, ensure_ascii=False))
    except Exception as exc:  # noqa: BLE001
        return _r("F4_harness", "FAIL", type(exc).__name__ + ": " + str(exc))


def f5_connectivity() -> Dict[str, Any]:
    try:
        from plugins.connectivity.plugin import handle
        r = handle("status", {})
        return _r("F5_connectivity", "PASS" if r.get("status") == "ok" else "FAIL",
                  json.dumps(r, ensure_ascii=False))
    except Exception as exc:  # noqa: BLE001
        return _r("F5_connectivity", "FAIL", type(exc).__name__ + ": " + str(exc))


def f6_control_plane() -> Dict[str, Any]:
    import importlib
    mods = ["router_llm_hf.watchdog", "router_llm_hf.queue_manager",
            "router_llm_hf.recall_engine", "router_llm_hf.output_contract",
            "router_llm_hf.escalation_guard", "router_llm_hf.mode_router"]
    fallidos = []
    for m in mods:
        try:
            importlib.import_module(m)
        except Exception as exc:  # noqa: BLE001
            fallidos.append(m + ":" + type(exc).__name__)
    return _r("F6_control_plane", "PASS" if not fallidos else "FAIL",
              "6/6 importables" if not fallidos else "; ".join(fallidos))


def f7_data_plane() -> Dict[str, Any]:
    p = ROOT / "ROUTER MVP v1" / "system_prompt_py" / "openai_compatible_proxy.py"
    try:
        if not p.is_file():
            return _r("F7_data_plane", "FAIL", "archivo no existe: " + str(p))
        py_compile.compile(str(p), doraise=True)
        return _r("F7_data_plane", "PASS", "py_compile OK (sin ejecutar)")
    except Exception as exc:  # noqa: BLE001
        return _r("F7_data_plane", "FAIL", type(exc).__name__ + ": " + str(exc))


def f8_persistencia() -> Dict[str, Any]:
    try:
        d = ROOT / "state"
        d.mkdir(parents=True, exist_ok=True)
        p = d / "_orch_write_probe.tmp"
        with open(p, "w", encoding="utf-8") as f:
            f.write("probe")
            f.flush()
            os.fsync(f.fileno())
        p.unlink()
        return _r("F8_persistencia", "PASS", "state/ escribible con fsync")
    except Exception as exc:  # noqa: BLE001
        return _r("F8_persistencia", "FAIL", type(exc).__name__ + ": " + str(exc))


def f9_gobernanza() -> Dict[str, Any]:
    try:
        from router_llm_hf.output_contract import OutputContract
        c = OutputContract.quick(task="orch-probe", respuesta="ok",
                                 estado="COMPLETADO")
        c.validate_or_raise()
        return _r("F9_gobernanza", "PASS", "OutputContract strict valida")
    except Exception as exc:  # noqa: BLE001
        return _r("F9_gobernanza", "FAIL", type(exc).__name__ + ": " + str(exc))


STAGES: List[Tuple[str, Callable[[], Dict[str, Any]]]] = [
    ("F1", f1_memoria), ("F2", f2_busqueda), ("F3", f3_ligas),
    ("F4", f4_harness), ("F5", f5_connectivity), ("F6", f6_control_plane),
    ("F7", f7_data_plane), ("F8", f8_persistencia), ("F9", f9_gobernanza),
]


def run_all(out_path: str) -> int:
    results = [fn() for _, fn in STAGES]
    fails = sum(1 for r in results if r["status"] == "FAIL")
    f10 = _r("F10_reporte", "PASS", out_path)
    report = {"ts": _now(), "branch": "ccr-f01c3de9-bmry0s",
              "pass": len(results) - fails, "fail": fails,
              "stages": results + [f10]}
    p = Path(out_path)
    try:
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(report, indent=2, ensure_ascii=False),
                     encoding="utf-8")
    except Exception as exc:  # noqa: BLE001
        report["stages"][-1] = _r("F10_reporte", "FAIL", type(exc).__name__)
        fails += 1
    print("=" * 72)
    for r in report["stages"]:
        print(f"{r['stage']:<18} {r['status']:<5} {r['detail']}")
    print("=" * 72)
    print(f"PASS: {len(results) - fails + (0 if fails else 0)} | FAIL: {fails}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", default="docs/ORCHESTRATOR_REPORT.json")
    args = ap.parse_args()
    sys.exit(run_all(args.json))
