"""storage_wiring.py — Adaptador del núcleo (MINIMAX 4).

Reexporta el cableado de almacenamiento implementado en
external/tools/storage_wiring.py para el cableado del ciclo de vida del proxy
(verificación del bucket de memoria en el startup).

FIX (MINIMAX 2E) — por qué este adaptador ya no es un simple reexport:
  · external/tools/storage_wiring.py usa `repo_type="bucket"`, que NO existe en
    huggingface_hub (validos: model | dataset | space) -> repo_info() y
    create_repo() fallan siempre -> el proxy reportaba storage roto SIEMPRE.
  · ademas hacia un create_repo() en cada arranque: una escritura en HF en cada
    reinicio del Space (y sin PRO/creditos eso es un 402 garantizado).

Este adaptador (la capa que consume el proxy):
  · VERIFICA el bucket con la API real de buckets (GET, solo lectura).
  · NO crea nada: si el bucket no existe, lo dice y lo deja para el operador
    (o para el MINIMAX de HF), sin escribir en HF desde el arranque.
  · Mantiene la API que consume el proxy: ensure_bucket() / verify_storage_connection().
"""
from __future__ import annotations

import json
import logging
import os
import urllib.error
import urllib.request

logger = logging.getLogger(__name__)

BUCKET_NAMESPACE = os.getenv("HF_BUCKET_NAMESPACE", "COMAND-CENTER-1")
BUCKET_NAME = os.getenv("HF_BUCKET_NAME", "yaiwes-memoria-storage")
BUCKET_ID = f"{BUCKET_NAMESPACE}/{BUCKET_NAME}"
BUCKET_API = "https://huggingface.co/api/buckets"


class StorageWiring:
    """Verificacion (solo lectura) del bucket de memoria."""

    @staticmethod
    def _token() -> str:
        return os.getenv("HF_TOKEN") or os.getenv("HF_TOKEN_1_NEW") or ""

    @staticmethod
    def _get(url: str, token: str, timeout: int = 15):
        req = urllib.request.Request(url, method="GET")
        if token:
            req.add_header("Authorization", f"Bearer {token}")
        req.add_header("Accept", "application/json")
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.status, r.read().decode("utf-8", "replace")
        except urllib.error.HTTPError as e:
            return e.code, e.read().decode("utf-8", "replace")
        except Exception as e:
            return 0, f"{type(e).__name__}: {e}"

    @staticmethod
    def ensure_bucket() -> dict:
        """Comprueba (sin escribir) si el bucket de memoria existe."""
        token = StorageWiring._token()
        status, body = StorageWiring._get(f"{BUCKET_API}/{BUCKET_NAMESPACE}/{BUCKET_NAME}", token)
        if status == 200:
            info = {}
            try:
                info = json.loads(body)
            except Exception:
                info = {}
            logger.info(f"Bucket {BUCKET_ID} verificado (HTTP 200).")
            return {"status": "exists", "bucket": BUCKET_ID, "http": status, "info": info}
        if status == 404:
            logger.warning(f"Bucket {BUCKET_ID} no existe (404). No se crea desde aqui.")
            return {"status": "missing", "bucket": BUCKET_ID, "http": status}
        logger.error(f"Bucket {BUCKET_ID}: no verificable (HTTP {status}).")
        return {"status": "error", "bucket": BUCKET_ID, "http": status, "detail": body[:200]}

    @staticmethod
    def verify_storage_connection() -> bool:
        """True solo si el bucket responde 200 de verdad."""
        res = StorageWiring.ensure_bucket()
        return res.get("status") == "exists"
