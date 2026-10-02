"""O4-04..O4-18 — Adapters del Orquestador / Command Center.

Una capa, no 8 frameworks: cada componente externo se registra como
capacidad con guardarraíles declarados. Autoridades: HERMES crea el goal
global; SHERIFF valida pre-ejecución; ORACLE (judge+verifier) cierra.
Ningún adapter transfiere autoridad ni muta el MissionContract.

Fail-closed: un adapter sin su comando/runtime configurado no ejecuta.
"""

from __future__ import annotations

import os
import shlex
import subprocess
from dataclasses import dataclass, field
from typing import Any, Callable

from .contracts import LayerResult, NodeContract, Status
from .governance import judge, verifier
from .ledger import append_event, verify_ledger
from .orchestrator_contracts import (
    EvidenceRecord, MissionContract, OracleStatus, OracleVerdict,
    ResultEnvelope, TaskContract)


class AdapterError(RuntimeError):
    pass


# ---------------------------------------------------------------------
# O4-03 capability map: qué aporta cada componente y qué tiene PROHIBIDO.
# ---------------------------------------------------------------------
COMPONENT_CAPABILITIES: dict[str, dict[str, Any]] = {
    "hermes":      {"provides": "global_goal_authority", "forbidden": (),
                    "command_env": "YAIWES_HERMES_COMMAND"},
    "rowboat":     {"provides": "context_roundtrip", "forbidden": ("mutate_global_goal",),
                    "command_env": "YAIWES_ROWBOAT_COMMAND"},
    "ms_agent_framework": {"provides": "sequential_concurrent_handoff_checkpoint_resume",
                           "forbidden": (), "command_env": "YAIWES_MSAF_COMMAND"},
    "orca":        {"provides": "parallel_workers_worktree_isolation",
                    "forbidden": ("shared_workspace_write",), "command_env": "YAIWES_ORCA_COMMAND"},
    "omniroute":   {"provides": "provider_account_failover_routing_receipt",
                    "forbidden": (), "command_env": "YAIWES_OMNIROUTE_COMMAND"},
    "deepseek_harness": {"provides": "plugin_execution",
                         "forbidden": ("side_effect_without_sheriff",), "command_env": "YAIWES_DEEPSEEK_HARNESS_COMMAND"},
    "munder_difflin": {"provides": "local_role_coordination",
                       "forbidden": ("global_replan",), "command_env": "YAIWES_MUNDER_COMMAND"},
    "dagu_dbos":   {"provides": "durability_crash_resume",
                   "forbidden": ("duplicate_side_effect",), "command_env": "YAIWES_DAGU_DBOS_COMMAND"},
    "mcp":         {"provides": "capability_context_bus",
                    "forbidden": ("authority_transfer", "uncontrolled_context_write"),
                    "command_env": "YAIWES_MCP_COMMAND"},
}


# ---------------------------------------------------------------------
# O4-04: Hermes brain — solo Hermes crea/replanifica el goal global.
# ---------------------------------------------------------------------
def create_global_goal(mission_id: str, goal: str, *, caller: str) -> MissionContract:
    if caller != "hermes":
        raise PermissionError(f"GLOBAL_GOAL_CREATE_DENIED:{caller}")
    return MissionContract.build(mission_id, goal)


def assert_no_global_goal_mutation(component: str, mission: MissionContract,
                                   attempted_goal: str) -> None:
    """O4-07/O4-12: un adapter NUNCA puede mutar el goal global."""
    if attempted_goal != mission.global_goal:
        raise AdapterError(f"GLOBAL_GOAL_MUTATION_DENIED:{component}")


# ---------------------------------------------------------------------
# O4-05: Sheriff pre-exec — mutation_without_sheriff -> denied.
# ---------------------------------------------------------------------
def sheriff_precheck(node: NodeContract, action: str) -> list[str]:
    from .governance import sheriff
    errors = sheriff.check(node)
    if node.mutation and "sheriff" not in node.authorization:
        errors.append("mutation_without_sheriff_authorization")
    if action in node.forbidden_actions:
        errors.append(f"forbidden_action:{action}")
    return errors


