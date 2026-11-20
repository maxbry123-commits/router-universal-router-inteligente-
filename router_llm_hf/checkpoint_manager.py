"""checkpoint_manager.py — Persistencia ERR (Externalize-Recognize-Rehydrate).
- Escritura atómica (tmp + os.replace).
- Validación de input_sha256 (detecta cambios de plan).
- Fingerprint de progreso (progress_sha256).
"""
import os
import json
import hashlib
import logging
from pathlib import Path
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class CheckpointManager:
    def __init__(self, state_dir: str = None):
        self.state_dir = Path(state_dir or os.getenv("CHECKPOINT_DIR", "state/checkpoints"))
        self.state_dir.mkdir(parents=True, exist_ok=True)

    def _sha256(self, data: str) -> str:
        return hashlib.sha256(data.encode("utf-8")).hexdigest()

    def save(self, task_id: str, state: dict, input_sha256: str) -> str:
        """Guarda el estado de forma atómica. Retorna la ruta del archivo."""
        state = dict(state)  # Copia para no mutar el original
        state["input_sha256"] = input_sha256
        state["updated_at"] = datetime.now(timezone.utc).isoformat()
        state["progress_sha256"] = self._sha256(
            json.dumps(state, sort_keys=True, ensure_ascii=False)
        )
        path = self.state_dir / f"{task_id}.json"
        tmp = path.with_suffix(".tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2, ensure_ascii=False)
        os.replace(tmp, path)
        logger.info(f"[checkpoint] saved {task_id} -> {path}")
        return str(path)

    def resume(self, task_id: str, input_sha256: str) -> dict:
        """Retorna el estado previo si input_sha256 coincide. Si no, None."""
        path = self.state_dir / f"{task_id}.json"
        if not path.exists():
            return None
        try:
            with open(path, "r", encoding="utf-8") as f:
                state = json.load(f)
            if state.get("input_sha256") != input_sha256:
                logger.warning(f"[checkpoint] input cambió para {task_id}, no reanudar")
                return None
            return state
        except Exception as e:
            logger.error(f"[checkpoint] error leyendo {path}: {e}")
            return None

    def list_checkpoints(self) -> list:
        """Lista los task_ids que tienen checkpoint."""
        if not self.state_dir.exists():
            return []
        return [p.stem for p in self.state_dir.glob("*.json")]

    def delete(self, task_id: str) -> bool:
        """Elimina el checkpoint de una tarea."""
        path = self.state_dir / f"{task_id}.json"
        if path.exists():
            path.unlink()
            return True
        return False

    def prune(self, max_age_days: int = 7) -> int:
        import time
        cutoff = time.time() - max_age_days * 86400
        n = 0
        for p in self.state_dir.glob("*.json"):
            try:
                if p.stat().st_mtime < cutoff:
                    p.unlink(); n += 1
            except Exception: pass
        return n
