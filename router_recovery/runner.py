"""Ejecutor determinista: carga YAML -> valida Pydantic -> orden topologico -> dispatch -> ledger.

Uso (desde la raiz del repo):
    python -m router_recovery.runner --dag router_recovery/dag_schema.yaml --store .checkpoints/
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

import yaml

from .checkpoint_store import CheckpointStore
from .dispatcher import DISPATCH_TABLE
from .pydantic_models import DagNode, DagSpec, LedgerEvent, checksum, topo_order


class Runner:
    def __init__(self, store: CheckpointStore, mission_id: str):
        self.store = store
        self.mission_id = mission_id
        self.state: dict[str, Any] = store.load_state()
        self.state.setdefault("phases", {})

    def start(self, dag: DagSpec) -> None:
        self.state.update(
            mission_id=dag.mission_id,
            dag_sha=checksum(dag.model_dump()),
            node_ids=[n.node_id for n in dag.nodes],
        )
        self.store.save_state(self.state)

    def completed_ids(self) -> set[str]:
        """El ledger es la fuente de verdad. Nodos con node_done NO se re-ejecutan."""
        return {e.node_id for e in self.store.read_ledger() if e.event == "node_done"}

    def run(self, dag: DagSpec) -> dict[str, Any]:
        by_id = {n.node_id: n for n in dag.nodes}
        done = self.completed_ids()
        for node_id in topo_order(dag.nodes):
            if node_id in done:
                continue
            node = by_id[node_id]
            self._event(node, "node_start", {"root_ids": node.root_ids})
            try:
                handler = DISPATCH_TABLE.get(node.handler)
                if handler is None:
                    raise ValueError(f"handler desconocido: {node.handler}")
                result = handler(node)
            except Exception as exc:
                self._event(node, "error", {"type": type(exc).__name__, "msg": str(exc)[:500]}, "invalido")
                raise
            self._event(node, "node_done", {"result": result}, "completa")
        return self.state

    def resume(self, dag: DagSpec) -> dict[str, Any]:
        """Salta node_done; re-ejecuta los node_start sin node_done (nodo en vuelo al caer)."""
        return self.run(dag)

    def _event(self, node: DagNode, event: str, payload: dict, phase: str = "en_curso") -> None:
        self.store.append(LedgerEvent(mission_id=self.mission_id, node_id=node.node_id,
                                      event=event, payload=payload))
        self.state["phases"][node.node_id] = phase
        self.store.save_state(self.state)


def load_dag(path: str | Path) -> DagSpec:
    raw = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    return DagSpec.model_validate(raw)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Runner determinista del router recovery")
    p.add_argument("--dag", default="router_recovery/dag_schema.yaml")
    p.add_argument("--store", default=".checkpoints/")
    args = p.parse_args(argv)
    try:
        dag = load_dag(args.dag)
    except ValueError as exc:  # fail-closed: nada se ejecuta
        print(f"BLOCKER: {exc}", file=sys.stderr)
        return 2
    runner = Runner(CheckpointStore(args.store), dag.mission_id)
    runner.start(dag)
    runner.resume(dag)
    print("COMPLETED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
