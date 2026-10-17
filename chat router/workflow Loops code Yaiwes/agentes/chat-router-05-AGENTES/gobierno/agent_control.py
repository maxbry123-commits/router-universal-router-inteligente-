"""Control determinista del agente ejecutor T01.

DSL -> DAG -> Schema -> Sheriff -> Execute -> Verify -> Guardian -> Judge.
El Investigador prepara investigación; nunca declara PASS.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import PurePosixPath


@dataclass
class AgentTaskSpec:
    task_id: str
    objective: str
    scope: str
    required_files: list[str]
    acceptance_commands: list[str]
    dependencies: list[str] = field(default_factory=list)
    max_attempts: int = 3
    research_max_sources: int = 20

    def to_dict(self) -> dict:
        return {
            "task_id": self.task_id,
            "objective": self.objective,
            "scope": self.scope,
            "required_files": list(self.required_files),
            "acceptance_commands": list(self.acceptance_commands),
            "dependencies": list(self.dependencies),
            "max_attempts": self.max_attempts,
            "research_max_sources": self.research_max_sources,
        }


class AgentDSL:
    REQUIRED = ("task_id", "objective", "scope", "required_files", "acceptance_commands")

    @classmethod
    def parse(cls, payload: dict) -> AgentTaskSpec:
        missing = [k for k in cls.REQUIRED if not payload.get(k)]
        if missing:
            raise ValueError(f"DSL incompleto: {missing}")
        return AgentTaskSpec(
            task_id=str(payload["task_id"]),
            objective=str(payload["objective"]),
            scope=str(payload["scope"]),
            required_files=list(payload["required_files"]),
            acceptance_commands=list(payload["acceptance_commands"]),
            dependencies=list(payload.get("dependencies", [])),
            max_attempts=int(payload.get("max_attempts", 3)),
            research_max_sources=int(payload.get("research_max_sources", 20)),
        )


class AgentDAG:
    @staticmethod
    def build(spec: AgentTaskSpec) -> dict:
        nodes = [
            "SCHEMA", "SHERIFF", "EXECUTE", "VERIFY", "GUARDIAN",
            "JUDGE", "PASS", "REVISE", "RESEARCH", "BLOCK",
        ]
        edges = [
            ("SCHEMA", "SHERIFF"), ("SHERIFF", "EXECUTE"),
            ("EXECUTE", "VERIFY"), ("VERIFY", "GUARDIAN"),
            ("GUARDIAN", "JUDGE"), ("JUDGE", "PASS"),
            ("JUDGE", "REVISE"), ("REVISE", "EXECUTE"),
            ("REVISE", "RESEARCH"), ("RESEARCH", "EXECUTE"),
            ("SHERIFF", "BLOCK"), ("GUARDIAN", "BLOCK"),
        ]
        return {"task_id": spec.task_id, "nodes": nodes, "edges": edges}


class SchemaValidator:
    def validate(self, spec: AgentTaskSpec) -> tuple[bool, str]:
        if not spec.task_id or not spec.objective:
            return False, "id/objetivo vacíos"
        if not spec.required_files:
            return False, "required_files vacío"
        if not spec.acceptance_commands:
            return False, "acceptance_commands vacío"
        if spec.max_attempts < 1:
            return False, "max_attempts inválido"
        if not (1 <= spec.research_max_sources <= 20):
            return False, "research_max_sources fuera de rango"

        scope = PurePosixPath(spec.scope)
        if scope.is_absolute() or ".." in scope.parts:
            return False, "scope inválido"

        for name in spec.required_files:
            p = PurePosixPath(name)
            if p.is_absolute() or ".." in p.parts:
                return False, f"archivo requerido inválido: {name}"
        return True, "PASS"


class EvidenceVerifier:
    """PASS solo con archivos completos y pytest realmente ejecutado."""

    def verify(self, spec: AgentTaskSpec, evidence: dict) -> tuple[bool, list[str]]:
        issues: list[str] = []
        observed = set(evidence.get("files", []))
        missing = [f for f in spec.required_files if f not in observed]
        if missing:
            issues.append(f"missing_files:{','.join(missing)}")

        test_exit = evidence.get("test_exit_code")
        test_count = int(evidence.get("tests_collected", 0) or 0)
        if test_exit != 0:
            issues.append(f"pytest_exit:{test_exit}")
        if test_count <= 0:
            issues.append("no_tests_collected")
        if evidence.get("unauthorized_change"):
            issues.append("unauthorized_change")
        return not issues, issues


class Guardian:
    """Bloquea escapes de scope, falsos verdes y sync con árbol sucio."""

    def inspect(self, spec: AgentTaskSpec, evidence: dict) -> dict:
        if evidence.get("unauthorized_change"):
            return {"action": "BLOCK", "reason": "unauthorized_change"}

        scope = spec.scope.rstrip("/") + "/"
        for path in evidence.get("changed_files", []):
            clean = str(path).replace("\\", "/").lstrip("./")
            if not (clean == spec.scope.rstrip("/") or clean.startswith(scope)):
                return {"action": "BLOCK", "reason": f"path_escape:{path}"}

        if evidence.get("sync_attempted") and evidence.get("dirty_worktree"):
            return {"action": "REVISE", "reason": "dirty_worktree_before_sync"}

        if evidence.get("workflow_success") and evidence.get("test_exit_code") != 0:
            return {"action": "REVISE", "reason": "false_green_workflow"}

        return {"action": "CONTINUE", "reason": "PASS"}


class Investigator:
    @staticmethod
    def prepare(spec: AgentTaskSpec, failure: str, context: dict | None = None) -> dict:
        context = context or {}
        queries = [
            f"{spec.task_id} {failure}",
            f"{context.get('tool', '')} {context.get('version', '')} {failure}".strip(),
            f"GitHub issue {failure}",
            f"Stack Overflow {failure}",
        ]
        return {
            "task_id": spec.task_id,
            "failure": failure,
            "max_sources": min(spec.research_max_sources, 20),
            "queries": [q for q in queries if q],
            "required_output": [
                "root_cause", "evidence", "candidate_fix", "verification"
            ],
        }


class AgentOrchestrator:
    KNOWN_RECOVERABLE = {
        "pytest_failure", "missing_files",
        "dirty_worktree_before_sync", "false_green_workflow",
    }

    def __init__(self, validator: SchemaValidator | None = None) -> None:
        self.validator = validator or SchemaValidator()
        self.verifier = EvidenceVerifier()
        self.guardian = Guardian()

    def next_action(
        self,
        spec: AgentTaskSpec,
        evidence: dict,
        *,
        attempt: int = 1,
        failure_class: str = "",
    ) -> dict:
        ok, reason = self.validator.validate(spec)
        if not ok:
            return {"state": "BLOCK", "reason": reason}

        guard = self.guardian.inspect(spec, evidence)
        if guard["action"] == "BLOCK":
            return {"state": "BLOCK", "reason": guard["reason"]}
        if guard["action"] == "REVISE":
            return {"state": "REVISE", "reason": guard["reason"]}

        passed, issues = self.verifier.verify(spec, evidence)
        if passed:
            return {"state": "PASS", "reason": "evidence_complete"}

        if attempt >= spec.max_attempts:
            return {
                "state": "RESEARCH",
                "reason": failure_class or (issues[0] if issues else "unknown_failure"),
            }

        if failure_class and failure_class not in self.KNOWN_RECOVERABLE:
            return {"state": "RESEARCH", "reason": failure_class}

        return {"state": "REVISE", "reason": ",".join(issues)}