# ---------------------------------------------------------------------
# ComponentAdapter: fail-closed, declara su capacidad, delega en comando.
# ---------------------------------------------------------------------
@dataclass
class ComponentAdapter:
    component: str
    invoke_fn: Callable[[dict[str, Any]], dict[str, Any]] | None = field(default=None)

    def capability(self) -> dict[str, Any]:
        try:
            return COMPONENT_CAPABILITIES[self.component]
        except KeyError:
            raise AdapterError(f"UNKNOWN_COMPONENT:{self.component}")

    def invoke(self, task: TaskContract, mission: MissionContract,
               timeout_s: int = 120) -> dict[str, Any]:
        cap = self.capability()
        # Guardarraíl de autoridad: payload nunca intenta mutar el goal.
        attempted = task.payload.get("global_goal", mission.global_goal)
        assert_no_global_goal_mutation(self.component, mission, attempted)

        if self.invoke_fn is not None:
            return self.invoke_fn(task.payload)

        env_name = cap["command_env"]
        raw = os.environ.get(env_name or "")
        if not raw:
            raise AdapterError(f"RUNTIME_UNAVAILABLE:{self.component}:{env_name}")
        proc = subprocess.run([*shlex.split(raw)],
                              input=str(task.payload), text=True,
                              capture_output=True, timeout=timeout_s, check=False)
        if proc.returncode != 0:
            raise AdapterError(f"{self.component}_COMMAND_FAILED:{proc.returncode}")
        return {"stdout": proc.stdout, "component": self.component}


# ---------------------------------------------------------------------
# O4-15: Evidence Ledger — append hash-chain; tamper/missing detectado.
# ---------------------------------------------------------------------
class EvidenceLedger:
    def __init__(self) -> None:
        self.rows: list[dict[str, Any]] = []

    def record(self, task: TaskContract, envelope: ResultEnvelope) -> dict[str, Any]:
        if envelope.status == Status.PASS and not envelope.evidence:
            raise AdapterError("PASS_WITHOUT_EVIDENCE_REFUSED")
        row = append_event(self.rows, {
            "task_id": envelope.task_id, "mission_id": envelope.mission_id,
            "node_id": envelope.node_id, "status": envelope.status.value,
            "evidence": [r.sha256_hash for r in envelope.evidence],
            "receipt": envelope.receipt_sha256})
        return row

    def verify(self) -> bool:
        return verify_ledger(self.rows)


# ---------------------------------------------------------------------
# O4-16: Oracle post-exec — PASS|FAIL|INCOMPLETE|BLOCKED via judge+verifier.
# ---------------------------------------------------------------------
def oracle_verdict(node: NodeContract, result: LayerResult) -> OracleVerdict:
    errors = verifier.check(result) + judge.check(result)
    evidence = tuple(EvidenceRecord(ref=e.ref, kind=e.kind, sha256_hash=e.sha256)
                     for e in result.evidence)
    if result.status == Status.BLOCKED:
        return OracleVerdict(OracleStatus.BLOCKED, tuple(errors), evidence)
    if errors:
        return OracleVerdict(OracleStatus.FAIL, tuple(errors), evidence)
    if result.status == Status.PASS:
        return OracleVerdict(OracleStatus.PASS, (), evidence)
    return OracleVerdict(OracleStatus.INCOMPLETE, tuple(result.gaps), evidence)


# ---------------------------------------------------------------------
# O4-18: Pre-Questions / Input Shark — goal ambiguo pide campos faltantes.
# ---------------------------------------------------------------------
REQUIRED_GOAL_FIELDS = ("mission_id", "global_goal", "allowed_roles")


def input_shark(goal_fields: dict[str, Any]) -> dict[str, Any]:
    """Objetivo ambiguo -> pregunta los campos faltantes, hash normalizado."""
    missing = [f for f in REQUIRED_GOAL_FIELDS if not goal_fields.get(f)]
    return {
        "complete": not missing,
        "missing_fields": missing,
        "normalized_goal_sha": "" if missing else
            __import__("wordflow_loop.contracts", fromlist=["sha256"]).sha256(goal_fields.get("global_goal", "")),
    }
