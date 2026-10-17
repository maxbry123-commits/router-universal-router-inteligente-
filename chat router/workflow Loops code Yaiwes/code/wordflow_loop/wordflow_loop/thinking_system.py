"""ThinkingSystem — slot de razonamiento del orquestador, via mirothinker.

Resuelve el agente `mirothinker` a través de AgentFleetAdapter (registry
canónico). Produce razones/refutaciones con evidencia e incertidumbre;
NUNCA autoriza ejecución, rutas, state transitions ni deploy (contrato de
memoria del agente). FAIL_CLOSED si el comando no está configurado.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .agent_fleet.agent_fleet_adapter import AgentBindingError, AgentFleetAdapter

THINKING_AGENT_ID = "mirothinker"


@dataclass(frozen=True)
class ThinkingResult:
    agent_id: str
    goal: str
    reasons: list[str] = field(default_factory=list)
    evidence: list[dict] = field(default_factory=list)
    uncertainty: list[str] = field(default_factory=list)
    status: str = "REASONED"


class ThinkingSystem:
    """Puerto de razonamiento del orquestador; delega en mirothinker."""

    def __init__(self, adapter: AgentFleetAdapter | None = None) -> None:
        self._adapter = adapter or AgentFleetAdapter()

    def reason(self, goal: str, options: list[dict] | None = None,
               evidence_state: dict | None = None, timeout_s: int = 120) -> ThinkingResult:
        """Pide a mirothinker razones/refutaciones. Sin autoridad de ejecución."""
        try:
            self._adapter.resolve(agent_id=THINKING_AGENT_ID)
        except AgentBindingError as exc:
            raise RuntimeError(f"THINKING_AGENT_NOT_BOUND:{exc}") from exc

        payload = self._adapter.build_invocation_payload(
            THINKING_AGENT_ID,
            {
                "mode": "reasoning",
                "goal": goal,
                "options": options or [],
                "evidence_state": evidence_state or {},
                "constraints": [
                    "produce razones y refutaciones con evidencia",
                    "señala incertidumbre; no autorices ejecución ni deploy",
                ],
            },
        )
        response = self._adapter.invoke(THINKING_AGENT_ID, payload, timeout_s=timeout_s)

        return ThinkingResult(
            agent_id=THINKING_AGENT_ID,
            goal=goal,
            reasons=list(response.get("reasons", ())),
            evidence=list(response.get("evidence", ())),
            uncertainty=list(response.get("uncertainty", ())),
            status=response.get("status", "REASONED"),
        )
