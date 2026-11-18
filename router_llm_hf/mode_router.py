"""mode_router.py — Enruta por modo usando el registro central y los adapters de HF."""
import json, os, logging, urllib.request
from .mode_detector import detect_mode

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
    """Detecta el modo (si no viene) y devuelve el plan de enrutamiento."""
    prompt = ""
    for m in payload.get("messages", []):
        if m.get("role") == "user":
            prompt = m.get("content", "")
            break
    mode = payload.get("mode") or detect_mode(prompt)
    adapter = get_adapter_config(mode)
    return {
        "mode": mode,
        "base_model": adapter.get("base_model"),
        "lora": adapter.get("lora"),
        "dataset": adapter.get("dataset"),
        "adapter_config": adapter,
    }
