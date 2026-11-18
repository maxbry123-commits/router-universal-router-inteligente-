"""mode_router.py — Enruta por modo usando el registro central y los adapters de HF."""
import json, os, logging, urllib.request
from .mode_detector import detect_mode

VALID_MODES = ['python', 'backend', 'architecture', 'agentic_tool']
_ADAPTER_REPO = "COMAND-CENTER-1/swe-code-adapters"

def _verify_adapter(mode: str) -> dict:
    """Verifica adapter_config.json en HF. Devuelve cfg o {'error': ...}."""
    import json, urllib.request
    url = f"https://huggingface.co/{_ADAPTER_REPO}/resolve/main/{mode}/adapter_config.json"
    try:
        with urllib.request.urlopen(url, timeout=8) as r:
            if r.status != 200:
                return {"error": f"http_{r.status}"}
            return json.loads(r.read())
    except Exception as e:
        return {"error": f"{type(e).__name__}:{e}"}


logger = logging.getLogger(__name__)
REGISTRY_PATH = os.path.join(os.path.dirname(__file__), "SATELITE_CENTRAL_CONECCION.json")
HF_ADAPTERS_BASE = "https://huggingface.co/COMAND-CENTER-1/swe-code-adapters/resolve/main"

# Cache simple de adapter_config para no golpear HF en cada request
_ADAPTER_CACHE = {}


def load_registry():
    if not os.path.exists(REGISTRY_PATH):
        logger.warning("Registro central no encontrado.")
        return {}
    with open(REGISTRY_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def get_adapter_config(mode: str) -> dict:
    """Lee el adapter_config.json del repo de HF (con cache en memoria)."""
    if mode in _ADAPTER_CACHE:
        return _ADAPTER_CACHE[mode]
    url = f"{HF_ADAPTERS_BASE}/{mode}/adapter_config.json"
    try:
        with urllib.request.urlopen(url, timeout=5) as r:
            data = json.loads(r.read().decode())
            _ADAPTER_CACHE[mode] = data
            return data
    except Exception as e:
        logger.warning(f"No se pudo leer adapter_config para {mode}: {e}")
        _ADAPTER_CACHE[mode] = {}
        return {}


def route(payload: dict) -> dict:
    try:
        return _route_impl(payload)
    except Exception as e:
        return {'error': str(e), 'mode': payload.get('mode')}

def _route_impl(payload: dict) -> dict:
    from .mode_detector import detect_mode
    prompt = ""
    for m in payload.get("messages", []):
        if m.get("role") == "user":
            prompt = m.get("content", ""); break
    mode = payload.get("mode") or detect_mode(prompt)
    if mode not in VALID_MODES:
        return {"mode": mode, "error": f"invalid_mode, valid={VALID_MODES}"}
    # Re-integrado (MiniMax 3, riesgo 4 del bloque): _ADAPTER_CACHE evita pedir
    # el adapter a HF en cada request; el shape cacheado es adapter_config.json.
    if mode in _ADAPTER_CACHE:
        adapter = _ADAPTER_CACHE[mode]
    else:
        adapter = _verify_adapter(mode)
        _ADAPTER_CACHE[mode] = {} if adapter.get("error") else adapter
    if adapter.get("error"):
        return {"mode": mode, "adapter_config": {},
                "dataset": None, "error": adapter["error"]}
    if not adapter:
        return {"mode": mode, "adapter_config": {},
                "dataset": None, "error": "adapter_not_found"}
    return {"mode": mode, "adapter_config": adapter,
            "dataset": adapter.get("dataset") or adapter.get("dataset_combined"),
            "base_model": adapter.get("base_model") or adapter.get("base_model_name_or_path"),
            "lora": adapter.get("lora")}
