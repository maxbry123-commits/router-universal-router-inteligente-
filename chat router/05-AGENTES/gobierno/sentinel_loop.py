"""LOOP común de los sentinelas YAIWES.

DSL -> DAG -> Schema -> Sheriff -> Observe -> Verify -> Guardian -> Classify
-> Research -> Order -> Reverify -> PASS/BLOCK.

Una sola implementación; las réplicas chat/fabrica/plan4 solo aportan configuración.
La LLM puede investigar/redactar, pero nunca declarar PASS.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import PurePosixPath


STATES = {"PASS", "ACTIVE", "REVISE", "RESEARCH", "BLOCK"}


@dataclass
class SentinelSpec:
    sentinel_id: str
    objective: str
    repository: str
    report_path: str
    priority_goals: list[str]
    evidence_required: list[str]
    research_sources: list[str] = field(default_factory=list)
    max_attempts: int = 3
    max_research_sources: int = 20

    def to_dict(self) -> dict:
        return {
            "sentinel_id": self.sentinel_id,
            "objective": self.objective,
            "repository": self.repository,
            "report_path": self.report_path,
            "priority_goals": list(self.priority_goals),
            "evidence_required": list(self.evidence_required),
            "research_sources": list(self.research_sources),
            "max_attempts": self.max_attempts,
            "max_research_sources": self.max_research_sources,
        }


class SentinelDSL:
    REQUIRED = (
        "sentinel_id", "objective", "repository", "report_path",
        "priority_goals", "evidence_required",
    )

    @classmethod
    def parse(cls, payload: dict) -> SentinelSpec:
        missing = [k for k in cls.REQUIRED if not payload.get(k)]
        if missing:
            raise ValueError(f"DSL sentinela incompleto: {missing}")
        return SentinelSpec(
            sentinel_id=str(payload["sentinel_id"]),
            objective=str(payload["objective"]),
            repository=str(payload["repository"]),
            report_path=str(payload["report_path"]),
            priority_goals=list(payload["priority_goals"]),
            evidence_required=list(payload["evidence_required"]),
            research_sources=list(payload.get("research_sources", [])),
            max_attempts=int(payload.get("max_attempts", 3)),
            max_research_sources=int(payload.get("max_research_sources", 20)),
        )


class SentinelDAG:
    @staticmethod
    def build(spec: SentinelSpec) -> dict:
        nodes = [
            "OBSERVE", "VERIFY", "GUARDIAN", "CLASSIFY", "RESEARCH",
            "ORDER", "EXECUTOR", "REVERIFY", "PASS", "BLOCK",
        ]
        edges = [
            ("OBSERVE", "VERIFY"), ("VERIFY", "GUARDIAN"),
            ("GUARDIAN", "CLASSIFY"), ("CLASSIFY", "PASS"),
            ("CLASSIFY", "RESEARCH"), ("RESEARCH", "ORDER"),
            ("ORDER", "EXECUTOR"), ("EXECUTOR", "REVERIFY"),
            ("REVERIFY", "OBSERVE"), ("GUARDIAN", "BLOCK"),
            ("CLASSIFY", "BLOCK"),
        ]
        return {"sentinel_id": spec.sentinel_id, "nodes": nodes, "edges": edges}


class SentinelSchemaValidator:
    def validate(self, spec: SentinelSpec) -> tuple[bool, str]:
        if not spec.priority_goals:
            return False, "sin objetivos prioritarios"
        if not spec.evidence_required:
            return False, "sin contrato de evidencia"
        if spec.max_attempts < 1:
            return False, "max_attempts inválido"
        if not (1 <= spec.max_research_sources <= 20):
            return False, "max_research_sources fuera de rango"
        p = PurePosixPath(spec.report_path)
        if p.is_absolute() or ".." in p.parts:
            return False, "report_path inválido"
        return True, "PASS"


class SentinelSheriff:
    """El sentinela puede escribir informes/órdenes; nunca código del objetivo."""

    ALLOWED_PREFIXES = (
        "chat router/06-EQUIPO/",
        "chat router/07-SENTINELAS/",
        "chat router/06-ESPEJOS/tareas/",
    )

    def validate_write_paths(self, paths: list[str]) -> tuple[bool, str]:
        for raw in paths:
            path = str(raw).replace("\\", "/")
            if path.startswith("/") or ".." in PurePosixPath(path).parts:
                return False, f"ruta inválida:{raw}"
            if not any(path.startswith(prefix) for prefix in self.ALLOWED_PREFIXES):
                return False, f"sentinela no autorizado a editar:{raw}"
        return True, "PASS"


class SentinelVerifier:
    """Verifica objetivo por evidencia; nunca usa el texto de la LLM para PASS."""

    def verify(self, spec: SentinelSpec, evidence: dict) -> tuple[bool, list[str]]:
        issues: list[str] = []
        if not evidence.get("observed_sha"):
            issues.append("missing_observed_sha")
        if evidence.get("observed_sha") != evidence.get("current_sha"):
            issues.append("stale_observation")
        if evidence.get("executor_active"):
            issues.append("executor_active")
        if evidence.get("workflow_false_green"):
            issues.append("workflow_false_green")

        objective = evidence.get("objective_evidence", {})
        for key in spec.evidence_required:
            value = objective.get(key)
            if value in (None, False, "", [], {}):
                issues.append(f"missing_evidence:{key}")
        return not issues, issues


class SentinelGuardian:
    """Controla frescura, loops inútiles, repetición y desvíos."""

    def inspect(self, spec: SentinelSpec, state: dict, evidence: dict) -> dict:
        if evidence.get("unauthorized_change"):
            return {"action": "BLOCK", "reason": "unauthorized_change"}
        if evidence.get("observed_sha") != evidence.get("current_sha"):
            return {"action": "REOBSERVE", "reason": "stale_observation"}
        if state.get("attempt", 0) >= spec.max_attempts:
            return {"action": "RESEARCH", "reason": "attempt_limit"}
        if (
            state.get("last_failure")
            and state.get("last_failure") == evidence.get("failure_class")
            and state.get("same_failure_count", 0) >= 2
        ):
            return {"action": "RESEARCH", "reason": "repeated_failure"}
        return {"action": "CONTINUE", "reason": "PASS"}


class SentinelResearchPlanner:
    """Crea el paquete de investigación; máximo 20 fuentes, con prioridad."""

    @staticmethod
    def build(
        spec: SentinelSpec,
        failure: str,
        error_literal: str = "",
        context: dict | None = None,
    ) -> dict:
        context = context or {}
        sources = list(dict.fromkeys(spec.research_sources))[:spec.max_research_sources]
        component = context.get("component", spec.objective)
        version = context.get("version", "")
        queries = [
            f"{component} {version} {failure}".strip(),
            f"{component} {error_literal}".strip(),
            f"{failure} GitHub issue fix",
            f"{failure} Stack Overflow",
            f"{failure} developer community",
        ]
        return {
            "sentinel_id": spec.sentinel_id,
            "failure": failure,
            "error_literal": error_literal[-1000:],
            "queries": queries,
            "sources": sources,
            "min_independent_sources": 3,
            "max_sources": spec.max_research_sources,
            "required_output": [
                "root_cause", "evidence", "do_not_regenerate",
                "repair_steps", "acceptance_check",
            ],
        }


class SentinelOrchestrator:
    """Decide la siguiente acción del sentinela a partir de evidencia real."""

    def __init__(self) -> None:
        self.validator = SentinelSchemaValidator()
        self.verifier = SentinelVerifier()
        self.guardian = SentinelGuardian()

    def next_action(
        self,
        spec: SentinelSpec,
        state: dict,
        evidence: dict,
    ) -> dict:
        ok, reason = self.validator.validate(spec)
        if not ok:
            return {"state": "BLOCK", "reason": reason}

        guard = self.guardian.inspect(spec, state, evidence)
        if guard["action"] == "BLOCK":
            return {"state": "BLOCK", "reason": guard["reason"]}
        if guard["action"] == "REOBSERVE":
            return {"state": "ACTIVE", "reason": guard["reason"]}

        passed, issues = self.verifier.verify(spec, evidence)
        if passed:
            return {"state": "PASS", "reason": "objective_evidence_complete"}

        if "executor_active" in issues:
            return {"state": "ACTIVE", "reason": "executor_active"}

        failure = evidence.get("failure_class") or (issues[0] if issues else "unknown")
        if guard["action"] == "RESEARCH":
            return {"state": "RESEARCH", "reason": failure}

        return {"state": "REVISE", "reason": failure}


def update_state(previous: dict, result: dict, evidence: dict) -> dict:
    """Memoria persistente para que cada ciclo continúe el anterior."""
    failure = evidence.get("failure_class", "")
    same = previous.get("same_failure_count", 0)
    if failure and failure == previous.get("last_failure"):
        same += 1
    elif failure:
        same = 1
    else:
        same = 0

    state = dict(previous)
    state.update({
        "status": result["state"],
        "last_sha": evidence.get("current_sha", ""),
        "last_failure": failure,
        "same_failure_count": same,
        "evidence": evidence,
        "next_action": result.get("reason", ""),
    })
    if result["state"] in {"REVISE", "RESEARCH"}:
        state["attempt"] = previous.get("attempt", 0) + 1
    return state
