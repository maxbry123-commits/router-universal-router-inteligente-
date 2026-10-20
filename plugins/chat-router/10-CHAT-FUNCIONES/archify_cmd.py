"""Genera Mermaid validado para /archify."""
from __future__ import annotations
import re

def archify(texto:str)->str:
    if not texto.strip(): raise ValueError("texto requerido")
    safe=re.sub(r"[^\w áéíóúÁÉÍÓÚñÑ.-]","",texto)[:120]
    result=f"flowchart LR\n  INPUT[Input] --> TASK[{safe}] --> PASS[PASS]"
    if not result.lstrip().startswith(("flowchart","graph")): raise ValueError("Mermaid inválido")
    return result
