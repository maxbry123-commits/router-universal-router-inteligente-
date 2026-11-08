import hashlib
import json

class MissionContract:
    def __init__(self, objective: str, plan_sha256: str, scope: list, acceptance: list):
        self.locked_objective = objective
        self.locked_plan_sha256 = plan_sha256
        self.locked_scope = scope
        self.locked_acceptance = acceptance
        self.contract_hash = self._compute_hash()

    def _compute_hash(self) -> str:
        data = {"obj": self.locked_objective, "plan": self.locked_plan_sha256, "scope": self.locked_scope}
        return hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()

    def verify_goal_lock(self, current_objective: str, current_plan_sha256: str, current_scope: list) -> bool:
        if current_objective != self.locked_objective:
            raise ValueError(f"GOAL_LOCK_VIOLADO (Objetivo): '{current_objective}' != '{self.locked_objective}'")
        if current_plan_sha256 != self.locked_plan_sha256:
            raise ValueError(f"GOAL_LOCK_VIOLADO (Plan): '{current_plan_sha256}' != '{self.locked_plan_sha256}'")
        if set(current_scope) != set(self.locked_scope):
            raise ValueError(f"GOAL_LOCK_VIOLADO (Scope): {current_scope} != {self.locked_scope}")
        return True
