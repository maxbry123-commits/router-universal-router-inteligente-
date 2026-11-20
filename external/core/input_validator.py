"""input_validator.py — Valida estructura F1/F2"""
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

F1_CAMPOS = ["Objetivo:"]
F2_CAMPOS = ["Objetivo:", "PLAN PROPUESTO", "Restricciones:", "Criterio de éxito:"]


def validar_f1(input_text: str) -> Dict[str, Any]:
    faltantes = [c for c in F1_CAMPOS if c not in input_text]
    if faltantes:
        return {"valido": False, "formato": "F1", "faltantes": faltantes,
                "error": f"F1 incompleto: faltan {faltantes}"}
    return {"valido": True, "formato": "F1", "faltantes": []}


def validar_f2(input_text: str) -> Dict[str, Any]:
    faltantes = [c for c in F2_CAMPOS if c not in input_text]
    if faltantes:
        return {"valido": False, "formato": "F2", "faltantes": faltantes,
                "error": f"F2 incompleto: faltan {faltantes}"}
    return {"valido": True, "formato": "F2", "faltantes": []}


def validar(input_text: str, formato: str) -> Dict[str, Any]:
    if formato == "F1":
        return validar_f1(input_text)
    if formato == "F2":
        return validar_f2(input_text)
    return {"valido": False, "formato": formato, "error": f"Formato desconocido: {formato}"}
