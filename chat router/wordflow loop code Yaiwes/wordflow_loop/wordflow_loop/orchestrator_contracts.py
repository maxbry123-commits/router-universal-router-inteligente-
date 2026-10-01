"""O4-06 — Contratos normalizados del Orquestador / Command Center.

MissionContract (goal global, solo Hermes lo crea/replanifica),
TaskContract (por nodo/worker), ResultEnvelope (salida uniforme),
EvidenceRecord (evidencia hash), OracleVerdict (PASS/FAIL/INCOMPLETE/
BLOCKED, nunca sin evidencia). Capa fina sobre contracts.py + ledger.py.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from .contracts import Evidence, Status, canonical, sha256


class MissionAuthority(str, Enum):
    HERMES = "HERMES"           # único que crea/replanifica el goal global
    SHERIFF = "SHERIFF"         # autoridad pre-ejecución
    ORACLE = "ORACLE"           # autoridad post-ejecución


@dataclass(frozen=True)
class MissionContract:
    mission_id: str
    global_goal: str
    created_by: MissionAuthority
    goal_sha256: str = ""
    allowed_roles: tuple[str, ...] = ()
    constraints: tuple[str, ...] = ()

    @classmethod
    def build(cls, mission_id: str, global_goal: str,
              created_by: MissionAuthority = MissionAuthority.HERMES,
              allowed_roles: tuple[str, ...] = (),
              constraints: tuple[str, ...] = ()) -> "MissionContract":
        if created_by != MissionAuthority.HERMES:
            raise PermissionError("ONLY_HERMES_CREATES_GLOBAL_GOAL")
        return cls(mission_id=mission_id, global_goal=global_goal,
                   created_by=created_by,
                   goal_sha256=sha256(global_goal),
                   allowed_roles=allowed_roles, constraints=constraints)


@dataclass(frozen=True)
class TaskContract:
    task_id: str
    mission_id: str
    node_id: str
    required_role: str
    payload: dict[str, Any]
    lease_seconds: int = 60
    allowed_paths: tuple[str, ...] = ()
    authorization: tuple[str, ...] = ()
    task_sha256: str = ""

    def sha(self) -> str:
        return sha256(canonical({
            "task_id": self.task_id, "mission_id": self.mission_id,
            "node_id": self.node_id, "required_role": self.required_role,
            "payload": self.payload}))


@dataclass(frozen=True)
class EvidenceRecord:
    ref: str
    kind: str
    sha256_hash: str
    captured_at_ms: int = 0

    def to_evidence(self) -> Evidence:
        return Evidence(kind=self.kind, ref=self.ref, sha256=self.sha256_hash)


class OracleStatus(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    INCOMPLETE = "INCOMPLETE"
    BLOCKED = "BLOCKED"


@dataclass(frozen=True)
class OracleVerdict:
    status: OracleStatus
    reasons: tuple[str, ...] = ()
    evidence: tuple[EvidenceRecord, ...] = ()

    def valid(self) -> bool:
        """PASS jamás sin evidencia real (judge/verifier)."""
        if self.status == OracleStatus.PASS:
            return bool(self.evidence)
        return True


@dataclass(frozen=True)
class ResultEnvelope:
    task_id: str
    mission_id: str
    node_id: str
    status: Status
    output: dict[str, Any] = field(default_factory=dict)
    evidence: tuple[EvidenceRecord, ...] = ()
    gaps: tuple[str, ...] = ()
    actions: tuple[str, ...] = ()
    receipt_sha256: str = ""

    def sealed(self) -> "ResultEnvelope":
        raw = {"task_id": self.task_id, "mission_id": self.mission_id,
               "node_id": self.node_id, "status": self.status.value,
               "output": self.output,
               "evidence": [r.sha256_hash for r in self.evidence],
               "gaps": list(self.gaps)}
        return ResultEnvelope(**{**self.__dict__, "receipt_sha256": sha256(canonical(raw))})
