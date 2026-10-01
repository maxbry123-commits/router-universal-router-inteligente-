"""Skill Runtime Contract — yaiwes.skill-runtime/v1 (T11-I).

Código copiado de la especificación del Director
(chat router/01-PLAN/T-11/T-11-I-01-SKILL-RUNTIME-SCHEMA-CODE.md).
Markdown = interfaz humana; schema + código = autoridad ejecutable.
Skill sin adapter+schema+tests queda DOCUMENTATION_ONLY.
"""
from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

SKILL_STATUSES = ("DOCUMENTATION_ONLY", "SCHEMA_READY", "ADAPTER_READY",
                  "TESTED", "EXECUTABLE", "BLOCKED", "PENDING_VERIFICATION")


@dataclass(frozen=True)
class SkillInvocation:
    skill_id: str
    project_id: str
    task_id: str
    input: dict[str, Any]
    allowed_tools: tuple[str, ...]
    write_scope: tuple[str, ...]
    requested_at: float = field(default_factory=time.time)


@dataclass
class SkillResult:
    skill_id: str
    status: str
    output: dict[str, Any]
    evidence: list[dict[str, Any]]
    errors: list[str]


class SkillContractError(RuntimeError):
    pass


class SkillRegistry:
    def __init__(self):
        self.contracts = {}
        self.adapters = {}

    def register(self, contract, adapter=None):
        skill_id = contract["id"]
        if skill_id in self.contracts:
            raise SkillContractError("duplicate skill")
        if contract["status"] == "EXECUTABLE" and adapter is None:
            raise SkillContractError("EXECUTABLE requires adapter")
        self.contracts[skill_id] = contract
        if adapter:
            self.adapters[skill_id] = adapter

    def invoke(self, invocation, sheriff_check):
        contract = self.contracts.get(invocation.skill_id)
        if not contract:
            raise SkillContractError("skill not registered")
        if contract["status"] != "EXECUTABLE":
            raise SkillContractError("skill not executable")
        if not sheriff_check(contract, invocation):
            raise SkillContractError("blocked by sheriff")
        result = self.adapters[invocation.skill_id](invocation)
        if not result.evidence:
            raise SkillContractError("missing evidence")
        return result


def sheriff_skill_check(contract, invocation):
    allowed = set(contract.get("tools_allowed", []))
    requested = set(invocation.allowed_tools)
    if not requested.issubset(allowed):
        return False

    prefixes = tuple(contract.get("permissions", {}).get("write_paths", []))
    for path in invocation.write_scope:
        if prefixes and not any(path.startswith(p) for p in prefixes):
            return False
    return True


def compile_skill(spec):
    required = [
        "id", "name", "classification",
        "inputs", "outputs", "permissions", "status",
    ]
    missing = [x for x in required if x not in spec]
    if missing:
        raise SkillContractError(f"missing fields: {missing}")

    if spec["status"] == "EXECUTABLE" and not spec.get("adapter", {}).get("entrypoint"):
        raise SkillContractError("adapter.entrypoint required")
    if spec["status"] not in SKILL_STATUSES:
        raise SkillContractError(f"unknown status: {spec['status']}")
    return spec


def register_from_spec(registry: SkillRegistry, spec: dict,
                       adapters: dict[str, Callable] | None = None) -> dict:
    """compile → register. Sin adapter queda DOCUMENTATION_ONLY si el spec lo dice."""
    contract = compile_skill(spec)
    adapter = (adapters or {}).get(contract["id"])
    if contract["status"] == "EXECUTABLE" and adapter is None:
        raise SkillContractError("EXECUTABLE sin adapter real")
    registry.register(contract, adapter)
    return contract
