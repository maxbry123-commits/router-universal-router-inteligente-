"""Contratos únicos del equipo YAIWES (docs 22 y 23 del Director).

Job/Result: contrato de la cadena de ingeniería (doc 22).
Task/State: contrato de la jerarquía de gobierno (doc 23).
Ningún agente manda mensajes libres: todo pasa por estos objetos.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class State(str, Enum):
    """Máquina de estados del workflow (doc 23)."""
    INPUT = "INPUT"
    PLANNING = "PLANNING"
    DEBATE = "DEBATE"
    SHERIFF = "SHERIFF"
    EXECUTION = "EXECUTION"
    REVIEW = "REVIEW"
    JUDGMENT = "JUDGMENT"
    PASS = "PASS"
    REVISE = "REVISE"
    BLOCK = "BLOCK"


def _require(data: dict, keys: list[str], cls: str) -> None:
    faltan = [k for k in keys if k not in data or data[k] is None]
    if faltan:
        raise ValueError(f"{cls}: faltan campos obligatorios: {faltan}")


@dataclass
class Job:
    """Contrato único de trabajo de ingeniería (doc 22)."""
    job_id: str
    objective: str
    scope: list[str] = field(default_factory=list)
    acceptance: list[str] = field(default_factory=list)
    state: str = State.INPUT.value
    attempt: int = 0
    evidence: list = field(default_factory=list)
    issues: list = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.job_id:
            raise ValueError("Job: job_id obligatorio")
        if not self.objective:
            raise ValueError("Job: objective obligatorio")

    def to_dict(self) -> dict:
        return {
            "job_id": self.job_id,
            "objective": self.objective,
            "scope": list(self.scope),
            "acceptance": list(self.acceptance),
            "state": self.state,
            "attempt": self.attempt,
            "evidence": list(self.evidence),
            "issues": list(self.issues),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Job":
        _require(data, ["job_id", "objective"], "Job")
        return cls(
            job_id=data["job_id"],
            objective=data["objective"],
            scope=list(data.get("scope", [])),
            acceptance=list(data.get("acceptance", [])),
            state=data.get("state", State.INPUT.value),
            attempt=int(data.get("attempt", 0)),
            evidence=list(data.get("evidence", [])),
            issues=list(data.get("issues", [])),
        )


@dataclass
class Result:
    """Respuesta estándar de cualquier agente (doc 22)."""
    job_id: str
    agent: str
    status: str
    changed_files: list[str] = field(default_factory=list)
    tests: list = field(default_factory=list)
    issues: list = field(default_factory=list)
    evidence: list = field(default_factory=list)
    next_action: str = ""

    def __post_init__(self) -> None:
        if not self.job_id:
            raise ValueError("Result: job_id obligatorio")
        if not self.agent:
            raise ValueError("Result: agent obligatorio")
        if self.status not in ("PASS", "REVISE", "BLOCK", "FAIL"):
            raise ValueError(f"Result: status inválido: {self.status}")

    def to_dict(self) -> dict:
        return {
            "job_id": self.job_id,
            "agent": self.agent,
            "status": self.status,
            "changed_files": list(self.changed_files),
            "tests": list(self.tests),
            "issues": list(self.issues),
            "evidence": list(self.evidence),
            "next_action": self.next_action,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Result":
        _require(data, ["job_id", "agent", "status"], "Result")
        return cls(
            job_id=data["job_id"],
            agent=data["agent"],
            status=data["status"],
            changed_files=list(data.get("changed_files", [])),
            tests=list(data.get("tests", [])),
            issues=list(data.get("issues", [])),
            evidence=list(data.get("evidence", [])),
            next_action=data.get("next_action", ""),
        )


@dataclass
class Task:
    """Contrato de una tarea del plan (doc 23)."""
    id: str
    objective: str
    role: str
    dependencies: list[str] = field(default_factory=list)
    allowed_paths: list[str] = field(default_factory=list)
    acceptance: list[str] = field(default_factory=list)
    evidence: dict = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.id:
            raise ValueError("Task: id obligatorio")
        if not self.objective:
            raise ValueError("Task: objective obligatorio")
        if not self.role:
            raise ValueError("Task: role obligatorio")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "objective": self.objective,
            "role": self.role,
            "dependencies": list(self.dependencies),
            "allowed_paths": list(self.allowed_paths),
            "acceptance": list(self.acceptance),
            "evidence": dict(self.evidence),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Task":
        _require(data, ["id", "objective", "role"], "Task")
        return cls(
            id=data["id"],
            objective=data["objective"],
            role=data["role"],
            dependencies=list(data.get("dependencies", [])),
            allowed_paths=list(data.get("allowed_paths", [])),
            acceptance=list(data.get("acceptance", [])),
            evidence=dict(data.get("evidence", {})),
        )
