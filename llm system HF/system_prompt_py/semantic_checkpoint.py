# semantic_checkpoint.py
import json
import hashlib
import os
from pathlib import Path
from core_recovery import atomic_write_json

class SemanticCheckpoint:
    """
    Checkpoint con validación de entorno.
    Si el modelo, proveedor o versión del prompt cambian, el checkpoint se invalida.
    """
    def __init__(self, plan_id: str, environment: dict):
        """
        environment = {"model": "llama3-70b", "provider": "groq", "prompt_version": "v1.2"}
        """
        self.plan_id = plan_id
        self.environment = environment
        self.dir = Path(".checkpoints")
        self.dir.mkdir(exist_ok=True)
        self.state_file = self.dir / f"{plan_id}_semantic.json"
        self.environment_hash = self._hash_environment(environment)
        self.state = self._load()

    def _hash_environment(self, env: dict) -> str:
        """Calcula la huella del entorno para detectar cambios."""
        env_str = json.dumps(env, sort_keys=True)
        return hashlib.sha256(env_str.encode()).hexdigest()

    def _load(self) -> dict:
        if self.state_file.exists():
            with open(self.state_file, "r", encoding="utf-8") as f:
                state = json.load(f)
            
            # Verificar plan
            if state.get("plan_sha256") != self.plan_id:
                raise ValueError("Plan SHA256 cambió. Abortando reanudación.")
            
            # Verificar entorno
            if state.get("environment_hash") != self.environment_hash:
                raise ValueError(
                    f"Entorno cambió. Antes: {state.get('environment')}, "
                    f"Ahora: {self.environment}. Abortando reanudación."
                )
            return state

        return {
            "plan_sha256": self.plan_id,
            "environment_hash": self.environment_hash,
            "environment": self.environment,
            "completed_blocks": [],
            "current": None
        }

    def save_block(self, block_id: str, code: str):
        code_hash = hashlib.sha256(code.encode()).hexdigest()
        self.state["completed_blocks"] = [
            b for b in self.state["completed_blocks"] if b["id"] != block_id
        ]
        self.state["completed_blocks"].append({"id": block_id, "hash": code_hash})
        self.state["current"] = block_id
        atomic_write_json(str(self.state_file), self.state)
        return code_hash

    def is_valid_for_resume(self) -> bool:
        """Retorna True solo si el entorno y el plan son los mismos."""
        return True  # Si llegamos aquí, ya validó en _load
