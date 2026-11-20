"""
download_manager.py — Motor unificado de descarga selectiva (Capa Externa)
Ubicacion: external/tools/download_manager.py
Regla: unico sistema permitido. ghgrab para GitHub, snapshot_download para HF.
"""
import os
import subprocess
import logging
from pathlib import Path
from huggingface_hub import snapshot_download

logger = logging.getLogger(__name__)


class DownloadManager:
    def __init__(self, cache_dir: str = "./external_cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def download_hf_model(self, repo_id: str, allow_patterns: list = None) -> str:
        """Descarga modelo o dataset de Hugging Face con reanudacion."""
        logger.info(f"Descargando HF: {repo_id}")
        path = snapshot_download(
            repo_id=repo_id,
            cache_dir=str(self.cache_dir),
            allow_patterns=allow_patterns,
            resume_download=True,
            local_files_only=False,
        )
        logger.info(f"Descarga completada en: {path}")
        return path

    def download_github_folder(self, repo_url: str, folder_path: str, output_dir: str) -> str:
        """Descarga carpeta especifica de GitHub usando ghgrab."""
        out_path = Path(output_dir)
        out_path.mkdir(parents=True, exist_ok=True)

        cmd = ["ghgrab", "download", f"{repo_url}/tree/main/{folder_path}", "--output", str(out_path)]
        logger.info(f"Ejecutando: {' '.join(cmd)}")

        try:
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            logger.info(f"ghgrab exito: {result.stdout}")
            return str(out_path)
        except subprocess.CalledProcessError as e:
            logger.error(f"ghgrab fallo: {e.stderr}")
            raise RuntimeError(f"Fallo descarga de {folder_path}: {e.stderr}")

    def verify_checksum(self, file_path: str, expected_sha256: str) -> bool:
        """Verifica integridad del archivo descargado."""
        import hashlib
        h = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                h.update(chunk)
        actual = h.hexdigest()
        if actual != expected_sha256:
            logger.error(f"Checksum fallo: esperado {expected_sha256}, obtenido {actual}")
            return False
        return True
