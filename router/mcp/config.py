"""Configuracion en tiempo de ejecucion. Ningun secreto vive en el codigo: todo sale de variables de entorno
(que el Router rellena desde su banco de secretos). La URL con llave se arma al vuelo y nunca se guarda."""
from __future__ import annotations
import os

OWNER = "maxbry123-commits"
RAMAS_DEFECTO = "feat/modos-router,reorganizacion"


def env(nombre: str, defecto: str = "") -> str:
    return os.environ.get(nombre, defecto) or defecto


def router_base() -> str:
    return env("RIU_ROUTER_URL", "https://comand-center-1-riu-router.hf.space").rstrip("/")


def ramas_permitidas() -> list:
    return [r.strip() for r in env("RIU_MCP_RAMAS", RAMAS_DEFECTO).split(",") if r.strip()]


def escritura_activa() -> bool:
    return env("RIU_MCP_ESCRITURA", "1") != "0"


def llave_mcp() -> str:
    return env("RIU_MCP_KEY") or env("RIU_PUBLIC_CHAT_KEY")  # respaldo del MCP viejo


def llave_chat() -> str:
    return env("RIU_CHAT_KEY")  # ref del banco: router/chat-ui-director


def github_pat() -> str:
    return env("RIU_GITHUB_PAT") or env("GITHUB_PERSONAL_ACCESS_TOKEN")


def secretos() -> list:
    return [s for s in (llave_mcp(), llave_chat(), github_pat()) if s and len(s) >= 6]


def redactar(obj):
    """Sustituye cualquier secreto conocido por *** en cualquier estructura (salidas, errores, logs)."""
    sec = secretos()
    if isinstance(obj, str):
        for s in sec:
            obj = obj.replace(s, "***")
        return obj
    if isinstance(obj, dict):
        return {k: redactar(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [redactar(v) for v in obj]
    return obj
