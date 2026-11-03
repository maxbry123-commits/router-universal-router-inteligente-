"""Catalogo unico de modelos, agentes y workflows. Ambos chats lo consultan por el Harness; no se copia a otro backend.
El catalogo identifica modelos: la disponibilidad real se comprueba contra el proveedor (GET /models)."""

MODELOS = {
    "hf/lfm2.5-350m": {"provider": "hf", "model": "lfm2.5-350m"},
    "hf/qwen2.5-coder-1.5b": {"provider": "hf", "model": "qwen2.5-coder-1.5b"},
    "hf/qwen3.5-0.8b": {"provider": "hf", "model": "qwen3.5-0.8b"},
    "hf/qwen3-0.6b": {"provider": "hf", "model": "qwen3-0.6b"},
    # Cuentas web del bridge: sólo IDs reales publicados por /v1/models.
    # Estos modelos se pueden usar por el runtime OpenClaw sin LLM traductor.
    "swecode-consulta": {"provider": "web", "model": "swecode-consulta"},
    "web-qwen38max": {"provider": "web", "model": "web-qwen38max"},
    "web-qwen37max": {"provider": "web", "model": "web-qwen37max"},
    "web-dsv4-flash": {"provider": "web", "model": "web-dsv4-flash"},
    "web-claude-sonnet": {"provider": "web", "model": "web-claude-sonnet"},
    "groq/qwen/qwen3.8-27b": {"provider": "groq", "model": "qwen/qwen3.8-27b"},
    "nvidia/minimaxai/minimax-m3.1-flash": {"provider": "nvidia", "model": "minimaxai/minimax-m3.1-flash"},
    "nvidia/meta/muse-glimmer-30b": {"provider": "nvidia", "model": "meta/muse-glimmer-30b"},
    "nvidia/nvidia/nemotron-3-ultra-550b-a55b": {"provider": "nvidia", "model": "nvidia/nemotron-3-ultra-550b-a55b"},
    "nvidia/z-ai/glm-5.3": {"provider": "nvidia", "model": "z-ai/glm-5.3"},
}
# Nombres para mostrar (UNICA fuente: el frontend y el bridge los consumen por /chat/swe/capacidades; ninguno mantiene su propia lista).
NOMBRES = {
    "hf/lfm2.5-350m": "LFM2.5 350M (HF local)",
    "hf/qwen2.5-coder-1.5b": "Qwen2.5-Coder 1.5B (HF local)",
    "hf/qwen3.5-0.8b": "Qwen3.5 0.8B (HF local)",
    "hf/qwen3-0.6b": "Qwen3 0.6B (HF local)",
    "swecode-consulta": "Ask Cónsil · arbitra Qwen 3.8 Max",
    "web-qwen38max": "Qwen 3.8 Max · web",
    "web-qwen37max": "Qwen 3.7 Max · web",
    "web-dsv4-flash": "DeepSeek V4 Flash · web",
    "web-claude-sonnet": "Claude Sonnet · web",
    "groq/qwen/qwen3.8-27b": "Qwen 3.8 27B",
    "nvidia/minimaxai/minimax-m3.1-flash": "MiniMax M3.1 Flash",
    "nvidia/meta/muse-glimmer-30b": "Muse Glimmer 30B",
    "nvidia/nvidia/nemotron-3-ultra-550b-a55b": "Nemotron 3 Ultra 550B",
    "nvidia/z-ai/glm-5.3": "GLM 5.3",
}
# Notas verificadas contra la documentacion OFICIAL (informativas; la disponibilidad real sale siempre de GET /models del proveedor).
NOTAS = {
    "nvidia/z-ai/glm-5.3": "GLM-5.3 se mantiene deshabilitado mientras NVIDIA no lo liste: build.nvidia.com/z-ai/glm-5.3 devuelve 404 (comprobado 2026-11-01)",
    "groq/qwen/qwen3.8-27b": "Groq lo publica como Preview (console.groq.com/docs/models): max 16,384 tokens de salida, contexto 131,072",
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


def catalogo():
    """Lista ordenada del catalogo unico para cualquier chat: [{id, nombre, proveedor, modelo}]. La disponibilidad se pide aparte (disponibilidad.capacidades)."""
    return [{"id": mid, "nombre": NOMBRES.get(mid, mid), "proveedor": m["provider"], "modelo": m["model"]} for mid, m in MODELOS.items()]


def compatible(agente, modelo, permitidos=None):
    """(bool, motivo): ¿puede ese agente usar ese modelo? Regla unica: ambos deben estar en el catalogo y, si el agente solo admite ciertos modelos
    (p. ej. Claude Code solo usa el modelo NVIDIA que sirve su pasarela; `permitidos` lo aporta disponibilidad.capacidades), el modelo debe figurar entre ellos."""
    if agente not in AGENTES:
        return False, "agente fuera del catalogo: " + str(agente)
    if modelo not in MODELOS:
        return False, "modelo fuera del catalogo: " + str(modelo)
    if permitidos is not None and modelo not in permitidos:
        return False, "%s solo admite: %s" % (agente, ", ".join(permitidos) or "ninguno")
    return True, ""
