"""service_routes.py — Los 4 modos de SERVICIO del router (contrato unico).

No son modos entrenables: no tienen dataset ni LoRA. Son RUTAS del proxy. Por eso
el Director los pidio como "modos" y el prevalidador los daria 0/4 si se buscascan
adapter_config.json entrenables.

  swe_code    -> POST /v1/swe        (Grupo 2 · LLM local con clave; local primero)
  swe_free    -> POST /v1/swe-free    (Grupo 2 · LLM local gratuito; local primero)
  team_qwe    -> POST /v1/team-qwe    (orquestador multi-agente; proveedores)
  deployment  -> POST /v1/deployment  (despliegue; proveedores + guia)

Reparto del Grupo 2 (LLM local GGUF) — los 3 Spaces son reales:
  space-grupo-2-router-llm-hf-1 -> Qwen/Qwen2.5-Coder-0.5B-Instruct-GGUF  (modo swe_code)
  space-grupo-2-router-llm-hf-2 -> LiquidAI/LFM2.5-350M-GGUF              (modo team_qwe)
  space-grupo-2-router-llm-hf-3 -> unsloth/Qwen3.5-0.8B-GGUF             (modo swe_free)

Este modulo NO decide: solo declara el contrato. La decision la toma el proxy
(que lo lee) y el Control Plane (que lo enruta).
"""
from __future__ import annotations

NAMESPACE = "COMAND-CENTER-1"

SERVICE_MODES = {
    "swe_code": {
        "route": "/v1/swe",
        "space": "space-grupo-2-router-llm-hf-1",
        "model": "Qwen/Qwen2.5-Coder-0.5B-Instruct-GGUF",
        "local_first": True,
        "adapter_type": "service",
        "description": "Grupo 2 · LLM local con clave: ejecuta en el Space local del Grupo 2.",
    },
    "swe_free": {
        "route": "/v1/swe-free",
        "space": "space-grupo-2-router-llm-hf-3",
        "model": "unsloth/Qwen3.5-0.8B-GGUF",
        "local_first": True,
        "adapter_type": "service",
        "description": "Grupo 2 · LLM local gratuito: mismo codigo, ruta propia y coste cero.",
    },
    "team_qwe": {
        "route": "/v1/team-qwe",
        "space": "space-grupo-2-router-llm-hf-2",
        "model": "LiquidAI/LFM2.5-350M-GGUF",
        "local_first": False,
        "adapter_type": "service",
        "description": "Orquestador multi-agente: cadena de proveedores (el modelo local es demasiado pequeño).",
    },
    "deployment": {
        "route": "/v1/deployment",
        "space": None,
        "model": None,
        "local_first": False,
        "adapter_type": "service",
        "description": "Despliegue: cadena de proveedores + guia de despliegue del router.",
    },
}

# Ruta -> modo de servicio (para resolver por request.url.path)
ROUTE_TO_MODE = {cfg["route"]: mode for mode, cfg in SERVICE_MODES.items()}


def service_mode_for_path(path):
    """Modo de servicio de una ruta del proxy (o None)."""
    if not path:
        return None
    return ROUTE_TO_MODE.get(path.rstrip("/") or path)


def local_target_for_mode(mode):
    """(space, model) local del modo de servicio, o None si no usa Space local."""
    cfg = SERVICE_MODES.get(mode)
    if not cfg or not cfg.get("local_first"):
        return None
    return cfg["space"], cfg["model"]


def space_url(space, path=""):
    base = "https://comand-center-1-{}.hf.space".format(space)
    return "{}/{}".format(base, path.lstrip("/")) if path else base
