"""space_inventory.py — Inventario canonico de los Spaces del router.

Fuente UNICA de verdad del cableado de Spaces. El router tiene DOS grupos de
TRES Spaces (6 en total):

  Grupo 1 "compute" (proxy / Data Plane): local-llm-router, -v2, -v7
  Grupo 2 "llm"     (LLM local GGUF):      swe-code-s1, -s2, -s3

NO forman parte del router (infraestructura; el proxy no los enruta):
  hf-bucket-mcp — servidor MCP del bucket de memoria.

Nombres historicos RETIRADOS: "riu-router", "claude-github-mcp-backup" y
"swe-code-web" NO existen en HF (HTTP 404 verificado el 2026-11-18). Se
quitaron de los listados del repo porque dejaban el health-check siempre en
OFFLINE y las inyecciones del scaler fallando en 3 Spaces.

Este modulo solo declara el inventario: no escribe ni llama a la API de HF.
"""
from __future__ import annotations

NAMESPACE = "COMAND-CENTER-1"

# Grupo 1: proxy del Data Plane (3)
GROUP_1_COMPUTE = ("local-llm-router", "local-llm-router-v2", "local-llm-router-v7")
# Grupo 2: LLM local (GGUF) (3)
GROUP_2_LLM = ("swe-code-s1", "swe-code-s2", "swe-code-s3")

SPACE_COUNT = len(GROUP_1_COMPUTE) + len(GROUP_2_LLM)  # 6

# Infraestructura: existe, pero el router no lo enruta.
NOT_ROUTER_SPACES = ("hf-bucket-mcp",)
# Historicos: 404 en HF.
RETIRED_SPACES = ("riu-router", "claude-github-mcp-backup", "swe-code-web")


def all_spaces():
    """Los 6 Spaces del router (2 grupos x 3)."""
    return GROUP_1_COMPUTE + GROUP_2_LLM


def group_of(space):
    """'compute' | 'llm' | None (si no pertenece al router)."""
    if space in GROUP_1_COMPUTE:
        return "compute"
    if space in GROUP_2_LLM:
        return "llm"
    return None


def hf_repo_id(space):
    return "{}/{}".format(NAMESPACE, space)


def space_url(space, path=""):
    base = "https://comand-center-1-{}.hf.space".format(space)
    if not path:
        return base
    return "{}/{}".format(base, path.lstrip("/"))
