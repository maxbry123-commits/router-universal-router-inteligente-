"""Tipos y límites del módulo. No almacena memoria ni define scheduler."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Protocol
import hashlib, json, re

ID = re.compile(r'^[A-Za-z0-9_-]{1,64}$')

def stable_hash(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                                     separators=(',', ':'), default=str).encode()).hexdigest()

class NCTError(ValueError):
    pass

@dataclass
class WorkUnit:
    id: str
    goal: str
    block: str = 'executor'
    depends_on: list[str] = field(default_factory=list)
    priority: int = 5
    allowed_ops: list[str] = field(default_factory=list)
    acceptance: list[dict] = field(default_factory=list)
    scope: list[str] = field(default_factory=list)
    max_retries: int = 2
    coda: dict = field(default_factory=dict)
    def validate(self) -> None:
        if not ID.fullmatch(self.id): raise NCTError('task ID inválido')
        if not self.goal.strip(): raise NCTError('objetivo vacío')
        if not (1 <= self.priority <= 10): raise NCTError('prioridad fuera de rango')
        if self.max_retries > 3 or self.max_retries < 0: raise NCTError('reintentos fuera de rango')
        if len(self.goal) > 8000: raise NCTError('objetivo excesivo')
        if len(set(self.depends_on)) != len(self.depends_on) or self.id in self.depends_on:
            raise NCTError('dependencias inválidas')
        if not all(isinstance(c, dict) for c in self.acceptance): raise NCTError('aceptación inválida')
        if not isinstance(self.coda,dict):raise NCTError('CODA debe ser objeto')
        if set(self.coda)-{'continue_when','close_when','on_error','handoff'}:
            raise NCTError('CODA contiene instrucciones no reconocidas')
        if self.coda.get('close_when','acceptance_verified')!='acceptance_verified':
            raise NCTError('CODA no puede saltarse la verificación')
        if self.coda.get('on_error','repair_or_block') not in ('repair_or_block','block'):
            raise NCTError('CODA on_error inválido')

@dataclass
class Receipt:
    id: str
    task_id: str
    status: str
    evidence: dict = field(default_factory=dict)
    phase: int = 4
    source: str = 'external'
    def asdict(self) -> dict:
        return {'id':self.id, 'task_id':self.task_id, 'status':self.status,
                'evidence':self.evidence, 'phase':self.phase, 'source':self.source}

class ModelBlockPort(Protocol):
    async def invoke(self, block: str, payload: dict) -> dict: ...

class ExistingQueuePort(Protocol):
    async def submit_and_wait(self, task: WorkUnit, perform: Any) -> dict: ...

class ExistingMemoryPort(Protocol):
    async def load(self, task_id: str) -> dict | None: ...
    async def checkpoint(self, task_id: str, value: dict) -> None: ...

class ExistingToolPort(Protocol):
    async def execute(self, validated_ops: dict, task_id: str) -> dict: ...

class CheckerPort(Protocol):
    async def check(self, task: WorkUnit, receipts: list[dict]) -> dict: ...
