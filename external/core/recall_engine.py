"""recall_engine.py — Re-invocacion con feedback, max 8 intentos
NOTA: DISTINTO a router_llm_hf/recall_engine.py (commit 0ef04d83 ya en rama).
"""
from __future__ import annotations
import asyncio
import logging
from typing import Any, Dict, Optional, Callable, Awaitable, List

logger = logging.getLogger(__name__)


class RecallEngine:
    MAX_ATTEMPTS = 8
    BACKOFF_BASE_S = 1.0
    BACKOFF_MAX_S = 30.0
    HISTORY_LIMIT = 1000

    def __init__(self) -> None:
        self._history: Dict[str, List[Dict[str, Any]]] = {}

    async def execute_with_recall(
        self,
        task_id: str,
        func: Callable[[Optional[Dict[str, Any]]], Awaitable[Any]],
        error_feedback: Optional[Callable[[Exception], Dict[str, Any]]] = None,
    ) -> Any:
        self._history.setdefault(task_id, [])
        last_error: Optional[Dict[str, Any]] = None
        for attempt in range(1, self.MAX_ATTEMPTS + 1):
            try:
                result = await func(last_error)
                self._history[task_id].append({"attempt": attempt, "status": "success"})
                self._trim_history(task_id)
                return result
            except Exception as e:
                logger.warning("Task %s intento %d/%d fallo: %s",
                               task_id, attempt, self.MAX_ATTEMPTS, e)
                last_error = (error_feedback(e) if error_feedback
                              else {"error": str(e), "type": type(e).__name__})
                self._history[task_id].append(
                    {"attempt": attempt, "status": "failed", "error": last_error}
                )
                self._trim_history(task_id)
                if attempt != self.MAX_ATTEMPTS:
                    backoff = min(self.BACKOFF_BASE_S * (2 ** (attempt - 1)),
                                  self.BACKOFF_MAX_S)
                    await asyncio.sleep(backoff)
        raise RuntimeError(f"Task {task_id} fallo tras {self.MAX_ATTEMPTS} intentos")

    def _trim_history(self, task_id: str) -> None:
        h = self._history.get(task_id)
        if h and len(h) > self.HISTORY_LIMIT:
            self._history[task_id] = h[-self.HISTORY_LIMIT:]

    def get_history(self, task_id: str) -> List[Dict[str, Any]]:
        return self._history.get(task_id, [])

    def clear_history(self, task_id: str) -> None:
        self._history.pop(task_id, None)
