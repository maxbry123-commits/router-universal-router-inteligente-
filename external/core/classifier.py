"""classifier.py — Clasificador 8 tipos input -> F1/F2 (NCT/APEX)"""
import logging
import unicodedata
from typing import Tuple

logger = logging.getLogger(__name__)

TIPOS = {
    "pregunta": ["?", "qué", "cómo", "por qué", "cuándo", "dónde", "quién"],
    "investigacion": ["investigar", "buscar", "analizar", "DECCON", "fuentes"],
    "programacion": ["código", "implementar", "función", "clase", "bug", "fix", "refactor"],
    "auditoria": ["auditar", "X-Ray", "forense", "GAP", "verificación"],
    "arquitectura": ["diseño", "sistema", "componentes", "contratos", "cableado"],
    "agente": ["agente", "tool", "ejecutar", "aprobación", "HITL"],
    "proyecto": ["proyecto", "plan", "roadmap", "tareas", "progreso"],
    "comando": ["ejecuta", "corre", "despliega", "commit", "push"],
}
F1_TYPES = {"pregunta", "investigacion"}


def _normalize(text: str) -> str:
    return unicodedata.normalize("NFD", text).lower()


def clasificar(input_text: str) -> Tuple[str, str]:
    low = _normalize(input_text)
    for tipo, keywords in TIPOS.items():
        if any(kw in low for kw in keywords):
            formato = "F1" if tipo in F1_TYPES else "F2"
            logger.info("Clasificado: %s -> %s", tipo, formato)
            return (tipo, formato)
    words = len(input_text.split())
    return ("pregunta", "F1") if words < 50 else ("proyecto", "F2")


def validar_formato(input_text: str, formato_esperado: str) -> bool:
    if formato_esperado == "F1":
        return "Objetivo:" in input_text or "objetivo:" in input_text
    if formato_esperado == "F2":
        return ("Objetivo:" in input_text or "objetivo:" in input_text) and (
            "PLAN PROPUESTO" in input_text or "Plan de acción" in input_text
        )
    return False
