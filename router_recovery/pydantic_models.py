"""Validacion fail-closed del DAG (ciclos, dependencias, duplicados, LOC) y eventos del ledger."""
from __future__ import annotations

import hashlib
import heapq
import json
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator, model_validator


class NodeStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"


def checksum(obj: Any) -> str:
    """sha256 canonico (claves ordenadas) de un objeto JSON-serializable."""
    return hashlib.sha256(json.dumps(obj, sort_keys=True, ensure_ascii=False, default=str).encode()).hexdigest()


class DagNode(BaseModel):
    node_id: str = Field(pattern=r"^N[0-9]+$")
    name: str = Field(min_length=1, max_length=120)
    role: str = Field(pattern=r"^(architect|implementer|tester)$")
    objective: str = Field(min_length=1, max_length=2000)
    root_ids: list[str] = Field(min_length=1)
    files: list[dict[str, str]] = Field(default_factory=list)
    depends_on: list[str] = Field(default_factory=list)
    estimated_loc: int = Field(ge=1, le=2000)
    max_loc_per_block: int = Field(default=200, ge=1, le=200)
    acceptance: list[str] = Field(min_length=1)
    failure_policy: str = Field(default="fail_closed", pattern=r"^(fail_closed|retry|skip)$")
    handler: str = Field(default="dispatch_implementer")

    @field_validator("depends_on")
    @classmethod
    def _no_self_dep(cls, v: list[str], info) -> list[str]:
        if info.data.get("node_id") in v:
            raise ValueError("Un nodo no puede depender de si mismo")
        return v


def topo_order(nodes: list[DagNode]) -> list[str]:
    """Orden topologico determinista (Kahn con cola ordenada). Lanza ValueError si hay ciclo."""
    ids = [n.node_id for n in nodes]
    indeg = {i: 0 for i in ids}
    adj: dict[str, list[str]] = {i: [] for i in ids}
    for n in nodes:
        for dep in n.depends_on:
            adj[dep].append(n.node_id)
            indeg[n.node_id] += 1
    heap = [i for i in ids if indeg[i] == 0]
    heapq.heapify(heap)
    out: list[str] = []
    while heap:
        cur = heapq.heappop(heap)
        out.append(cur)
        for nxt in adj[cur]:
            indeg[nxt] -= 1
            if indeg[nxt] == 0:
                heapq.heappush(heap, nxt)
    if len(out) != len(ids):
        raise ValueError("El DAG contiene un ciclo")
    return out


class DagSpec(BaseModel):
    schema_version: str = "1.0"
    mission_id: str
    objective: str
    nodes: list[DagNode] = Field(min_length=1)

    @model_validator(mode="after")
    def _validate_dag(self) -> "DagSpec":
        ids = [n.node_id for n in self.nodes]
        if len(set(ids)) != len(ids):
            raise ValueError("node_id duplicados en el DAG")
        known = set(ids)
        for n in self.nodes:
            for dep in n.depends_on:
                if dep not in known:
                    raise ValueError(f"{n.node_id} depende de {dep} inexistente")
        topo_order(self.nodes)  # ciclo -> ValueError
        return self


class LedgerEvent(BaseModel):
    ts: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    mission_id: str
    node_id: str
    event: Literal["node_start", "node_done", "error"]
    payload: dict[str, Any] = Field(default_factory=dict)
    checksum: str = ""

    @model_validator(mode="after")
    def _fill_checksum(self) -> "LedgerEvent":
        if not self.checksum:
            self.checksum = checksum(self.model_dump(exclude={"checksum"}))
        return self
