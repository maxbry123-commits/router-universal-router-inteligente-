"""Clave unica de acceso del Router.

Una sola clave (la del Director) en RIU_API_KEY. Por compatibilidad, si no esta
definida se usan las variables antiguas, para que el arranque no falle.
No contiene ningun valor de clave.
"""
import os


def access_key() -> str:
    for name in ("RIU_API_KEY", "RIU_PUBLIC_CHAT_KEY", "RIU_MCP_KEY", "RIU_ROUTER_API_KEY"):
        v = os.getenv(name)
        if v:
            return v
    return ""
