"""Fichas externas: catalogo de modelos, servicios y conexion al puente existente."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent/"puente_chat"/"fichas"
def handle(action,payload):
    if action in ("listar","modelos","status"):
        fichas=[json.loads(p.read_text()) for p in sorted(ROOT.glob("*.json"))]
        return {"ok":True,"fichas":fichas,"count":len(fichas),"transporte":"HTTP","banco":"HF cifrado"}
    from plugins.puente_chat.plugin import handle as bridge
    return bridge(action,payload)
