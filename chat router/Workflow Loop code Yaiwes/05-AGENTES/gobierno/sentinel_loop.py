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
    task_scope: str = ""
    required_files: list[str] = field(default_factory=list)
    acceptance: str = ""
    objective_checks: list[str] = field(default_factory=list)
    max_attempts: int = 3
    max_research_sources: int = 20
    max_stall_minutes: int = 30

    def to_dict(self) -> dict:
        return {
            "sentinel_id": self.sentinel_id,
            "objective": self.objective,
            "repository": self.repository,
            "report_path": self.report_path,
            "priority_goals": list(self.priority_goals),
            "evidence_required": list(self.evidence_required),
            "research_sources": list(self.research_sources),
            "task_scope": self.task_scope,
            "required_files": list(self.required_files),
            "acceptance": self.acceptance,
            "objective_checks": list(self.objective_checks),
            "max_attempts": self.max_attempts,
            "max_research_sources": self.max_research_sources,
            "max_stall_minutes": self.max_stall_minutes,
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
            task_scope=str(payload.get("task_scope", "")),
            required_files=list(payload.get("required_files", [])),
            acceptance=str(payload.get("acceptance", "")),
            objective_checks=list(payload.get("objective_checks", [])),
            max_attempts=int(payload.get("max_attempts", 3)),
            max_research_sources=int(payload.get("max_research_sources", 20)),
            max_stall_minutes=int(payload.get("max_stall_minutes", 30)),
        )


