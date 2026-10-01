# T-11-I — CONTRATO UNIVERSAL SKILL → SCHEMA → CODE

## Objetivo

No ejecutar un `SKILL.md` como texto libre.

Flujo obligatorio:

```text
SKILL/DOCUMENTACIÓN
→ PARSER
→ SKILL CONTRACT
→ SCHEMA
→ ADAPTER EJECUTABLE
→ SHERIFF
→ REGISTRY
→ TEST
→ EXECUTABLE
```

## Schema universal

```yaml
schema: yaiwes.skill-runtime/v1
id:
name:
version:
source:
  type: github|documentation|local|unknown
  url:
  verified: false
description:
classification:
  kind: meta_skill|review|memory|planning|methodology|discovery|collection|unknown
  executable_mode: adapter|workflow|tool|documentation_only
inputs:
  required: []
outputs:
  required: []
preconditions: []
capabilities: []
tools_allowed: []
side_effects:
  filesystem: none|read|write
  network: false
  process: false
  git: false
  memory: false
permissions:
  read_paths: []
  write_paths: []
  network_domains: []
  commands: []
forbidden:
  - bypass_sheriff
  - self_pass
  - undeclared_side_effect
  - privilege_escalation
timeouts:
  execution_seconds:
  idle_seconds:
retry:
  enabled: false
  max_attempts: 0
evidence:
  required: true
  types: []
tests:
  contract: []
  integration: []
  negative: []
adapter:
  language: python
  entrypoint:
  callable: run
status: DOCUMENTATION_ONLY|SCHEMA_READY|ADAPTER_READY|EXECUTABLE|BLOCKED|PENDING_VERIFICATION
```

## Runtime Python

```python
from dataclasses import dataclass, field
from typing import Any, Callable
import time

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
```

## Sheriff

```python
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
```

## Compiler

```python
def compile_skill(spec):
    required = [
        "id", "name", "classification",
        "inputs", "outputs", "permissions", "status"
    ]
    missing = [x for x in required if x not in spec]
    if missing:
        raise SkillContractError(f"missing fields: {missing}")

    if spec["status"] == "EXECUTABLE":
        if not spec.get("adapter", {}).get("entrypoint"):
            raise SkillContractError("adapter.entrypoint required")
    return spec
```

## Estados

```text
DOCUMENTATION_ONLY
→ SCHEMA_READY
→ ADAPTER_READY
→ TESTED
→ EXECUTABLE
```

Si falta verificar fuente/capacidad:

```text
PENDING_VERIFICATION
```

Regla final:

```text
Markdown = interfaz humana.
Schema + código = autoridad ejecutable.
```
