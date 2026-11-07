# mode_router_v2.py
import json
from typing import Dict, Optional

MODES_CONFIG = {
    "programacion": {
        "keywords": ["programa", "escribe", "crea", "función", "script"],
        "dataset": "NickIBrody/python-code-instructions-85k",
        "adapter": {"qwen2.5": "driaforall/Tiny-Agent-a-0.5B", "qwen3.5": "mstrasser/Jeff-Qwen3.5-0.8B-tools", "lfm2.5": "ermiaazarkhalili/LFM2.5-350M-Function-Calling-xLAM-Unsloth"},
        "coupler": "pythonic_tool_calling",
        "prompt": "MODO PROGRAMACIÓN: Código modular, comentado, sin mocks."
    },
    "refactor": {
        "keywords": ["refactorizar", "optimizar", "limpiar", "mejorar código"],
        "dataset": "KavinduHansaka/Python_Refactor_Dataset",
        "adapter": {"qwen2.5": "driaforall/Tiny-Agent-a-0.5B", "qwen3.5": "mstrasser/Jeff-Qwen3.5-0.8B-tools", "lfm2.5": "hauser458b/lfm2.5-350m-python-math"},
        "coupler": "yagni_enforcer",
        "prompt": "MODO REFACTOR: Mejora legibilidad y rendimiento sin cambiar funcionalidad."
    },
    "forense": {
        "keywords": ["error", "fallo", "bug", "auditar", "traceback", "seguridad"],
        "dataset": "scthornton/securecode-web",
        "adapter": {"qwen2.5": "girish00/ConicAI_LLM_model", "qwen3.5": "mstrasser/Jeff-Qwen3.5-0.8B-tools", "lfm2.5": "distil-labs/distil-lfm25-shellper"},
        "coupler": "security_gate",
        "prompt": "MODO FORENSE: Analiza causa raíz y vulnerabilidades. Cita ruta:línea."
    },
    "frontend": {
        "keywords": ["react", "html", "css", "interfaz", "diseño", "ui"],
        "dataset": "xlelords/vulcan",
        "adapter": {"qwen2.5": "girish00/ConicAI_LLM_model", "qwen3.5": "mstrasser/Jeff-Qwen3.5-0.8B-tools", "lfm2.5": "ermiaazarkhalili/LFM2.5-350M-Function-Calling-xLAM-Unsloth"},
        "coupler": "ui_component_generator",
        "prompt": "MODO FRONTEND: Usa Tailwind/React. Componentes autocontenidos."
    },
    "backend": {
        "keywords": ["fastapi", "flask", "sql", "base de datos", "endpoint"],
        "dataset": "b-mc2/sql-create-context",
        "adapter": {"qwen2.5": "driaforall/Tiny-Agent-a-0.5B", "qwen3.5": "mstrasser/Jeff-Qwen3.5-0.8B-tools", "lfm2.5": "distil-labs/distil-lfm25-shellper"},
        "coupler": "api_contract_validator",
        "prompt": "MODO BACKEND: APIs robustas, validación de entrada, SQL parametrizado."
    },
    "agentico": {
        "keywords": ["agente", "tool", "herramienta", "decide", "planifica"],
        "dataset": "alibayram/qwen3.5-toolcalling-v2",
        "adapter": {"qwen2.5": "driaforall/Tiny-Agent-a-0.5B", "qwen3.5": "mstrasser/Jeff-Qwen3.5-0.8B-tools", "lfm2.5": "ermiaazarkhalili/LFM2.5-350M-Function-Calling-xLAM-Unsloth"},
        "coupler": "pythonic_tool_calling",
        "prompt": "MODO AGÉNTICO: Usa herramientas. Reporta GAP_DETECTADO si falta info."
    },
    "validacion": {
        "keywords": ["test", "probar", "verificar", "pytest", "unit test"],
        "dataset": "Arain/UnitTest-Finetuning",
        "adapter": {"qwen2.5": "driaforall/Tiny-Agent-a-0.5B", "qwen3.5": "mstrasser/Jeff-Qwen3.5-0.8B-tools", "lfm2.5": "distil-labs/distil-lfm25-shellper"},
        "coupler": "test_runner",
        "prompt": "MODO VALIDACIÓN: Tests unitarios. Si falla, corrige y reintenta."
    },
    "documentacion": {
        "keywords": ["docstring", "readme", "comentar", "documentar"],
        "dataset": "argilla/Synth-APIGen-v0.1",
        "adapter": {"qwen2.5": "girish00/ConicAI_LLM_model", "qwen3.5": "mstrasser/Jeff-Qwen3.5-0.8B-tools", "lfm2.5": "ermiaazarkhalili/LFM2.5-350M-Function-Calling-xLAM-Unsloth"},
        "coupler": "doc_generator",
        "prompt": "MODO DOCUMENTACIÓN: Docstrings completos, README ejecutable."
    },
    "optimizacion": {
        "keywords": ["rendimiento", "latencia", "optimizar", "yagni"],
        "dataset": "KavinduHansaka/Python_Refactor_Dataset",
        "adapter": {"qwen2.5": "driaforall/Tiny-Agent-a-0.5B", "qwen3.5": "mstrasser/Jeff-Qwen3.5-0.8B-tools", "lfm2.5": "hauser458b/lfm2.5-350m-python-math"},
        "coupler": "yagni_enforcer",
        "prompt": "MODO OPTIMIZACIÓN: YAGNI. stdlib antes que dependencias."
    },
    "investigacion": {
        "keywords": ["investiga", "busca", "documentación", "referencia"],
        "dataset": "nuhmanpk/dev-knowledge-base",
        "adapter": {"qwen2.5": "girish00/ConicAI_LLM_model", "qwen3.5": "kinit/qwen3.5-0.8B-extract-ml-conversations-qlora", "lfm2.5": "ermiaazarkhalili/LFM2.5-350M-Function-Calling-xLAM-Unsloth"},
        "coupler": "rag_context_builder",
        "prompt": "MODO INVESTIGACIÓN: Usa contexto web. Cita fuentes. No inventes."
    },
    "planificacion": {
        "keywords": ["plan", "roadmap", "divide", "arquitectura"],
        "dataset": "NickIBrody/python-code-instructions-85k",
        "adapter": {"qwen2.5": "driaforall/Tiny-Agent-a-0.5B", "qwen3.5": "mstrasser/Jeff-Qwen3.5-0.8B-tools", "lfm2.5": "distil-labs/distil-lfm25-shellper"},
        "coupler": "task_decomposer",
        "prompt": "MODO PLANIFICACIÓN: Divide en bloques ≤200 LOC. Genera plan_sha256."
    },
    "debugging": {
        "keywords": ["debug", "traceback", "error", "no funciona"],
        "dataset": "scthornton/securecode-web",
        "adapter": {"qwen2.5": "girish00/ConicAI_LLM_model", "qwen3.5": "mstrasser/Jeff-Qwen3.5-0.8B-tools", "lfm2.5": "distil-labs/distil-lfm25-shellper"},
        "coupler": "traceback_analyzer",
        "prompt": "MODO DEBUGGING: Lee traceback de abajo hacia arriba. Corrige causa raíz."
    }
}

def detect_mode(user_input: str) -> Optional[str]:
    text = user_input.lower()
    best_mode, best_score = None, 0
    for mode, cfg in MODES_CONFIG.items():
        score = sum(1 for kw in cfg["keywords"] if kw in text)
        if score > best_score:
            best_mode, best_score = mode, score
    return best_mode

def get_mode_config(mode: str, model_family: str = "qwen2.5") -> dict:
    cfg = MODES_CONFIG.get(mode)
    if not cfg:
        return {"error": f"Modo '{mode}' no reconocido"}
    return {
        "mode": mode,
        "dataset": cfg["dataset"],
        "adapter": cfg["adapter"].get(model_family, cfg["adapter"]["qwen2.5"]),
        "coupler": cfg["coupler"],
        "prompt": cfg["prompt"]
    }

def route(user_input: str, model_family: str = "qwen2.5") -> dict:
    mode = detect_mode(user_input)
    if not mode:
        mode = "programacion"
    return get_mode_config(mode, model_family)
