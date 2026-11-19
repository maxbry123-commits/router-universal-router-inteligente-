"""space_inventory.py — Inventario canonico de los Spaces del router.

Fuente UNICA de verdad del cableado de Spaces. El router tiene DOS grupos de
TRES Spaces (6 en total):

  Grupo 1 "compute" (proxy / Data Plane, Router MVP v1):
      space-grupo-1-router-mvp-1, space-grupo-1-router-mvp-1-v2,
      space-grupo-1-router-mvp-1-v7
      -> solo COMPUTO: enruta, decide el modo y devuelve la respuesta.
  Grupo 2 "llm" (LLM local GGUF):
      space-grupo-2-router-llm-hf-1, space-grupo-2-router-llm-hf-2,
      space-grupo-2-router-llm-hf-3
      -> solo INFERENCE local (puerto 7861): un GGUF por Space.

Renombrados en HF el 2026-11-18 (move_repo). Nombres anteriores RETIRADOS
(ya no existen con ese nombre): local-llm-router, local-llm-router-v2,
local-llm-router-v7, swe-code-s1, swe-code-s2, swe-code-s3.

NO forman parte del router (infraestructura; el proxy no los enruta):
  hf-bucket-mcp — servidor MCP del bucket de memoria.

Historicos que NO existen en HF (HTTP 404 verificado el 2026-11-18):
  # REMOVED: riu-router ref, claude-github-mcp-backup, swe-code-web.

COMPUTO y ALMACENAMIENTO PERSISTENTE (lo que se conecta a HF):
  - compute: cada Space es un contenedor HF con hardware cpu-upgrade (32 GB RAM,
    CPU de pago). El Grupo 1 expone el puerto 7860 (proxy Router MVP v1) y el
    Grupo 2 el 7861 (servidor de modelo).
  - almacenamiento persistente, 2 capas:
      1) disco del Space: /data (disco persistente del Space de pago) -> estado,
         checkpoints y cache de los GGUF descargados.
      2) memoria compartida: bucket de HF
         hf://buckets/COMAND-CENTER-1/yaiwes-memoria-storage, servido por el MCP
         oficial hf-bucket-mcp (MCP_MEMORY_HTTP_URL) -> banco cifrado, memoria
         de los agentes y auditoria, compartidos entre los 6 Spaces.

Este modulo solo declara el inventario: no escribe ni llama a la API de HF.
"""
from __future__ import annotations

NAMESPACE = "COMAND-CENTER-1"

# Grupo 1: compute / proxy del Data Plane (3)
GROUP_1_COMPUTE = (
    "space-grupo-1-router-mvp-1",
    "space-grupo-1-router-mvp-1-v2",
    "space-grupo-1-router-mvp-1-v7",
)
# Grupo 2: LLM local (GGUF) (3)
GROUP_2_LLM = (
    "space-grupo-2-router-llm-hf-1",
    "space-grupo-2-router-llm-hf-2",
    "space-grupo-2-router-llm-hf-3",
)

SPACE_COUNT = len(GROUP_1_COMPUTE) + len(GROUP_2_LLM)  # 6

# Infraestructura: existe, pero el router no lo enruta.
NOT_ROUTER_SPACES = ("hf-bucket-mcp",)
# Historicos: 404 en HF (incluye los nombres anteriores de los 6 Spaces).
RETIRED_SPACES = (
    "# REMOVED: riu-router ref",
    "claude-github-mcp-backup",
    "swe-code-web",
    "local-llm-router",
    "local-llm-router-v2",
    "local-llm-router-v7",
    "swe-code-s1",
    "swe-code-s2",
    "swe-code-s3",
)

# --- Compute y almacenamiento (lo que cada grupo aporta) --------------------
HARDWARE = "cpu-upgrade"  # 32 GB RAM, CPU de pago
APP_PORT_COMPUTE = 7860
APP_PORT_LLM = 7861
BUCKET = "COMAND-CENTER-1/yaiwes-memoria-storage"
BUCKET_URI = "hf://buckets/COMAND-CENTER-1/yaiwes-memoria-storage"
MCP_MEMORY_SPACE = "hf-bucket-mcp"
MCP_MEMORY_PATH = "/mcp"
DISCO_PERSISTENTE = "/data"

GROUPS = {
    "grupo_1_router_mvp_1": {
        "nombre": "space grupo 1 router MVP 1",
        "rol": "compute",
        "funcion": "Enruta y ejecuta. No sirve modelos.",
        "spaces": GROUP_1_COMPUTE,
        "app_port": APP_PORT_COMPUTE,
        "hardware": HARDWARE,
        "compute": "HF Space docker · hardware cpu-upgrade (32 GB RAM, CPU de pago) · puerto {}".format(
            APP_PORT_COMPUTE
        ),
        "almacenamiento": {
            "disco_persistente": DISCO_PERSISTENTE,
            "memoria_compartida": "{} via {} (MCP_MEMORY_HTTP_URL)".format(BUCKET_URI, MCP_MEMORY_SPACE),
        },
    },
    "grupo_2_router_llm_hf": {
        "nombre": "space grupo 2 router LLM HF",
        "rol": "llm",
        "funcion": "Sirve UN modelo local. No enruta ni decide.",
        "spaces": GROUP_2_LLM,
        "app_port": APP_PORT_LLM,
        "hardware": HARDWARE,
        "compute": "HF Space docker · hardware cpu-upgrade (32 GB RAM, CPU de pago) · puerto {}".format(
            APP_PORT_LLM
        ),
        "almacenamiento": {
            "disco_persistente": DISCO_PERSISTENTE,
            "memoria_compartida": "{} via {} (MCP_MEMORY_HTTP_URL)".format(BUCKET_URI, MCP_MEMORY_SPACE),
        },
    },
}

# Modelo local que sirve cada Space del Grupo 2 (variables reales del Space).
GROUP_2_MODELOS = {
    "space-grupo-2-router-llm-hf-1": "Qwen/Qwen2.5-Coder-0.5B-Instruct-GGUF",
    "space-grupo-2-router-llm-hf-2": "LiquidAI/LFM2.5-350M-GGUF",
    "space-grupo-2-router-llm-hf-3": "unsloth/Qwen3.5-0.8B-GGUF",
}


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


def mcp_memory_url():
    """URL del MCP de HF que sirve el bucket de memoria."""
    return "https://comand-center-1-{}.hf.space{}".format(MCP_MEMORY_SPACE, MCP_MEMORY_PATH)


def grupo_por_rol(rol):
    """'compute' | 'llm' -> nombre del grupo."""
    for nombre, g in GROUPS.items():
        if g["rol"] == rol:
            return nombre
    return None
