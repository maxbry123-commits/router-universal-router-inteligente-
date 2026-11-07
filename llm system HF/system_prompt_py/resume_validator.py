# resume_validator.py
from typing import Dict, Set

REQUIRED_CHECKPOINT_FIELDS = {
    "plan_sha256", "environment_hash", "completed_blocks", "current", "consumed_interrupts"
}

class ResumeValidator:
    @staticmethod
    def validate_checkpoint(state: dict) -> bool:
        missing = REQUIRED_CHECKPOINT_FIELDS - set(state.keys())
        if missing:
            raise ValueError(f"Checkpoint inválido. Faltan campos: {missing}")
        if not isinstance(state.get("completed_blocks"), list):
            raise ValueError("completed_blocks debe ser lista")
        if not isinstance(state.get("consumed_interrupts"), list):
            raise ValueError("consumed_interrupts debe ser lista")
        return True

    @staticmethod
    def consume_interrupt(state: dict, interrupt_id: str) -> bool:
        consumed: Set[str] = set(state.get("consumed_interrupts", []))
        if interrupt_id in consumed:
            return False
        consumed.add(interrupt_id)
        state["consumed_interrupts"] = list(consumed)
        return True
