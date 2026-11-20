"""
escalation_guard.py — AND-gate anti-escalada (Control Plane)
"""
from __future__ import annotations
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
        self._escalation_blocked: bool = False

    def set_condition(self, condition: str, value: bool) -> None:
        if condition in self._conditions_met:
            self._conditions_met[condition] = value

    def can_escalate(self) -> bool:
        all_met = all(self._conditions_met.values())
        if not all_met:
            logger.warning("Escalada bloqueada: faltan %s",
                           [c for c, v in self._conditions_met.items() if not v])
            self._escalation_blocked = True
        return all_met

    def reset(self) -> None:
        self._conditions_met = {c: False for c in self.REQUIRED_CONDITIONS}
        self._escalation_blocked = False

    def status(self) -> Dict[str, Any]:
        return {
            "conditions_met": self._conditions_met.copy(),
            "can_escalate": all(self._conditions_met.values()),
            "last_blocked": self._escalation_blocked,
        }
