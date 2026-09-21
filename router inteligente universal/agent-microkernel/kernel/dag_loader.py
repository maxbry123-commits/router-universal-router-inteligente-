"""Loads and validates workflow.dag.yaml (schema yaiwes.micro-agent/v1). FAIL_CLOSED: unknown fields or cycles are errors."""
from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

SCHEMA = "yaiwes.micro-agent/v1"
ROUTES = {"nvidia", "groq", "cerebras"}
FALLBACKS = {"deepseek_flash", "minimax_m3"}
ACTIONS = {"code", "plan", "docs", "summarize"}


class DagError(ValueError):
    pass


def load(path: str | Path) -> dict[str, Any]:
    dag = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    errs = validate(dag)
    if errs:
        raise DagError("; ".join(errs))
    return dag


def validate(dag: Any) -> list[str]:
    errs: list[str] = []
    if not isinstance(dag, dict) or dag.get("schema") != SCHEMA:
        return [f"schema debe ser {SCHEMA}"]
    ex = dag.get("execution") or {}
    if ex.get("mode") != "fail_closed":
        errs.append("execution.mode debe ser fail_closed")
    agents = dag.get("agents")
    if not isinstance(agents, dict) or not agents:
        return errs + ["agents vacío"]
    for name, a in agents.items():
        for r in a.get("route", []):
            if r not in ROUTES:
                errs.append(f"{name}: ruta desconocida {r}")
        for f in a.get("fallback", []):
            if f not in FALLBACKS:
                errs.append(f"{name}: respaldo desconocido {f}")
        if a.get("action") not in ACTIONS:
            errs.append(f"{name}: action inválida {a.get('action')}")
        if not str(a.get("task", "")).strip():
            errs.append(f"{name}: task vacío")
        for d in a.get("depends_on", []):
            if d not in agents:
                errs.append(f"{name}: depends_on desconocido {d}")
    if not errs:
        try:
            order(dag)
        except DagError as exc:
            errs.append(str(exc))
    return errs


def order(dag: dict[str, Any]) -> list[list[str]]:
    """Topological levels: agents in the same level run in parallel."""
    agents = dag["agents"]
    remaining = {n: set(a.get("depends_on", [])) for n, a in agents.items()}
    levels: list[list[str]] = []
    while remaining:
        ready = sorted(n for n, deps in remaining.items() if not deps)
        if not ready:
            raise DagError("el DAG tiene un ciclo")
        levels.append(ready)
        for n in ready:
            del remaining[n]
        for deps in remaining.values():
            deps.difference_update(ready)
    return levels
