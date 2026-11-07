# checkpoint_manager.py
import os
import json
import hashlib
from pathlib import Path
from core_recovery import atomic_write_json

def compute_sha256(data: str) -> str:
    return hashlib.sha256(data.encode("utf-8")).hexdigest()

class CheckpointManager:
    def __init__(self, plan_id: str, checkpoint_dir: str = ".checkpoints"):
        self.plan_id = plan_id
        self.dir = Path(checkpoint_dir)
        self.dir.mkdir(exist_ok=True)
        self.state_file = self.dir / f"{plan_id}_state.json"
        self.state = self._load_state()

    def _load_state(self) -> dict:
        if self.state_file.exists():
            with open(self.state_file, "r", encoding="utf-8") as f:
                state = json.load(f)
            # Extraído de motor_cli.py: Validación de plan_sha256
            if state.get("plan_sha256") != self.plan_id:
                raise ValueError("Plan SHA256 no coincide. El plan cambió. Abortando reanudación.")
            return state
        return {"plan_sha256": self.plan_id, "completed_blocks": [], "current_block": None}

    def save_block(self, block_id: str, code: str):
        code_hash = compute_sha256(code)
        block_file = self.dir / f"{block_id}.py"
        with open(block_file, "w", encoding="utf-8") as f:
            f.write(code)
        
        # Evitar duplicados en el estado
        self.state["completed_blocks"] = [b for b in self.state["completed_blocks"] if b["id"] != block_id]
        self.state["completed_blocks"].append({"id": block_id, "hash": code_hash})
        self.state["current_block"] = block_id
        atomic_write_json(str(self.state_file), self.state)
        return code_hash

    def get_next_block(self, all_blocks: list) -> dict | None:
        completed_ids = {b["id"] for b in self.state["completed_blocks"]}
        for block in all_blocks:
            if block["id"] not in completed_ids:
                return block
        return None
