"""Catalogo unico de modelos, agentes y workflows. Ambos chats lo consultan por el Harness; no se copia a otro backend.
El catalogo identifica modelos: la disponibilidad real se comprueba contra el proveedor (GET /models)."""

MODELOS = {
    "hf/lfm2.5-350m": {"provider": "hf", "model": "lfm2.5-350m"},
    "hf/qwen2.5-coder-1.5b": {"provider": "hf", "model": "qwen2.5-coder-1.5b"},
    "hf/qwen3.5-0.8b": {"provider": "hf", "model": "qwen3.5-0.8b"},
    "hf/qwen3-0.6b": {"provider": "hf", "model": "qwen3-0.6b"},
    "groq/qwen/qwen3.8-27b": {"provider": "groq", "model": "qwen/qwen3.8-27b"},
    "nvidia/minimaxai/minimax-m3.1-flash": {"provider": "nvidia", "model": "minimaxai/minimax-m3.1-flash"},
    "nvidia/meta/muse-glimmer-30b": {"provider": "nvidia", "model": "meta/muse-glimmer-30b"},
    "nvidia/nvidia/nemotron-3-ultra-550b-a55b": {"provider": "nvidia", "model": "nvidia/nemotron-3-ultra-550b-a55b"},
    "nvidia/z-ai/glm-5.3": {"provider": "nvidia", "model": "z-ai/glm-5.3"},
}
AGENTES = ("openclaw", "swe-agent", "openhands", "opencode", "codex", "claude-code",)
WORKFLOWS = ("individual", "swe_code", "liquid_mirror",)


def validar_modelo(identificador):
    if not isinstance(identificador, str) or identificador not in MODELOS:
        raise ValueError("MODELO_NO_REGISTRADO")
    return MODELOS[identificador]


def validar_agente(identificador):
    if not isinstance(identificador, str) or identificador not in AGENTES:
        raise ValueError("AGENTE_NO_REGISTRADO")


def validar_workflow(identificador):
    if not isinstance(identificador, str) or identificador not in WORKFLOWS:
        raise ValueError("WORKFLOW_NO_REGISTRADO")
