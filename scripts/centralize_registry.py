"""centralize_registry.py — Centraliza el registro de cableado existente.
Trae SATÉLITE CENTRAL CONECCION.yaml de main (si no está en ccr),
lo fusiona con SYSTEM_WIRING_REGISTRY.yaml y escribe
router_llm_hf/SATELITE_CENTRAL_CONECCION.json SIN secretos.
"""
import json, os, subprocess, logging
import yaml

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAIN_YAML = os.path.join(ROOT, "SATÉLITE CENTRAL CONECCION", "SATÉLITE CENTRAL CONECCION.yaml")
CCR_YAML = os.path.join(ROOT, "SYSTEM_WIRING_REGISTRY.yaml")
OUT_JSON = os.path.join(ROOT, "router_llm_hf", "SATELITE_CENTRAL_CONECCION.json")

def ensure_main_yaml():
    """Si el YAML de main no está en la rama actual, lo trae con git checkout."""
    if not os.path.exists(MAIN_YAML):
        logger.info("Trayendo SATÉLITE CENTRAL CONECCION.yaml de main...")
        subprocess.run(
            ["git", "checkout", "main", "--",
             "SATÉLITE CENTRAL CONECCION/SATÉLITE CENTRAL CONECCION.yaml"],
            check=True, cwd=ROOT,
        )
    return MAIN_YAML

def load_yaml(path):
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}

def main():
    ensure_main_yaml()
    main_data = load_yaml(MAIN_YAML)
    ccr_data = load_yaml(CCR_YAML)

    merged = {
        "version": "1.0",
        "fuente_maestra": "SATÉLITE CENTRAL CONECCION.yaml (main) + SYSTEM_WIRING_REGISTRY.yaml (ccr)",
        "plataformas": main_data.get("plataformas", {}),
        "componentes": main_data.get("componentes", []),
        "umbral_active": main_data.get("umbral_active", {}),
        "conexiones": {
            "main": main_data.get("conexiones", []),
            "ccr": ccr_data.get("conexiones", []),
        },
        "nota": "Registro central sin secretos. Los 10 MCP/HTTP viven en HF Secrets.",
    }

    os.makedirs(os.path.dirname(OUT_JSON), exist_ok=True)
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(merged, f, indent=2, ensure_ascii=False)
    logger.info(f"Registro central escrito en {OUT_JSON}")

if __name__ == "__main__":
    main()
