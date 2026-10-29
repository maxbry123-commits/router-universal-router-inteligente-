"""Council paralelo sobre Router YAIWES; SIMULADO=1 no usa red."""
from __future__ import annotations
import asyncio,json,os

def _respuesta(pregunta:str,i:int)->str:
    if os.environ.get("SIMULADO")=="1": return f"modelo-{i}: {pregunta}"
    try:
        from pathlib import Path
        import sys
        root=Path(__file__).resolve().parents[1]/"05-AGENTES"/"colmena"
        sys.path.insert(0,str(root)); from router_cliente import RouterCliente
        return RouterCliente().chat(pregunta,"council")
    except Exception as exc: raise RuntimeError(f"council router: {exc}") from exc

async def ask_council(pregunta:str,modelos:int=3)->dict:
    if not pregunta or modelos<1: raise ValueError("pregunta/modelos inválidos")
    respuestas=await asyncio.gather(*[asyncio.to_thread(_respuesta,pregunta,i+1) for i in range(modelos)])
    sintesis=respuestas[0] if len(respuestas)==1 else " | ".join(respuestas)
    return {"pregunta":pregunta,"respuestas":list(respuestas),"revision_cruzada":len(respuestas),"sintesis":sintesis}
