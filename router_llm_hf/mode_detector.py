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

# --- Modos de SERVICIO (4) -------------------------------------------------
# No son modos entrenables: son RUTAS del proxy (ver router_llm_hf/service_routes.py).
# Se detectan aparte y TIENEN PRIORIDAD sobre los modos de codigo cuando el
# usuario los pide de forma explicita.
SERVICE_RULES = {
    "swe_code": [r"\bswe[\s_-]?code\b"],
    "swe_free": [r"\bswe[\s_-]?free\b"],
    "team_qwe": [r"\bteam[\s_-]?qwe\b", r"\bqwe\b"],
    "deployment": [r"\bdeploy", r"\bdesplieg", r"\bdockerfile\b", r"\bkubernetes\b"],
}

SERVICE_MODE_NAMES = tuple(SERVICE_RULES.keys())


def detect_mode(prompt: str) -> str:
    """Devuelve el modo detectado. Si no hay coincidencia, DEFAULT_MODE.

    Puntuacion por ESPECIFICIDAD: cada patron que casa suma len(patron), asi
    "modelo 3D" (10) gana a "genera" (5) y "razona" (7) gana a "falla" (6).
    Empate -> el match mas temprano en el prompt; ultimo desempate -> orden de
    declaracion. (El desempate anterior, "gana el primero del dict", hacia que
    3d_code y reasoning perdieran contra code_generate y code_debug.)
    """
    p = (prompt or "").lower()
    best = None
    for order, (mode, pats) in enumerate(RULES.items()):
        score = 0
        count = 0
        first = None
        for pat in pats:
            for mt in re.finditer(pat, p, re.IGNORECASE):
                score += len(pat)
                count += 1
                if first is None or mt.start() < first:
                    first = mt.start()
        if count == 0:
            continue
        key = (-score, first, order)
        if best is None or key < best[0]:
            best = (key, mode)
    return best[1] if best else DEFAULT_MODE


def detect_service_route(prompt: str):
    """Modo de SERVICIO explicito (o None).

    Desempate determinista: gana el modo cuyo PATIDO aparece antes en el prompt
    (intencion principal del usuario); a igualdad, el que mas patrones casa y,
    en ultimo termino, el orden de declaracion.
    """
    p = (prompt or "").lower()
    hits = {}
    for order, (mode, pats) in enumerate(SERVICE_RULES.items()):
        first = None
        count = 0
        for pat in pats:
            for m in re.finditer(pat, p, re.IGNORECASE):
                count += 1
                if first is None or m.start() < first:
                    first = m.start()
        if count:
            hits[mode] = (first, -count, order)
    if not hits:
        return None
    return min(hits.items(), key=lambda kv: kv[1])[0]
