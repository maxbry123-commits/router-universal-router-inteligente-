MODES_CONFIG = {
    "programacion": {"keywords": ["programa", "escribe", "crea", "función"], "dataset": "NickIBrody/python-code-instructions-85k", "adapter": "driaforall/Tiny-Agent-a-0.5B"},
    "refactor": {"keywords": ["refactorizar", "optimizar", "limpiar"], "dataset": "KavinduHansaka/Python_Refactor_Dataset", "adapter": "mstrasser/Jeff-Qwen3.5-0.8B-tools"},
    "forense": {"keywords": ["error", "fallo", "bug", "auditar"], "dataset": "scthornton/securecode-web", "adapter": "ermiaazarkhalili/LFM2.5-350M-Function-Calling-xLAM-Unsloth"},
    "frontend": {"keywords": ["react", "html", "css", "interfaz"], "dataset": "xlelords/vulcan", "adapter": "mstrasser/Jeff-Qwen3.5-0.8B-tools"},
    "backend": {"keywords": ["fastapi", "flask", "sql", "base de datos"], "dataset": "b-mc2/sql-create-context", "adapter": "Salesforce/xlam-function-calling-60k"},
    "agentico": {"keywords": ["agente", "tool", "herramienta"], "dataset": "alibayram/qwen3.5-toolcalling-v2", "adapter": "mstrasser/Jeff-Qwen3.5-0.8B-tools"},
    "validacion": {"keywords": ["test", "probar", "verificar"], "dataset": "Arain/UnitTest-Finetuning", "adapter": "driaforall/Tiny-Agent-a-0.5B"},
    "documentacion": {"keywords": ["docstring", "readme", "comentar"], "dataset": "argilla/Synth-APIGen-v0.1", "adapter": "girish00/ConicAI_LLM_model"},
    "optimizacion": {"keywords": ["rendimiento", "latencia", "optimizar"], "dataset": "KavinduHansaka/Python_Refactor_Dataset", "adapter": "hauser458b/lfm2.5-350m-python-math"},
    "investigacion": {"keywords": ["investiga", "busca", "documentación"], "dataset": "nuhmanpk/dev-knowledge-base", "adapter": "kinit/qwen3.5-0.8B-extract-ml-conversations-qlora"},
    "planificacion": {"keywords": ["plan", "roadmap", "divide"], "dataset": "NickIBrody/python-code-instructions-85k", "adapter": "driaforall/Tiny-Agent-a-0.5B"},
    "debugging": {"keywords": ["debug", "traceback", "error"], "dataset": "scthornton/securecode-web", "adapter": "girish00/ConicAI_LLM_model"}
}

def detect_mode(user_input: str) -> str:
    text = user_input.lower()
    best_mode, best_score = "programacion", 0
    for mode, cfg in MODES_CONFIG.items():
        score = sum(1 for kw in cfg["keywords"] if kw in text)
        if score > best_score:
            best_mode, best_score = mode, score
    return best_mode

def route(user_input: str, model_family: str = "qwen2.5") -> dict:
    mode = detect_mode(user_input)
    cfg = MODES_CONFIG[mode]
    return {"mode": mode, "dataset": cfg["dataset"], "adapter": cfg["adapter"]}
