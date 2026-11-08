import json
import hashlib
from pathlib import Path
from core_recovery import atomic_write_json

CHECKPOINT_DIR = ".checkpoints"

def compute_sha256(data: str) -> str:
    return hashlib.sha256(data.encode("utf-8")).hexdigest()

class CheckpointManager:
    def __init__(self, plan_id: str):
        self.plan_id = plan_id
        self.dir = Path(CHECKPOINT_DIR)
        self.dir.mkdir(exist_ok=True)
        self.state_file = self.dir / f"{plan_id}_state.json"
        self.state = self._load()

    def _load(self) -> dict:
        if self.state_file.exists():
            with open(self.state_file, "r", encoding="utf-8") as f:
                state = json.load(f)
            if state.get("plan_sha256") != self.plan_id:
                raise ValueError("Plan SHA256 no coincide. Reanudacion abortada.")
            return state
        return {"plan_sha256": self.plan_id, "completed_blocks": [], "current": None}

    def save_block(self, block_id: str, code: str):
        code_hash = compute_sha256(code)
        with open(self.dir / f"{block_id}.py", "w", encoding="utf-8") as f:
            f.write(code)
        self.state["completed_blocks"] = [b for b in self.state["completed_blocks"] if b["id"] != block_id]
        self.state["completed_blocks"].append({"id": block_id, "hash": code_hash})
        self.state["current"] = block_id
        atomic_write_json(str(self.state_file), self.state)

    def get_next(self, all_blocks: list) -> dict | None:
        done = {b["id"] for b in self.state["completed_blocks"]}
        return next((b for b in all_blocks if b["id"] not in done), None)
