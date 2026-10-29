"""Compactación determinista del historial."""
from __future__ import annotations
from typing import Any

def compactar(historial:list[Any])->dict[str,Any]:
    if not isinstance(historial,list): raise TypeError("historial debe ser lista")
    text="\n".join(str(x.get("content",x)) if isinstance(x,dict) else str(x) for x in historial)
    return {"objetivo":text[:500],"decisiones":[],"archivos":[],"estado":"compactado","siguiente_paso":"continuar","mensajes":len(historial)}
