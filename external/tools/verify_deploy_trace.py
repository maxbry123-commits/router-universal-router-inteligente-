"""verify_deploy_trace.py — Raiz de trazabilidad de despliegue
Lee RAW de cada commit del KB, calcula SHA256 real, clasifica por categoria
y genera docs/AUDIT_SHA256_FORENSE.json con evidencia forense completa.
"""
from __future__ import annotations
import hashlib
import json
import logging
import sys
import time
from pathlib import Path
from typing import Dict, Any, List

try:
    import httpx
except ImportError:
    print("FATAL: httpx no instalado. Ejecutar: pip install httpx")
    sys.exit(2)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

REPO = "maxbry123-commits/router-universal-router-inteligente-"
BRANCH = "ccr-f01c3de9-bmry0s"
RAW_BASE = f"https://raw.githubusercontent.com/{REPO}/{BRANCH}"

# 13 commits del KB clasificados por categoria
COMMITS: List[Dict[str, Any]] = [
    # Categoria A: diff visible completo
    {"commit": "3fa2974", "archivo": "ROUTER MVP v1/system_prompt_py/openai_compatible_proxy.py",
     "categoria": "diff_visible", "loc_esperadas": 126, "descripcion": "Data Plane proxy"},
    {"commit": "077f1ef", "archivo": "ROUTER MVP v1/system_prompt_py/README.md",
     "categoria": "diff_visible", "loc_esperadas": 51, "descripcion": "README Data Plane"},
    {"commit": "12b1a6f7", "archivo": "router_llm_hf/watchdog.py",
     "categoria": "diff_visible", "loc_esperadas": 67, "descripcion": "Watchdog 30s/96s"},
    {"commit": "c1bde4da", "archivo": "router_llm_hf/queue_manager.py",
     "categoria": "diff_visible", "loc_esperadas": 99, "descripcion": "Queue prioridad 85% RAM"},
    {"commit": "bce0065", "archivo": "router_llm_hf/output_contract.py",
     "categoria": "diff_visible", "loc_esperadas": 42, "descripcion": "Pydantic strict 8 campos"},
    {"commit": "48ab8f6d", "archivo": "router_llm_hf/mode_router.py",
     "categoria": "diff_visible", "loc_esperadas": 43, "descripcion": "12 modos a (dataset, LoRA)"},
    {"commit": "0ef04d83", "archivo": "router_llm_hf/recall_engine.py",
     "categoria": "diff_visible", "loc_esperadas": 55, "descripcion": "Recall 8 intentos"},
    # Categoria B: diff vacio (flag F1)
    {"commit": "138a54f", "archivo": "ROUTER MVP v1/system_prompt_py/tests/test_control_bridge.py",
     "categoria": "diff_vacio_F1", "loc_esperadas": 40, "descripcion": "Test cierre Data Plane",
     "flag": "F1a"},
    {"commit": "9efd12d", "archivo": "router_llm_hf/tests/__init__.py",
     "categoria": "diff_vacio_F1", "loc_esperadas": 1, "descripcion": "Init tests Control Plane",
     "flag": "F1a"},
    {"commit": "cd095fc", "archivo": "router_llm_hf/escalation_guard.py",
     "categoria": "diff_vacio_F1", "loc_esperadas": 44, "descripcion": "AND-gate anti-escalada",
     "flag": "F1b"},
    {"commit": "c506896", "archivo": "router_llm_hf/tests/test_queue_manager.py",
     "categoria": "diff_vacio_F1", "loc_esperadas": 42, "descripcion": "Test queue Control Plane",
     "flag": "F1c"},
    {"commit": "561a97a", "archivo": "router_llm_hf/__init__.py",
     "categoria": "diff_vacio_F1", "loc_esperadas": 23, "descripcion": "Init paquete Control Plane",
     "flag": "F1d"},
    # Categoria C: error de sesion GitHub
    {"commit": "fd07fae", "archivo": "router_llm_hf/README.md",
     "categoria": "error_sesion_GH", "loc_esperadas": None, "descripcion": "README Control Plane",
     "flag": "F1"},
]


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def fetch_raw(archivo: str, timeout: float = 20.0) -> Dict[str, Any]:
    url = f"{RAW_BASE}/{archivo}"
    try:
        r = httpx.get(url, timeout=timeout, follow_redirects=True)
        r.raise_for_status()
        text = r.text
        lines = text.count("\n")
        return {
            "status": "OK",
            "url": url,
            "size_bytes": len(text.encode("utf-8")),
            "lines": lines,
            "sha256": sha256_text(text),
            "sha256_bytes": sha256_bytes(r.content),
            "preview": text[:200],
        }
    except httpx.HTTPStatusError as e:
        return {"status": f"HTTP_{e.response.status_code}", "url": url, "error": str(e)}
    except Exception as e:
        return {"status": "ERROR", "url": url, "error": str(e)}


