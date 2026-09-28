"""Council paralelo con modo SIMULADO sin red."""
from __future__ import annotations
import asyncio
import os
from typing import Any

async def _consultar(idx: int, pregunta: str) -> dict[str, Any]:
    if os.getenv("SIMULADO") == "1":
        return {"modelo": f"sim-{idx}", "respuesta": f"respuesta-{idx}: {pregunta}", "approve": True}
    raise RuntimeError("Router real no configurado en este módulo standalone")

async def ask_council(pregunta: str, modelos: int = 3) -> dict[str, Any]:
    if not pregunta.strip():
        raise ValueError("pregunta vacía")
    if modelos < 1:
        raise ValueError("modelos debe ser >= 1")
    respuestas = await asyncio.gather(*(_consultar(i + 1, pregunta) for i in range(modelos)))
    revisiones = [{"modelo": r["modelo"],
                   "revisa": respuestas[(i + 1) % len(respuestas)]["modelo"],
                   "approve": bool(r.get("approve", False))}
                  for i, r in enumerate(respuestas)]
    sintesis = " | ".join(r["respuesta"] for r in respuestas)
    return {"status": "PASS", "pregunta": pregunta, "respuestas": respuestas,
            "revisiones": revisiones, "sintesis": sintesis}
