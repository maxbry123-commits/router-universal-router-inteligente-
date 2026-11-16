"""storage_wiring.py — Asegura que el Bucket de memoria existe y está conectado."""
import os
import logging
from huggingface_hub import HfApi, HfHubHTTPError

logger = logging.getLogger(__name__)
api = HfApi(token=os.getenv("HF_TOKEN"))
BUCKET_ID = "COMAND-CENTER-1/yaiwes-memoria-storage"

class StorageWiring:
    @staticmethod
    def ensure_bucket() -> dict:
        """Verifica si el bucket existe; si no, lo crea."""
        try:
            api.repo_info(repo_id=BUCKET_ID, repo_type="bucket")
            logger.info(f"Bucket {BUCKET_ID} ya existe.")
            return {"status": "exists", "bucket": BUCKET_ID}
        except Exception:
            logger.warning(f"Bucket {BUCKET_ID} no encontrado. Creando...")
            try:
                api.create_repo(repo_id=BUCKET_ID, repo_type="bucket", private=True)
                return {"status": "created", "bucket": BUCKET_ID}
            except Exception as e:
                logger.error(f"Fallo al crear bucket: {e}")
                return {"status": "error", "detail": str(e)}

    @staticmethod
    def verify_storage_connection() -> bool:
        """Verifica que el bucket está enlazado correctamente."""
        res = StorageWiring.ensure_bucket()
        return res.get("status") in ["exists", "created"]
