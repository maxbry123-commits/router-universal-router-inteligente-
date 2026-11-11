"""input_shark.py — DECCON 1-3 (20 fuentes). Decompose, Confront, Conclude."""
import re, logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

FUENTES = {
    "docs_repo": "docs/",
    "handoff_prev": "state/handoff.json",
    "crazy_wall": "state/crazy_wall.jsonl",
    "registry_modos": "external/tools/registry_modos.json",
    "output_contract": "external/core/output_contract.py",
    "escalation_guard": "external/core/escalation_guard.py",
    "queue_manager": "external/core/queue_manager.py",
    "recall_engine": "external/core/recall_engine.py",
    "mode_detector": "external/tools/mode_detector.py",
    "approval_gate": "external/tools/approval_gate.py",
    "download_manager": "external/tools/download_manager.py",
    "artifact_registry": "external/tools/artifact_registry.py",
    "capa_api": "external/api/capa_api.py",
    "proxy_health": "ROUTER MVP v1/system_prompt_py/openai_compatible_proxy.py",
    "hf_spaces": "llm system HF/manager.py",
    "github_commits": ".git/",
    "pytest_results": "tests/",
    "external_cache": "./external_cache",
    "state_dir": "./state",
    "owner_directives": "kernel/INPUT_BLOCK_YAIWES_CABLEADO.md",
}

PATRONES_RIESGO = [
    (r"\b(drop|delete|truncate|rm\s+-rf)\b", "destructivo"),
    (r"\b(password|secret|token|api_key)\s*[:=]", "credencial"),
    (r"\bsudo\b|\beval\(|exec\(", "privilegio"),
    (r"127\.0\.0\.1|localhost:(?!7860|7861)", "endpoint_no_autorizado"),
]

def decompose(input_text: str) -> Dict[str, Any]:
    palabras = len(input_text.split())
    lineas = input_text.count("\n") + 1
    riesgos = [et for pat, et in PATRONES_RIESGO
               if re.search(pat, input_text, re.IGNORECASE)]
    return {"palabras": palabras, "lineas": lineas,
            "riesgos_detectados": riesgos, "tamano_ok": palabras < 5000}

def confront(decomp: Dict[str, Any], fuentes_disponibles: List[str]) -> Dict[str, Any]:
    faltantes = [f for f in FUENTES if f not in fuentes_disponibles]
    return {"fuentes_totales": len(FUENTES),
            "fuentes_disponibles": len(fuentes_disponibles),
            "fuentes_faltantes": faltantes,
            "cobertura": len(fuentes_disponibles) / len(FUENTES) if FUENTES else 0.0}

def conclude(decomp: Dict[str, Any], confrontacion: Dict[str, Any]) -> Dict[str, Any]:
    riesgo_alto = bool(decomp["riesgos_detectados"])
    cobertura_ok = confrontacion["cobertura"] >= 0.7
    veredicto = ("OK" if (cobertura_ok and not riesgo_alto)
                 else "DEGRADADO" if cobertura_ok else "FAIL")
    return {"veredicto": veredicto,
            "cobertura_pct": round(confrontacion["cobertura"] * 100, 1),
            "riesgos": decomp["riesgos_detectados"],
            "accion": "continuar" if veredicto == "OK"
                      else "revisar" if veredicto == "DEGRADADO" else "bloquear"}

def run_deccon(input_text: str, fuentes_disponibles: List[str] = None) -> Dict[str, Any]:
    fuentes = fuentes_disponibles or []
    d = decompose(input_text)
    c = confront(d, fuentes)
    concl = conclude(d, c)
    return {"decompose": d, "confront": c, "conclude": concl}