class SentinelDAG:
    @staticmethod
    def build(spec: SentinelSpec) -> dict:
        nodes = [
            "OBSERVE", "SHERIFF", "VALIDATE", "CONTEXT", "RESEARCH",
            "ORDER", "EXECUTOR", "SUPERVISE", "VERIFY", "GUARDIAN",
            "REVERIFY", "PASS", "BLOCK",
        ]
        edges = [
            ("OBSERVE", "SHERIFF"), ("SHERIFF", "VALIDATE"),
            ("VALIDATE", "CONTEXT"), ("CONTEXT", "RESEARCH"),
            ("RESEARCH", "ORDER"), ("ORDER", "EXECUTOR"),
            ("EXECUTOR", "SUPERVISE"), ("SUPERVISE", "VERIFY"),
            ("VERIFY", "GUARDIAN"), ("GUARDIAN", "PASS"),
            ("GUARDIAN", "REVERIFY"), ("REVERIFY", "OBSERVE"),
            ("SHERIFF", "BLOCK"), ("GUARDIAN", "BLOCK"),
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
        if spec.max_stall_minutes < 1:
            return False, "max_stall_minutes inválido"
        if spec.task_scope:
            scope = PurePosixPath(spec.task_scope)
            if scope.is_absolute() or ".." in scope.parts:
                return False, "task_scope inválido"
            if not spec.required_files:
                return False, "required_files vacío"
            if not spec.acceptance:
                return False, "acceptance vacío"
            for name in spec.required_files:
                rp = PurePosixPath(name)
                if rp.is_absolute() or ".." in rp.parts:
                    return False, f"required_file inválido:{name}"
        p = PurePosixPath(spec.report_path)
        if p.is_absolute() or ".." in p.parts:
            return False, "report_path inválido"
        return True, "PASS"


class SentinelSheriff:
    """El sentinela puede escribir informes/órdenes; nunca código del objetivo."""

    ALLOWED_PREFIXES = (
        "chat router/06-EQUIPO/",
        "chat router/Workflow Loop code Yaiwes/07-SENTINELAS/",
        "chat router/Workflow Loop code Yaiwes/06-ESPEJOS/tareas/",
    )

    def validate_write_paths(self, paths: list[str]) -> tuple[bool, str]:
        for raw in paths:
            path = str(raw).replace("\\", "/")
            if path.startswith("/") or ".." in PurePosixPath(path).parts:
                return False, f"ruta inválida:{raw}"
            if not any(path.startswith(prefix) for prefix in self.ALLOWED_PREFIXES):
                return False, f"sentinela no autorizado a editar:{raw}"
        return True, "PASS"


    def validate_executor_paths(
        self, spec: SentinelSpec, changed_files: list[str]
    ) -> tuple[bool, str]:
        """Sheriff del ejecutor: ningún cambio puede escapar del scope de la tarea."""
        if not spec.task_scope:
            return True, "PASS"
        scope = spec.task_scope.rstrip("/") + "/"
        for raw in changed_files:
            path = str(raw).replace("\\", "/").lstrip("./")
            if path.startswith(".github/") or path.startswith("router inteligente universal/"):
                return False, f"forbidden_path:{path}"
            if not (path == spec.task_scope.rstrip("/") or path.startswith(scope)):
                return False, f"scope_escape:{path}"
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
        if evidence.get("objective_drift"):
            issues.append("objective_drift")
        if evidence.get("scope_escape"):
            issues.append("scope_escape")
        if evidence.get("stale_report"):
            issues.append("stale_report")

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
        if evidence.get("scope_escape"):
            return {"action": "INTERVENE", "reason": "scope_escape"}
        if evidence.get("objective_drift"):
            return {"action": "INTERVENE", "reason": "objective_drift"}
        if evidence.get("workflow_false_green"):
            return {"action": "INTERVENE", "reason": "false_green_workflow"}
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


class SentinelSupervisor:
    """Vigila al ejecutor mientras trabaja y detecta desviación antes del cierre."""

    def inspect(self, spec: SentinelSpec, runtime: dict) -> dict:
        if not runtime.get("executor_active"):
            return {"action": "IDLE", "reason": "executor_inactive"}

        if runtime.get("forbidden_path"):
            return {"action": "BLOCK", "reason": "forbidden_path"}
        if runtime.get("scope_escape"):
            return {"action": "INTERVENE", "reason": "scope_escape"}

        age = int(runtime.get("active_step_age_minutes", 0) or 0)
        if age >= spec.max_stall_minutes:
            return {"action": "RESEARCH", "reason": "executor_stalled"}

        if runtime.get("pytest_exit") == 5:
            return {"action": "INTERVENE", "reason": "no_tests_collected"}
        if (
            runtime.get("agent_exit") == 0
            and runtime.get("acceptance_exit") not in (None, 0)
        ):
            return {"action": "INTERVENE", "reason": "false_green_agent"}

        return {
            "action": "WATCH",
            "reason": runtime.get("active_step") or "executor_active",
        }


class SentinelContextBuilder:
    """Genera contexto ejecutable desde contrato + evidencia + investigación."""

    @staticmethod
    def build(
        spec: SentinelSpec,
        task_id: str,
        evidence: dict,
        research: dict | None = None,
    ) -> str:
        research = research or {}
        findings = research.get("findings") or research.get("fuentes") or []
        analysis = research.get("analysis") or research.get("analisis") or ""
        lines = [
            f"# {task_id} — CONTEXTO DEL SENTINELA",
            "",
            f"OBJETIVO: {spec.objective}",
            f"ALCANCE: {spec.task_scope or '-'}",
            "ARCHIVOS OBLIGATORIOS:",
        ]
        lines += [f"- {name}" for name in spec.required_files]
        lines += [
            "",
            f"ACEPTACIÓN: {spec.acceptance or '-'}",
            "",
            "EVIDENCIA ACTUAL:",
            f"- causa: {evidence.get('causa') or evidence.get('failure_class') or '-'}",
            f"- faltan: {evidence.get('faltan', [])}",
            f"- pytest/acceptance exit: {evidence.get('pytest_exit', '-')}",
            f"- scope_escape: {bool(evidence.get('scope_escape'))}",
            f"- objective_drift: {bool(evidence.get('objective_drift'))}",
            "",
            "REGLAS:",
            "- No regenerar archivos que ya pasen.",
            "- No escribir fuera del ALCANCE.",
            "- Si falta conocimiento, investigar antes de inventar.",
            "- Corregir solo la causa demostrada y volver a ejecutar aceptación.",
        ]
        if spec.objective_checks:
            lines += ["", "CHEQUEOS INDEPENDIENTES DEL OBJETIVO:"]
            lines += [f"- {check}" for check in spec.objective_checks]
        if findings:
            lines += ["", "FUENTES ENCONTRADAS:"]
            for item in findings[:20]:
                if isinstance(item, dict):
                    lines.append(
                        f"- {item.get('source','fuente')}: "
                        f"{item.get('title','')} {item.get('url','')}".strip()
                    )
                else:
                    lines.append(f"- {item}")
        if analysis:
            lines += ["", "ANÁLISIS DEL INVESTIGADOR:", str(analysis)]
        return "\n".join(lines).strip() + "\n"


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
            "objective": spec.objective,
            "task_scope": spec.task_scope,
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
        if guard["action"] == "INTERVENE":
            return {"state": "REVISE", "reason": guard["reason"]}

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
