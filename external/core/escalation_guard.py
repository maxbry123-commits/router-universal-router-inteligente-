"""escalation_guard.py — AND-gate anti-escalada
NOTA: Este archivo es DISTINTO a router_llm_hf/escalation_guard.py (ya existe en rama,
commit cd095fc). No hay colision: rutas diferentes.
"""
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


class EscalationGuard:
    REQUIRED_CONDITIONS = [
        "deferencia_explicita",
        "sin_tool_calls_activas",
        "feedback_previo_existe",
        "max_attempts_no_alcanzado",
    ]

    def __init__(self) -> None:
        self._conditions_met: Dict[str, bool] = {c: False for c in self.REQUIRED_CONDITIONS}
        self._last_blocked: bool = False

    def set_condition(self, condition: str, value: bool) -> None:
        if condition in self._conditions_met:
            self._conditions_met[condition] = value

    def can_escalate(self) -> bool:
        all_met = all(self._conditions_met.values())
        self._last_blocked = not all_met
        if not all_met:
            logger.warning(
                "Escalation blocked: faltan %s",
                [c for c, v in self._conditions_met.items() if not v],
            )
        return all_met

    def reset(self) -> None:
        self._conditions_met = {c: False for c in self.REQUIRED_CONDITIONS}
        self._last_blocked = False

    def status(self) -> Dict[str, Any]:
        return {
            "conditions_met": self._conditions_met.copy(),
            "can_escalate": all(self._conditions_met.values()),
            "last_blocked": self._last_blocked,
        }
