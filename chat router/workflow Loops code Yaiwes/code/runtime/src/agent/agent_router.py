"""
Agent Router Module - PECP-MAXBRY-100x (Nodo T-012)
DEPRECATED (N-2.5): la autoridad única de resolución de agentes es
AgentFleetAdapter + agent_fleet_registry.json (exact id -> slot -> role,
FAIL_CLOSED si no hay match real). Este módulo queda como adaptador
delegado; nunca selecciona registry[0] arbitrario.
"""

from typing import Dict, Any, List, Optional
import json
import warnings

from wordflow_loop.agent_fleet.agent_fleet_adapter import (
    AgentBindingError,
    AgentFleetAdapter,
)


class AgentRouter:
    """DEPRECATED: delega en AgentFleetAdapter. Sin match real -> FAIL_CLOSED."""

    def __init__(
        self,
        registry: Optional[List[Dict[str, Any]]] = None,
        adapter: Optional[AgentFleetAdapter] = None,
    ) -> None:
        warnings.warn(
            "AgentRouter está DEPRECATED (N-2.5); usa AgentFleetAdapter "
            "con agent_fleet_registry.json",
            DeprecationWarning,
            stacklevel=2,
        )
        self._adapter = adapter or AgentFleetAdapter()
        if registry is not None:
            self._registry = registry
        else:
            self._registry = self._adapter.list_agents()

    def select_agent(self, task_type: str, required_skills: List[str]) -> Dict[str, Any]:
        """Selección determinista por roles/skills; FAIL_CLOSED sin match real."""
        requested = set(required_skills) | {task_type}
        best_agent: Optional[Dict[str, Any]] = None
        max_matches: int = 0

        for agent in self._registry:
            caps = set(agent.get("capabilities", ())) | set(agent.get("roles", ()))
            matches = len(requested & caps)
            if matches > max_matches:
                max_matches = matches
                best_agent = agent
            elif matches == max_matches and matches > 0 and best_agent is not None:
                if agent.get("slot", 99) < best_agent.get("slot", 99):
                    best_agent = agent

        if best_agent is None or max_matches <= 0:
            return {
                "selected_agent_id": None,
                "matched_skills": 0,
                "status": "FAIL_CLOSED",
                "error": "NO_REAL_AGENT_MATCH",
            }

        agent_id = best_agent.get("agent_id") or best_agent.get("id")
        try:
            binding = self._adapter.resolve(agent_id=agent_id)
        except AgentBindingError:
            return {
                "selected_agent_id": None,
                "matched_skills": max_matches,
                "status": "FAIL_CLOSED",
                "error": f"AGENT_NOT_BOUND:{agent_id}",
            }

        return {
            "selected_agent_id": agent_id,
            "matched_skills": max_matches,
            "status": "ROUTED",
            "binding": binding,
        }


if __name__ == "__main__":
    print("=== TEST NODO T-012: AGENT ROUTER (deprecated, FAIL_CLOSED) ===")
    router = AgentRouter()
    print(json.dumps(router.select_agent("writer", ["executor"]), indent=2))
    print(json.dumps(router.select_agent("coding", ["nonexistent_skill_xyz"]), indent=2))
