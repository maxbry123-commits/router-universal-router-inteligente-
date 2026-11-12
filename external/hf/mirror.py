"""mirror.py — duplicate_space() entre regiones (HF Control)
Usa HfApi.duplicate_space (no duplicate_repo, que no existe para spaces).
"""
import os
import logging
from huggingface_hub import HfApi

logger = logging.getLogger(__name__)

def _api() -> HfApi:
    token = os.getenv("HF_TOKEN")
    if not token:
        raise RuntimeError("HF_TOKEN no configurada")
    return HfApi(token=token)

def mirror_space(source_id: str, dest_id: str = None, private: bool = True) -> dict:
    dest = dest_id or f"{source_id}-mirror"
    try:
        api = _api()
        # duplicate_space espera from_space y to_name; derivar namespace de dest
        parts = dest.split("/")
        if len(parts) == 2:
            to_namespace, to_name = parts
        else:
            to_namespace = parts[0].split("/")[0] if "/" in source_id else None
            to_name = dest
        api.duplicate_space(
            from_space=source_id,
            to_namespace=to_namespace,
            new_name=to_name,
            private=private,
        )
        logger.info("Mirror OK: %s -> %s", source_id, dest)
        return {"status": "mirrored", "source": source_id, "dest": dest}
    except Exception as e:
        logger.warning("Mirror fallo %s: %s", source_id, e)
        return {"status": "failed", "source": source_id, "error": str(e)}

def mirror_all(space_ids: list) -> list:
    return [mirror_space(s) for s in space_ids]
