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
'''

POWER_OLD = '''GROUP_1_COMPUTE = ["local-llm-router", "local-llm-router-v2", "local-llm-router-v7"]
GROUP_2_LLM = ["swe-code-s1", "swe-code-s2", "swe-code-s3"]
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
    GROUP_1_COMPUTE = ["local-llm-router", "local-llm-router-v2", "local-llm-router-v7"]
    GROUP_2_LLM = ["swe-code-s1", "swe-code-s2", "swe-code-s3"]
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
        "local-llm-router", "local-llm-router-v2", "local-llm-router-v7",
        "swe-code-s1", "swe-code-s2", "swe-code-s3",
    ]
'''

HEALTH_OLD = '''import httpx
import asyncio

SPACES = [
    "swe-code-s1", "swe-code-s2", "swe-code-s3",
    "riu-router", "claude-github-mcp-backup", "swe-code-web"
]
'''

HEALTH_NEW = '''import httpx
import asyncio

''' + BOOTSTRAP

SCALER_OLD = '''SPACES = ["swe-code-s1", "swe-code-s2", "swe-code-s3", "riu-router", "claude-github-mcp-backup", "swe-code-web"]
'''

SCALER_NEW = BOOTSTRAP

# Tercer bug real de la misma familia: apk_config.json apuntaba al Space MUERTO
# "riu-router" (404) en sus 3 entradas. El MCP real es "hf-bucket-mcp"
# (MCP oficial de HF, streamable HTTP, puerto 7860, bucket montado).
APK_OLD = '''{
  "edificio_1": {
    "s1": "https://comand-center-1-swe-code-s1.hf.space/v1/chat/completions",
    "s2": "https://comand-center-1-swe-code-s2.hf.space/v1/chat/completions",
    "s3": "https://comand-center-1-swe-code-s3.hf.space/v1/chat/completions"
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
    "s1": "https://comand-center-1-swe-code-s1.hf.space/v1/chat/completions",
    "s2": "https://comand-center-1-swe-code-s2.hf.space/v1/chat/completions",
    "s3": "https://comand-center-1-swe-code-s3.hf.space/v1/chat/completions"
  },
  "edificio_2": {
    "router": "https://comand-center-1-local-llm-router.hf.space",
    "mcp": "https://comand-center-1-hf-bucket-mcp.hf.space/mcp",
    "openclaw": "wss://comand-center-1-local-llm-router.hf.space/v1/openclaw"
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
