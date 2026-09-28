"""Genera y valida Mermaid para /archify."""
from __future__ import annotations
import re

def validar_mermaid(texto: str) -> str:
    limpio = texto.strip()
    if not re.match(r"^(flowchart|graph)\b", limpio):
        raise ValueError("Mermaid debe empezar por flowchart o graph")
    return limpio

def archify(texto: str) -> dict[str, str]:
    if not texto.strip():
        raise ValueError("texto requerido")
    safe = " ".join(texto.strip().split()).replace('"', "'")
    mermaid = f'flowchart LR\n  A["INPUT"] --> B["{safe}"] --> C["PASS|FAIL"]'
    return {"status": "PASS", "mermaid": validar_mermaid(mermaid)}
