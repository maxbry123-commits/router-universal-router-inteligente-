"""mode_detector.py — Detector determinista de los 12 modos por palabras clave.
Usa re.IGNORECASE para que HTML/CSS/React/API/README/3D/Blender coincidan
aunque el prompt esté en minúsculas.
"""
import re

RULES = {
    "code_refactor": [r"\brefactor", r"\breestructura", r"\brenombra", r"\bextrae método"],
    "code_debug": [r"\bdebug", r"\berror", r"\bexcepción", r"\btraza", r"\bfalla"],
    "code_review": [r"\brevisa", r"\baudita", r"\bcode review", r"\bmalas prácticas"],
    "code_generate": [r"\bgenera", r"\bcrea", r"\bimplementa", r"\bescribe código"],
    "architecture": [r"\barquitectura", r"\bdiseño", r"\bpatrón", r"\bmicroservicio"],
    "reasoning": [r"\brazona", r"\banaliza", r"\bpor qué", r"\bexplica paso a paso"],
    "tool_call": [r"\bherramienta", r"\bfunción", r"\bAPI", r"\bllama a"],
    "planning": [r"\bplan", r"\broadmap", r"\bfases", r"\bcronograma"],
    "documentation": [r"\bdocumenta", r"\bREADME", r"\bdocstring", r"\bcomenta"],
    "frontend": [r"\bHTML", r"\bCSS", r"\bReact", r"\binterfaz", r"\bbotón"],
    "3d_code": [r"\b3D", r"\bmalla", r"\bmodelo 3D", r"\bBlender", r"\bThree\.js"],
    "verification": [r"\bverifica", r"\btest", r"\bprueba unitaria", r"\bassert"],
}
DEFAULT_MODE = "code_generate"

def detect_mode(prompt: str) -> str:
    """Devuelve el modo detectado. Si no hay coincidencia, DEFAULT_MODE."""
    p = (prompt or "").lower()
    scores = {m: 0 for m in RULES}
    for m, pats in RULES.items():
        for pat in pats:
            if re.search(pat, p, re.IGNORECASE):
                scores[m] += 1
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else DEFAULT_MODE
