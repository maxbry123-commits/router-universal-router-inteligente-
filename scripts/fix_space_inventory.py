"""fix_space_inventory.py — Op1: inventario canonico de los 6 Spaces del router.

Problema real (verificado contra la API de HF el 2026-11-18):
  - El router tiene 2 GRUPOS de 3 Spaces = 6. El 7º repo de Space del namespace
    ("hf-bucket-mcp") es el servidor MCP del bucket: infraestructura, NO lo enruta
    el proxy. Ningun fichero del repo decia "7"; el error estaba en MI informe.
  - "ROUTER MVP v1/system_prompt_py/health_check.py" y "inject_scaler.py" listaban
    3 Spaces INEXISTENTES (HTTP 404): "riu-router", "claude-github-mcp-backup",
    "swe-code-web". Con eso el health-check caia siempre en OFFLINE (3 de 6 URLs
    muerte) y las inyecciones del scaler fallaban en 3 Spaces.

Que hace (idempotente, fail-closed):
  1. Crea "external/core/space_inventory.py" como fuente UNICA de verdad.
  2. "external/tools/space_power_manager.py" deja de duplicar los literales y
     arregla el NameError de "action" cuando la llamada a HF falla.
  3. "health_check.py" e "inject_scaler.py" pasan a usar el inventario real.

No escribe fuera del repo ni toca la API de HF.
"""
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
os.chdir(ROOT)

INVENTORY = '''"""space_inventory.py — Inventario canonico de los Spaces del router.

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
  riu-router, claude-github-mcp-backup, swe-code-web.

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
    "riu-router",
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
'''

POWER_OLD = '''GROUP_1_COMPUTE = ["space-grupo-1-router-mvp-1", "space-grupo-1-router-mvp-1-v2", "space-grupo-1-router-mvp-1-v7"]
GROUP_2_LLM = ["space-grupo-2-router-llm-hf-1", "space-grupo-2-router-llm-hf-2", "space-grupo-2-router-llm-hf-3"]
'''

POWER_NEW = '''try:
    # Inventario canonico (Op1): fuente unica de verdad de los 6 Spaces.
    from external.core.space_inventory import (
        GROUP_1_COMPUTE,
        GROUP_2_LLM,
        SPACE_COUNT,
        all_spaces,
        group_of,
    )
except ImportError:  # pragma: no cover - arranca igual sin el paquete "external"
    GROUP_1_COMPUTE = ["space-grupo-1-router-mvp-1", "space-grupo-1-router-mvp-1-v2", "space-grupo-1-router-mvp-1-v7"]
    GROUP_2_LLM = ["space-grupo-2-router-llm-hf-1", "space-grupo-2-router-llm-hf-2", "space-grupo-2-router-llm-hf-3"]
    SPACE_COUNT = 6

    def all_spaces():
        return tuple(GROUP_1_COMPUTE) + tuple(GROUP_2_LLM)

    def group_of(space):
        if space in GROUP_1_COMPUTE:
            return "compute"
        if space in GROUP_2_LLM:
            return "llm"
        return None
'''

# NameError real: "action" se asignaba DESPUES de la llamada; si la llamada a HF
# fallaba, el except usaba una variable no definida y tapaba el error original.
POWER_ACTION_OLD = '''            repo_id = f"COMAND-CENTER-1/{space}"
            try:
                if on:
                    api.restart_space(repo_id, repo_type="space", factory_reboot=False)
                    action = "wake"
                else:
                    api.pause_space(repo_id, repo_type="space")
                    action = "pause"
'''

POWER_ACTION_NEW = '''            repo_id = f"COMAND-CENTER-1/{space}"
            action = "wake" if on else "pause"
            try:
                if on:
                    api.restart_space(repo_id, repo_type="space", factory_reboot=False)
                else:
                    api.pause_space(repo_id, repo_type="space")
'''

BOOTSTRAP = '''import os
import sys

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

try:
    from external.core.space_inventory import all_spaces
    SPACES = list(all_spaces())
except ImportError:  # pragma: no cover
    SPACES = [
        "space-grupo-1-router-mvp-1", "space-grupo-1-router-mvp-1-v2", "space-grupo-1-router-mvp-1-v7",
        "space-grupo-2-router-llm-hf-1", "space-grupo-2-router-llm-hf-2", "space-grupo-2-router-llm-hf-3",
    ]
'''

