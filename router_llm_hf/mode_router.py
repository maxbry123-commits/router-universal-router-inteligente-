"""mode_router.py — Enruta por modo usando el registro central y los adapters de HF.

FUSION (Op2 + MiniMax 2D):MiniMax 2D dejo VALID_MODES con 4 modos
(python, backend, architecture, agentic_tool) y route() devolvia
"invalid_mode" para 11 de los 12 modos del detector (el detector NUNCA devuelve
"python"/"backend"/"agentic_tool": solo "architecture" coincidia). Ademas el
detector y las carpetas del repo de adapters de HF no comparten nombres (solo 5
de 12), asi que route() pedia adapters inexistentes y devolvia base_model=None.

Solucion: una sola lista de modos validos (12 del detector + 4 de servicio + los
nombres de carpeta de HF) y un alias explicito detector -> carpeta del adapter.
Los modos sin equivalente (reasoning, planning) se declaran None: NO se inventa
adapter. 2026-11-18: ambos tienen ya adapter real en HF (reasoning: IFM/Code-Reasoning
code-thinking-hard, planning: multimodal-reasoning-lab/Robot-Planning), asi que el alias
apunta a su propia carpeta.
"""
import json, os, logging, urllib.request
from .mode_detector import detect_mode, RULES, SERVICE_MODE_NAMES

# Repo de adapters de HF: 12 carpetas de codigo + 4 de servicio (Op3).
_ADAPTER_REPO = "COMAND-CENTER-1/swe-code-adapters"
HF_ADAPTERS_BASE = "https://huggingface.co/{}/resolve/main".format(_ADAPTER_REPO)

# Modos validos: los del detector + los de servicio + los nombres de carpeta de
# HF (python, backend, agentic_tool) que MiniMax 2D uso como subset de fix3.
VALID_MODES = list(RULES) + list(SERVICE_MODE_NAMES) + ["python", "backend", "agentic_tool"]

# Alias explicito: modo del detector -> carpeta del adapter en HF.
HF_ADAPTER_ALIAS = {
    "code_generate": "python",
    "code_debug": "code_review",
    "code_refactor": "verification_refactor",
    "verification": "verification_refactor",
    "tool_call": "agentic_tool",
    "reasoning": "reasoning",
    "planning": "planning",
    # modos de servicio: adapters propios en HF
    "swe_code": "swe_code",
    "swe_free": "swe_free",
    "team_qwe": "team_qwe",
    "deployment": "deployment",
}

logger = logging.getLogger(__name__)
REGISTRY_PATH = os.path.join(os.path.dirname(__file__), "SATELITE_CENTRAL_CONECCION.json")

# Cache simple de adapter_config para no golpear HF en cada request
_ADAPTER_CACHE = {}


def _verify_adapter(mode: str) -> dict:
    """Verifica adapter_config.json en HF. Devuelve cfg o {'error': ...}."""
    url = "{}/{}/adapter_config.json".format(HF_ADAPTERS_BASE, mode)
    try:
        with urllib.request.urlopen(url, timeout=8) as r:
            if r.status != 200:
                return {"error": "http_{}".format(r.status)}
            return json.loads(r.read())
    except Exception as e:
        return {"error": "{}:{}".format(type(e).__name__, e)}


def adapter_name_for_mode(mode: str):
    """Carpeta del adapter en HF para un modo (o None si ese modo no tiene)."""
    if mode in HF_ADAPTER_ALIAS:
        return HF_ADAPTER_ALIAS[mode]
    return mode


def get_adapter_config(mode: str) -> dict:
    """Adapter del modo (cacheado). Vacio si ese modo no tiene adapter."""
    if mode in _ADAPTER_CACHE:
        return _ADAPTER_CACHE[mode]
    name = adapter_name_for_mode(mode)
    if not name:
        _ADAPTER_CACHE[mode] = {}
        return {}
    adapter = _verify_adapter(name)
    _ADAPTER_CACHE[mode] = {} if adapter.get("error") else adapter
    return _ADAPTER_CACHE[mode]


def load_registry():
    if not os.path.exists(REGISTRY_PATH):
        logger.warning("Registro central no encontrado.")
        return {}
    with open(REGISTRY_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def route(payload: dict) -> dict:
    """Detecta el modo (si no viene) y devuelve el plan de enrutamiento."""
    try:
        return _route_impl(payload)
    except Exception as e:
        return {"error": str(e), "mode": payload.get("mode")}


def _route_impl(payload: dict) -> dict:
    prompt = ""
    for m in payload.get("messages", []):
        if m.get("role") == "user":
            prompt = m.get("content", "")
            break
    mode = payload.get("mode") or detect_mode(prompt)
    if mode not in VALID_MODES:
        return {"mode": mode, "error": "invalid_mode, valid={}".format(sorted(VALID_MODES))}
    adapter = get_adapter_config(mode)
    if not adapter:
        return {
            "mode": mode,
            "adapter_mode": adapter_name_for_mode(mode),
            "adapter_config": {},
            "dataset": None,
            "base_model": None,
            "lora": None,
            "error": "adapter_not_found",
        }
    return {
        "mode": mode,
        "adapter_mode": adapter_name_for_mode(mode),
        "adapter_config": adapter,
        # "dataset" es el repo FUENTE; "dataset_combined"/"dataset_path" son los
        # ficheros reales de COMAND-CENTER-1/swe-code-modes.
        "dataset": adapter.get("dataset"),
        "dataset_combined": adapter.get("dataset_combined"),
        "dataset_path": adapter.get("dataset_path"),
        "base_model": adapter.get("base_model"),
        "lora": adapter.get("lora"),
        "lora_path": adapter.get("lora_path"),
    }
