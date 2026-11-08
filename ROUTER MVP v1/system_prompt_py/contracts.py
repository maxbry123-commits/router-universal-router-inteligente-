import hashlib
import json

class MissionContract:
    def __init__(self, objective: str, scope: list, acceptance: list):
        self.locked_objective = objective
        self.locked_scope = scope
        self.locked_acceptance = acceptance
        self.contract_hash = self._compute_hash()

    def _compute_hash(self) -> str:
        data = {"obj": self.locked_objective, "scope": self.locked_scope, "acc": self.locked_acceptance}
        return hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()

    def verify_goal_lock(self, current_objective: str, current_scope: list) -> bool:
        if current_objective != self.locked_objective:
            raise ValueError(f"GOAL_LOCK_VIOLADO (Objetivo): '{current_objective}' != '{self.locked_objective}'")
        if set(current_scope) != set(self.locked_scope):
            raise ValueError(f"GOAL_LOCK_VIOLADO (Scope): {current_scope} != {self.locked_scope}")
        return True
