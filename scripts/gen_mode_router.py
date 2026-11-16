"""gen_mode_router.py — Genera router_llm_hf/mode_router.py que lee el registro
central y los adapter_config.json de HF para enrutar por modo.
"""
import os

OUT = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "router_llm_hf", "mode_router.py",
)

CODE = r'''"""mode_router.py — Enruta por modo usando el registro central y los adapters de HF."""
import json, os, logging, urllib.request
from .mode_detector import detect_mode

logger = logging.getLogger(__name__)
REGISTRY_PATH = os.path.join(os.path.dirname(__file__), "SATELITE_CENTRAL_CONECCION.json")
HF_ADAPTERS_BASE = "https://huggingface.co/COMAND-CENTER-1/swe-code-adapters/resolve/main"

def load_registry():
    if not os.path.exists(REGISTRY_PATH):
        logger.warning("Registro central no encontrado.")
        return {}
    with open(REGISTRY_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def get_adapter_config(mode: str) -> dict:
    """Lee el adapter_config.json del repo de HF (vía URL raw)."""
    url = f"{HF_ADAPTERS_BASE}/{mode}/adapter_config.json"
    try:
        with urllib.request.urlopen(url, timeout=5) as r:
            return json.loads(r.read().decode())
    except Exception as e:
        logger.warning(f"No se pudo leer adapter_config para {mode}: {e}")
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
'''

def main():
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(CODE)
    print(f"mode_router.py escrito en {OUT}")

if __name__ == "__main__":
    main()
