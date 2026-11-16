"""gen_mode_detector.py — Genera router_llm_hf/mode_detector.py con reglas
deterministas para los 12 modos. Sin ML, sin LLM.

NOTA DEL DIRECTOR (2026-11-16): el CODE de abajo es la versión YA CORREGIDA
que adjunta el owner (re.IGNORECASE). El bloque original del DAG traía
`re.search(pat, p)`, que dejaba muertos los literales en MAYÚSCULAS
(HTML, CSS, React, API, README, 3D, Blender, Three.js) porque detect_mode()
pasa el prompt a minúsculas. No se sustituye la lógica: se usa el fichero
corregido tal cual lo entrega el owner.
"""
import os

OUT = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "router_llm_hf", "mode_detector.py",
)

CODE = r'''"""mode_detector.py — Detector determinista de los 12 modos por palabras clave.
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
    p = prompt.lower()
    scores = {m: 0 for m in RULES}
    for m, pats in RULES.items():
        for pat in pats:
            if re.search(pat, p, re.IGNORECASE):  # <-- FIX: IGNORECASE
                scores[m] += 1
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else DEFAULT_MODE
'''

def main():
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(CODE)
    print(f"mode_detector.py escrito en {OUT}")

if __name__ == "__main__":
    main()
