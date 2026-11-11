"""
trigger_wake.py — Despertar Spaces SLEEPING/PAUSED (Salida 3/3)
Ubicacion: control huggueface/trigger_wake.py
Rol: Objetivo 3.3. restart_space si stage in (SLEEPING, PAUSED). Espera RUNNING.
"""
import os
import time
import logging
from huggingface_hub import HfApi

logger = logging.getLogger(__name__)
api = HfApi(token=os.getenv("HF_TOKEN"))


def _stage_of(info) -> str:
    stage = getattr(info, "stage", None)
    if stage is None and isinstance(info, dict):
        stage = info.get("stage")
    return str(stage) if stage else "UNKNOWN"


def wake_if_needed(space_id: str, max_wait_s: int = 30) -> dict:
    try:
        info = api.get_space_info(space_id, repo_type="space")
        stage = _stage_of(info)
        if stage in ("SLEEPING", "PAUSED"):
            api.restart_space(space_id, repo_type="space", factory_reboot=False)
            deadline = time.time() + max_wait_s
            while time.time() < deadline:
                info = api.get_space_info(space_id, repo_type="space")
                stage = _stage_of(info)
                if stage == "RUNNING":
                    return {"status": "woken", "space": space_id, "stage": stage}
                time.sleep(2)
            return {"status": "timeout", "space": space_id, "stage": stage}
        return {"status": "already_up", "space": space_id, "stage": stage}
    except Exception as e:
        logger.warning("Wake fallo %s: %s", space_id, e)
        return {"status": "failed", "space": space_id, "error": str(e)}


def wake_all(space_ids: list) -> list:
    return [wake_if_needed(s) for s in space_ids]