HEALTH_OLD = '''import httpx
import asyncio

SPACES = [
    "space-grupo-2-router-llm-hf-1", "space-grupo-2-router-llm-hf-2", "space-grupo-2-router-llm-hf-3",
    "riu-router", "claude-github-mcp-backup", "swe-code-web"
]
'''

HEALTH_NEW = '''import httpx
import asyncio

''' + BOOTSTRAP

SCALER_OLD = '''SPACES = ["space-grupo-2-router-llm-hf-1", "space-grupo-2-router-llm-hf-2", "space-grupo-2-router-llm-hf-3", "riu-router", "claude-github-mcp-backup", "swe-code-web"]
'''

SCALER_NEW = BOOTSTRAP

# Tercer bug real de la misma familia: apk_config.json apuntaba al Space MUERTO
# "riu-router" (404) en sus 3 entradas. El MCP real es "hf-bucket-mcp"
# (MCP oficial de HF, streamable HTTP, puerto 7860, bucket montado).
APK_OLD = '''{
  "edificio_1": {
    "s1": "https://comand-center-1-space-grupo-2-router-llm-hf-1.hf.space/v1/chat/completions",
    "s2": "https://comand-center-1-space-grupo-2-router-llm-hf-2.hf.space/v1/chat/completions",
    "s3": "https://comand-center-1-space-grupo-2-router-llm-hf-3.hf.space/v1/chat/completions"
  },
  "edificio_2": {
    "router": "https://comand-center-1-riu-router.hf.space",
    "mcp": "https://comand-center-1-riu-router.hf.space/mcp",
    "openclaw": "wss://comand-center-1-riu-router.hf.space:443/openclaw"
  },
  "auth_header": "X-API-Key",
  "timeout_s": 120
}
'''

APK_NEW = '''{
  "edificio_1": {
    "s1": "https://comand-center-1-space-grupo-2-router-llm-hf-1.hf.space/v1/chat/completions",
    "s2": "https://comand-center-1-space-grupo-2-router-llm-hf-2.hf.space/v1/chat/completions",
    "s3": "https://comand-center-1-space-grupo-2-router-llm-hf-3.hf.space/v1/chat/completions"
  },
  "edificio_2": {
    "router": "https://comand-center-1-space-grupo-1-router-mvp-1.hf.space",
    "mcp": "https://comand-center-1-hf-bucket-mcp.hf.space/mcp",
    "openclaw": "wss://comand-center-1-space-grupo-1-router-mvp-1.hf.space/v1/openclaw"
  },
  "auth_header": "X-API-Key",
  "timeout_s": 120,
  "nota": "El router son 2 grupos x 3 Spaces = 6 (Grupo 1 proxy, Grupo 2 LLM local). hf-bucket-mcp es el servidor MCP del bucket: infraestructura, no un grupo del router."
}
'''


def patch(path, old, new):
    """Reemplazo exacto; si el texto viejo no esta, no toca nada y avisa."""
    full = os.path.join(ROOT, path)
    with open(full, "r", encoding="utf-8") as fh:
        text = fh.read()
    if new in text and old not in text:
        print("SKIP (ya aplicado): {}".format(path))
        return True
    if old not in text:
        print("ABORT: patron no encontrado en {}".format(path))
        return False
    with open(full, "w", encoding="utf-8") as fh:
        fh.write(text.replace(old, new, 1))
    print("PATCH: {}".format(path))
    return True


def main():
    inv = os.path.join(ROOT, "external/core/space_inventory.py")
    if not os.path.exists(inv):
        with open(inv, "w", encoding="utf-8") as fh:
            fh.write(INVENTORY)
        print("NUEVO: external/core/space_inventory.py")
    else:
        print("EXISTE: external/core/space_inventory.py")

    ok = True
    ok &= patch("external/tools/space_power_manager.py", POWER_OLD, POWER_NEW)
    ok &= patch("external/tools/space_power_manager.py", POWER_ACTION_OLD, POWER_ACTION_NEW)
    ok &= patch("ROUTER MVP v1/system_prompt_py/health_check.py", HEALTH_OLD, HEALTH_NEW)
    ok &= patch("ROUTER MVP v1/system_prompt_py/inject_scaler.py", SCALER_OLD, SCALER_NEW)
    ok &= patch("ROUTER MVP v1/system_prompt_py/apk_config.json", APK_OLD, APK_NEW)
    if not ok:
        sys.exit(1)
    print("OP1_PATCH_OK")


if __name__ == "__main__":
    main()