def check_syntax_python(text: str) -> str:
    try:
        compile(text, "<raw>", "exec")
        return "OK"
    except SyntaxError as e:
        return f"SYNTAX_ERROR: {e}"


def verify_commit(commit_data: Dict[str, Any]) -> Dict[str, Any]:
    archivo = commit_data["archivo"]
    raw = fetch_raw(archivo)
    result = {
        "commit": commit_data["commit"],
        "archivo": archivo,
        "categoria": commit_data["categoria"],
        "descripcion": commit_data["descripcion"],
        "flag": commit_data.get("flag"),
        "loc_esperadas": commit_data["loc_esperadas"],
        "fetch": raw,
    }
    if raw["status"] != "OK":
        result["veredicto"] = "FAIL_FETCH"
        return result
    loc_real = raw["lines"]
    if commit_data["loc_esperadas"] is not None:
        delta = abs(loc_real - commit_data["loc_esperadas"])
        if delta > 5:
            result["veredicto"] = "LOC_MISMATCH"
            result["loc_real"] = loc_real
            result["delta"] = delta
            return result
    if archivo.endswith(".py"):
        preview = raw.get("preview", "")
        syntax = check_syntax_python(preview) if preview else "n/a"
        result["syntax"] = syntax
        if syntax.startswith("SYNTAX_ERROR"):
            result["veredicto"] = "SYNTAX_ERROR"
            return result
    result["veredicto"] = "OK"
    result["loc_real"] = loc_real
    return result


def run_full_audit() -> Dict[str, Any]:
    logger.info("Iniciando auditoria forense de %d commits", len(COMMITS))
    resultados = []
    for c in COMMITS:
        r = verify_commit(c)
        resultados.append(r)
        logger.info("[%s] %s -> %s (SHA256: %s)",
                    c["commit"][:7], c["archivo"], r["veredicto"],
                    r.get("fetch", {}).get("sha256", "N/A")[:16] + "...")
    resumen = {
        "total": len(resultados),
        "ok": sum(1 for r in resultados if r["veredicto"] == "OK"),
        "fail_fetch": sum(1 for r in resultados if r["veredicto"] == "FAIL_FETCH"),
        "loc_mismatch": sum(1 for r in resultados if r["veredicto"] == "LOC_MISMATCH"),
        "syntax_error": sum(1 for r in resultados if r["veredicto"] == "SYNTAX_ERROR"),
        "diff_visible_ok": sum(1 for r in resultados
                               if r["categoria"] == "diff_visible" and r["veredicto"] == "OK"),
        "diff_vacio_ok": sum(1 for r in resultados
                             if r["categoria"] == "diff_vacio_F1" and r["veredicto"] == "OK"),
        "error_sesion_ok": sum(1 for r in resultados
                               if r["categoria"] == "error_sesion_GH" and r["veredicto"] == "OK"),
    }
    return {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "repo": REPO,
        "branch": BRANCH,
        "resumen": resumen,
        "resultados": resultados,
    }


def write_report(audit: Dict[str, Any], out_path: str = "docs/AUDIT_SHA256_FORENSE.json") -> Path:
    p = Path(out_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(audit, f, indent=2, ensure_ascii=False)
    logger.info("Reporte forense escrito en %s", p)
    return p


def print_summary_table(audit: Dict[str, Any]) -> None:
    print("\n" + "=" * 100)
    print("AUDITORIA FORENSE X-RAY - RAIZ DE TRAZABILIDAD")
    print("=" * 100)
    print(f"{'commit':<10} {'archivo':<60} {'categoria':<18} {'veredicto':<15} {'sha256':<20}")
    print("-" * 100)
    for r in audit["resultados"]:
        sha = r.get("fetch", {}).get("sha256", "N/A")[:16]
        print(f"{r['commit']:<10} {r['archivo']:<60} {r['categoria']:<18} {r['veredicto']:<15} {sha}...")
    print("-" * 100)
    s = audit["resumen"]
    print(f"Total: {s['total']} | OK: {s['ok']} | FAIL_FETCH: {s['fail_fetch']} | "
          f"LOC_MISMATCH: {s['loc_mismatch']} | SYNTAX_ERROR: {s['syntax_error']}")
    print(f"Diff visible OK: {s['diff_visible_ok']}/7 | "
          f"Diff vacio OK: {s['diff_vacio_ok']}/5 | "
          f"Error sesion OK: {s['error_sesion_ok']}/1")
    print("=" * 100)


if __name__ == "__main__":
    audit = run_full_audit()
    write_report(audit)
    print_summary_table(audit)
    sys.exit(0 if audit["resumen"]["ok"] == audit["resumen"]["total"] else 1)
