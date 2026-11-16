"""space_power_manager.py — Enciende, apaga y reinicia los grupos de Spaces."""
import os
import time
import logging
from huggingface_hub import HfApi, HfHubHTTPError

logger = logging.getLogger(__name__)
api = HfApi(token=os.getenv("HF_TOKEN"))

GROUP_1_COMPUTE = ["local-llm-router", "local-llm-router-v2", "local-llm-router-v7"]
GROUP_2_LLM = ["swe-code-s1", "swe-code-s2", "swe-code-s3"]

class SpacePowerManager:
    @staticmethod
    def set_power(group: str, on: bool) -> list:
        """Enciende o apaga un grupo de Spaces."""
        spaces = GROUP_1_COMPUTE if group == "compute" else GROUP_2_LLM
        results = []
        for space in spaces:
            repo_id = f"COMAND-CENTER-1/{space}"
            try:
                if on:
                    api.restart_space(repo_id, repo_type="space", factory_reboot=False)
                    action = "wake"
                else:
                    api.pause_space(repo_id, repo_type="space")
                    action = "pause"
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
