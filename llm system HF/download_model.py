"""download_model.py — Descarga el GGUF del dataset HF al arrancar el Space.
Este archivo SÍ va en GitHub porque es runtime (lo llama entrypoint.sh).
"""
import os, sys, hashlib, logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="[download] %(message)s")
logger = logging.getLogger(__name__)

MODEL_REPO = os.getenv("MODEL_REPO", "COMAND-CENTER-1/swe-code-hf-gguf")
MODEL_FILE = os.getenv("MODEL_FILE")
MODEL_PATH = os.getenv("MODEL_PATH", "")
HF_TOKEN = os.getenv("HF_TOKEN", "")


def sha256_of(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    if not MODEL_FILE:
        logger.error("MODEL_FILE no configurado")
        return 1
    if not HF_TOKEN:
        logger.error("HF_TOKEN no configurado")
        return 1
    dest = Path(MODEL_PATH) if MODEL_PATH else Path("/data/models") / MODEL_FILE
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists():
        logger.info(f"Ya existe: {dest} ({dest.stat().st_size} B, sha={sha256_of(str(dest))[:16]}...)")
        return 0
    try:
        from huggingface_hub import hf_hub_download
    except ImportError:
        logger.error("huggingface_hub no instalado")
        return 1
    try:
        logger.info(f"Descargando {MODEL_REPO}/{MODEL_FILE}")
        local = hf_hub_download(
            repo_id=MODEL_REPO, filename=MODEL_FILE,
            repo_type="dataset", token=HF_TOKEN,
            local_dir=str(dest.parent),
        )
        logger.info(f"OK: {local} ({Path(local).stat().st_size} B)")
        return 0
    except Exception as e:
        logger.error(f"Falló descarga: {type(e).__name__}: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
