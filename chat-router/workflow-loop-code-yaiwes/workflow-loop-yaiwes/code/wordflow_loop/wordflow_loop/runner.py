"""LayerRunner — orquesta la cadena de gobernanza determinista por nodo.

Ciclo por nodo: validator (deps) -> sheriff (pre) -> executor -> sentinel
(runtime) -> supervisor (scope) -> guardian (ledger/mutación) -> verifier +
judge (PASS solo con evidencia real y sin gaps) -> append_event al ledger.
Ningún resultado se marca PASS sin pasar la cadena completa.
"""

from __future__ import annotations

import time
from typing import Any, Callable, Mapping, Sequence

from .contracts import LayerResult, NodeContract, Status
from .governance import guardian, judge, sentinel, sheriff, supervisor, validator, verifier
from .ledger import append_event

Executor = Callable[[NodeContract, dict[str, Any]], LayerResult]


def _collect_errors(*groups: list[str]) -> list[str]:
    return [e for g in groups for e in g]


class LayerRunner:
    """Ejecutor determinista de nodos bajo la cadena de gobernanza."""

    def __init__(self, executor: Executor) -> None:
        self.executor = executor
        self.ledger: list[dict[str, Any]] = []
        self.results: dict[str, LayerResult] = {}

    def _toposort(self, nodes: Sequence[NodeContract]) -> list[NodeContract]:
        remaining = {n.node_id: n for n in nodes}
        ordered: list[NodeContract] = []
        done: set[str] = set()
        while remaining:
            progressed = False
            for node_id in sorted(remaining):
                node = remaining[node_id]
                if all(d in done or d not in remaining for d in node.depends_on):
                    ordered.append(node)
                    done.add(node_id)
                    del remaining[node_id]
                    progressed = True
                    break
            if not progressed:
                raise ValueError("CYCLE_OR_UNKNOWN_DEPENDENCY:" + ",".join(sorted(remaining)))
        return ordered

    def run_node(self, node: NodeContract, ctx: dict[str, Any]) -> LayerResult:
        completed = {nid for nid, r in self.results.items() if r.status == Status.PASS}
        pre = _collect_errors(
            validator.check(node, completed),
            sheriff.check(node),
        )
        if pre:
            result = LayerResult(node_id=node.node_id, layer=node.layer,
                                 status=Status.BLOCKED, gaps=pre)
            self.results[node.node_id] = result
            append_event(self.ledger, {"node_id": node.node_id, "status": "BLOCKED", "errors": pre})
            return result

        started = time.monotonic()
        result = self.executor(node, ctx)
        post = _collect_errors(
            sentinel.check_runtime(node, result, started),
            supervisor.check(node, result),
            guardian.check(node, result, self.ledger),
            verifier.check(result),
            judge.check(result),
        )
        if post:
            result.status = Status.FAIL
            result.gaps.extend(post)
        self.results[node.node_id] = result
        append_event(self.ledger, {
            "node_id": node.node_id,
            "status": result.status.value,
            "evidence": [e.ref for e in result.evidence],
            "gaps": result.gaps,
        })
        return result

    def run(self, nodes: Sequence[NodeContract], ctx: dict[str, Any] | None = None) -> dict[str, LayerResult]:
        ctx = ctx or {}
        for node in self._toposort(nodes):
            self.run_node(node, ctx)
        return self.results
