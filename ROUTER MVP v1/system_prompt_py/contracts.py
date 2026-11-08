import hashlib
import json

class MissionContract:
    def __init__(self, objective: str, scope: list, acceptance: list):
        self.objective = objective
        self.scope = scope
        self.acceptance = acceptance
        self.contract_hash = self._compute_hash()

    def _compute_hash(self) -> str:
        data = {"obj": self.objective, "scope": self.scope, "acc": self.acceptance}
        return hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()

    def verify_goal_lock(self, current_objective: str) -> bool:
        if current_objective != self.objective:
            raise ValueError(f"GOAL_LOCK_VIOLADO: {current_objective} != {self.objective}")
        return True
