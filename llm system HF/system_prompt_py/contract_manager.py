# contract_manager.py
import json
import hashlib

class MissionContract:
    """
    Chat A define el contrato. Chat B NO PUEDE MODIFICARLO.
    Extraído del PROMPT_MAESTRO (Sección 4: MISSION CONTRACT + GOAL LOCK).
    """
    def __init__(self, mission_id: str, objective: str, scope: list, acceptance: list):
        self.mission_id = mission_id
        self.objective = objective
        self.scope = scope
        self.acceptance = acceptance
        self._hash = self._compute_hash()

    def _compute_hash(self) -> str:
        data = {
            "mission_id": self.mission_id,
            "objective": self.objective,
            "scope": self.scope,
            "acceptance": self.acceptance
        }
        return hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()

    def verify_goal_lock(self, current_objective: str) -> bool:
        """Verifica que el objetivo no haya sido alterado por Chat B."""
        if current_objective != self.objective:
            raise ValueError(f"GOAL LOCK VIOLADO: El objetivo cambió de '{self.objective}' a '{current_objective}'.")
        return True

    def to_dict(self) -> dict:
        return {
            "mission_id": self.mission_id,
            "objective": self.objective,
            "scope": self.scope,
            "acceptance": self.acceptance,
            "contract_hash": self._hash
        }
