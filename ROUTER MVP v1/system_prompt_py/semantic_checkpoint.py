import json
import hashlib
from pathlib import Path
from core_recovery import atomic_write_json
from resume_validator import ResumeValidator

class SemanticCheckpoint:
    def __init__(self, plan_id: str, environment: dict):
        self.plan_id = plan_id
        self.environment = environment
        self.dir = Path(".checkpoints")
        self.dir.mkdir(exist_ok=True)
        self.state_file = self.dir / f"{plan_id}_semantic.json"
        self.environment_hash = self._hash_environment(environment)
        self.state = self._load()

    def _hash_environment(self, env: dict) -> str:
        env_str = json.dumps(env, sort_keys=True)
        return hashlib.sha256(env_str.encode()).hexdigest()

    def _load(self) -> dict:
        if self.state_file.exists():
            with open(self.state_file, "r", encoding="utf-8") as f:
                state = json.load(f)
            if state.get("plan_sha256") != self.plan_id:
                raise ValueError("Plan SHA256 cambio. Abortando reanudacion.")
            if state.get("environment_hash") != self.environment_hash:
                raise ValueError("Entorno cambio. Abortando reanudacion.")
            ResumeValidator.validate_checkpoint(state)
            return state
        return {
            "plan_sha256": self.plan_id,
            "environment_hash": self.environment_hash,
            "environment": self.environment,
            "completed_blocks": [],
            "current": None,
            "consumed_interrupts": [],
            "locked_objective": None
        }

    def save_block(self, block_id: str, code: str):
        code_hash = hashlib.sha256(code.encode()).hexdigest()
        self.state["completed_blocks"] = [b for b in self.state["completed_blocks"] if b["id"] != block_id]
        self.state["completed_blocks"].append({"id": block_id, "hash": code_hash})
        self.state["current"] = block_id
        atomic_write_json(str(self.state_file), self.state)
        return code_hash

    def get_next(self, all_blocks: list) -> dict | None:
        done = {b["id"] for b in self.state["completed_blocks"]}
        return next((b for b in all_blocks if b["id"] not in done), None)

    def lock_objective(self, objective: str):
        if self.state.get("locked_objective") is None:
            self.state["locked_objective"] = objective
            atomic_write_json(str(self.state_file), self.state)

    def verify_objective(self, current_objective: str):
        locked = self.state.get("locked_objective")
        if locked and locked != current_objective:
            raise ValueError(f"GOAL_LOCK_VIOLADO: '{current_objective}' != '{locked}'")

    def _ensure(self):
        self.state.setdefault("partials", {})
        self.state.setdefault("parts", {})

    def save_partial(self, block_id: str, text: str):
        self._ensure()
        self.state["partials"][block_id] = {"text": text, "hash": hashlib.sha256(text.encode("utf-8")).hexdigest()}
        atomic_write_json(str(self.state_file), self.state)

    def get_partial(self, block_id: str) -> str:
        self._ensure()
        entry = self.state["partials"].get(block_id)
        return entry["text"] if entry else ""

    def clear_partial(self, block_id: str):
        self._ensure()
        if self.state["partials"].pop(block_id, None) is not None:
            atomic_write_json(str(self.state_file), self.state)

    def save_parts(self, block_id: str, names: list):
        self._ensure()
        self.state["parts"][block_id] = list(names)
        atomic_write_json(str(self.state_file), self.state)

    def _save(self):
        atomic_write_json(str(self.state_file), self.state)
