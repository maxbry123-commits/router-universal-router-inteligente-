"""space_power_manager.py — Enciende, apaga y reinicia los grupos de Spaces."""
import os
import time
import logging
from huggingface_hub import HfApi, HfHubHTTPError

logger = logging.getLogger(__name__)
api = HfApi(token=os.getenv("HF_TOKEN"))

try:
    # Inventario canonico (Op1): fuente unica de verdad de los 6 Spaces.
    from external.core.space_inventory import (
        GROUP_1_COMPUTE,
        GROUP_2_LLM,
        SPACE_COUNT,
        all_spaces,
        group_of,
    )
except ImportError:  # pragma: no cover - arranca igual sin el paquete "external"
    GROUP_1_COMPUTE = ["space-grupo-1-router-mvp-1", "space-grupo-1-router-mvp-1-v2", "space-grupo-1-router-mvp-1-v7"]
    GROUP_2_LLM = ["space-grupo-2-router-llm-hf-1", "space-grupo-2-router-llm-hf-2", "space-grupo-2-router-llm-hf-3"]
    SPACE_COUNT = 6

    def all_spaces():
        return tuple(GROUP_1_COMPUTE) + tuple(GROUP_2_LLM)

    def group_of(space):
        if space in GROUP_1_COMPUTE:
            return "compute"
        if space in GROUP_2_LLM:
            return "llm"
        return None

class SpacePowerManager:
    @staticmethod
    def set_power(group: str, on: bool) -> list:
        """Enciende o apaga un grupo de Spaces."""
        spaces = GROUP_1_COMPUTE if group == "compute" else GROUP_2_LLM
        results = []
        for space in spaces:
            repo_id = f"COMAND-CENTER-1/{space}"
            action = "wake" if on else "pause"
            try:
                if on:
                    api.restart_space(repo_id, repo_type="space", factory_reboot=False)
                else:
                    api.pause_space(repo_id, repo_type="space")
                logger.info(f"[{action.upper()}] {space} -> OK")
                results.append({"space": space, "action": action, "status": "ok"})
            except HfHubHTTPError as e:
                logger.error(f"Fallo al cambiar energía de {space}: {e}")
                results.append({"space": space, "action": action, "status": "error", "detail": str(e)})
        return results

    @staticmethod
    def get_status(group: str) -> dict:
        spaces = GROUP_1_COMPUTE if group == "compute" else GROUP_2_LLM
        status = {}
        for space in spaces:
            try:
                info = api.get_space_info(f"COMAND-CENTER-1/{space}", repo_type="space")
                status[space] = getattr(info, "stage", "UNKNOWN")
            except Exception:
                status[space] = "UNKNOWN"
        return status
