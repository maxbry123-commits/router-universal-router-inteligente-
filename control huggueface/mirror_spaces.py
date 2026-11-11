"""
mirror_spaces.py — Duplicar Spaces a region de respaldo (Salida 3/3)
Ubicacion: control huggueface/mirror_spaces.py
Rol: Objetivo 3.2. Usa HfApi.duplicate_repo. No ejecuta logica de negocio.
"""
import os
import logging
from huggingface_hub import HfApi

logger = logging.getLogger(__name__)
api = HfApi(token=os.getenv("HF_TOKEN"))


def mirror(source_id: str, dest_id: str = None, private: bool = True) -> dict:
    dest = dest_id or f"{source_id}-mirror"
    try:
        api.duplicate_repo(
            source_id,
            repo_type="space",
            target_repo=dest,
            private=private,
        )
        logger.info("Mirror OK: %s -> %s", source_id, dest)
        return {"status": "mirrored", "source": source_id, "dest": dest}
    except Exception as e:
        logger.warning("Mirror fallo %s: %s", source_id, e)
        return {"status": "failed", "source": source_id, "error": str(e)}


def mirror_all(space_ids: list) -> list:
    return [mirror(s) for s in space_ids]
