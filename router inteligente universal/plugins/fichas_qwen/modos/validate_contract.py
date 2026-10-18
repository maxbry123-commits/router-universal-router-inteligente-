#!/usr/bin/env python3
"""YAIWES — validador base independiente para contratos loop_contract 1.0/1.1.

Este archivo NO pretende recuperar el `validate_contract.py` original del Director.
Implementa la interfaz exacta que importa `validate_contract_v11.py`:
load, schema_errors, dag_errors, router_errors y loop_errors.
Fail-closed: error/módulo faltante -> veredicto FAIL, nunca PASS sintético.

Uso: python validate_contract.py loop_contract.example.json
     python validate_contract_v11.py loop_contract.example.v1_1.json
"""
from __future__ import annotations

import json
import sys
from collections import deque
from pathlib import Path
from typing import Any


def load(file: str | Path) -> dict[str, Any]:
    with Path(file).open("r", encoding="utf-8") as fh:
        data = json.load(fh)
    if not isinstance(data, dict):
        raise ValueError("contrato: la raiz debe ser objeto JSON")
    return data


def schema_errors(doc: dict[str, Any], schema: dict[str, Any]) -> list[str]:
    try:
        import jsonschema
    except ImportError:
        return ["jsonschema no instalado: falta dependencia real; FAIL_CLOSED"]
    try:
        jsonschema.Draft202012Validator.check_schema(schema)
        validator = jsonschema.Draft202012Validator(schema)
        errors = sorted(validator.iter_errors(doc), key=lambda e: (list(map(str, e.absolute_path)), e.message))
        return ["schema /" + "/".join(map(str, e.absolute_path)) + ": " + e.message for e in errors]
    except Exception as exc:
        return [f"schema fallo al validar: {type(exc).__name__}: {exc}"]


def dag_errors(doc: dict[str, Any]) -> list[str]:
    errs: list[str] = []
    dag = doc.get("dag")
    if not isinstance(dag, dict) or not isinstance(dag.get("nodes"), list):
        return ["dag: falta array de nodos"]
    nodes = dag["nodes"]
    ids = [n.get("id") for n in nodes if isinstance(n, dict)]
    if len(ids) != len(nodes) or any(not isinstance(i, str) or not i for i in ids):
        return ["dag: nodo inválido o id vacío"]
    unique = set(ids)
    if len(unique) != len(ids):
        errs.append("dag: ids duplicados")
    if not nodes:
        errs.append("dag: sin nodos")

    depends: dict[str, set[str]] = {}
    for n in nodes:
        node = n["id"]
        deps = n.get("depends_on", [])
        if not isinstance(deps, list):
            errs.append(f"dag: {node} depends_on no es array")
            continue
        if len(deps) != len(set(map(str, deps))):
            errs.append(f"dag: {node} depends_on repetido")
        depends[node] = set(deps)
        if node in deps:
            errs.append(f"dag: {node} depende de sí mismo")
        for dep in deps:
            if dep not in unique:
                errs.append(f"dag: {node} depende de nodo inexistente {dep}")

    edges = dag.get("edges")
    if not isinstance(edges, list):
        return errs + ["dag: falta array de edges"]
    actual: set[tuple[str, str]] = set()
    for e in edges:
        if not isinstance(e, dict):
            errs.append("dag: edge inválido")
            continue
        src, dst = e.get("from"), e.get("to")
        if src not in unique or dst not in unique:
            errs.append(f"dag: edge inexistente {src!r}->{dst!r}")
            continue
        if (src, dst) in actual:
            errs.append(f"dag: edge duplicado {src}->{dst}")
        actual.add((src, dst))
    expected = {(dep, node) for node, ds in depends.items() for dep in ds if dep in unique}
    for src, dst in sorted(expected - actual):
        errs.append(f"dag: falta edge {src}->{dst} para depends_on")
    for src, dst in sorted(actual - expected):
        errs.append(f"dag: edge {src}->{dst} no declarado en depends_on")

    if len(unique) == len(ids):
        count = {n: 0 for n in unique}
        successors: dict[str, list[str]] = {n: [] for n in unique}
        for src, dst in actual:
            count[dst] += 1
            successors[src].append(dst)
        queue = deque(x for x in ids if count[x] == 0)
        visited = 0
        while queue:
            node = queue.popleft()
            visited += 1
            for dst in successors[node]:
                count[dst] -= 1
                if not count[dst]:
                    queue.append(dst)
        if visited != len(unique):
            errs.append("dag: ciclo de dependencias detectado")
    return errs


def router_errors(doc: dict[str, Any]) -> list[str]:
    errs: list[str] = []
    r = doc.get("mode_router")
    if not isinstance(r, dict):
        return ["router: mode_router ausente"]
    modes = r.get("modes") or {}
    if not isinstance(modes, dict):
        return ["router: modes inválido"]
    default = r.get("default_mode")
    if default not in modes:
        errs.append(f"router: default_mode {default!r} no declarado")
    selector = r.get("selector") or {}
    allowed = selector.get("allowed") or []
    for mode in allowed:
        if mode not in modes:
            errs.append(f"router: selector permite modo no declarado {mode!r}")
    routes = r.get("routes")
    if not isinstance(routes, list) or not routes:
        return errs + ["router: routes ausentes"]
    ids: set[str] = set()
    signatures: set[tuple[int, str]] = set()
    for route in routes:
        if not isinstance(route, dict):
            errs.append("router: ruta no objeto")
            continue
        ident = route.get("id")
        if ident in ids:
            errs.append(f"router: id de ruta duplicado {ident!r}")
        ids.add(ident)
        dest = (route.get("to") or {}).get("mode")
        if dest not in modes:
            errs.append(f"router: ruta {ident} apunta a modo inexistente {dest!r}")
        # Match idéntico al mismo nivel de prioridad = ambigüedad concreta.
        sig = (route.get("priority"), json.dumps(route.get("match"), ensure_ascii=False, sort_keys=True))
        if sig in signatures:
            errs.append(f"router: match/priority duplicado en ruta {ident}")
        signatures.add(sig)
    return errs


def loop_errors(doc: dict[str, Any]) -> list[str]:
    errs: list[str] = []
    loop = doc.get("loop")
    if not isinstance(loop, dict):
        return ["loop: bloque ausente"]
    if loop.get("kind") != "no_stop_until_done":
        errs.append("loop: kind inesperado")
    if loop.get("phases") != ["gather_context", "act", "verify", "repeat"]:
        errs.append("loop: orden de fases distinto del contrato")
    if loop.get("no_escalation") is not True:
        errs.append("loop: no_escalation debe ser true")
    comp = loop.get("completion") or {}
    if comp.get("condition") != "all_nodes_terminal AND all_required_checks_passed":
        errs.append("loop: condición de cierre no coincide")
    limits = loop.get("hard_limits") or {}
    for k in ("max_iterations", "max_wall_clock_s", "max_cost_usd", "max_consecutive_no_progress"):
        v = limits.get(k)
        if isinstance(v, bool) or not isinstance(v, (int, float)) or v <= 0:
            errs.append(f"loop: límite obligatorio {k} inválido")
    if limits.get("on_limit") != "TERMINATE_WITH_REPORT":
        errs.append("loop: debe detenerse con reporte al llegar a límite")
    verdict = doc.get("verdict_policy") or {}
    if verdict.get("fail_closed") is not True:
        errs.append("loop: veredicto fail_closed debe ser true")
    if verdict.get("pass_requires_evidence") is not True:
        errs.append("loop: cierre exige evidencia")
    if verdict.get("self_report_counts_as_evidence") is not False:
        errs.append("loop: auto-reporte del modelo no es evidencia")
    return errs


# ---------------------------------------------------------------- estado del bucle
ESTADOS_TAREA = {"pending", "running", "verifying", "passed", "blocked_with_evidence", "skipped"}


def check_state_errors(doc: dict) -> list[str]:
    """Valida un state/progress.json generado por loop_controller (fail-closed)."""
    errs = []
    if not isinstance(doc, dict):
        return ["progress: no es un objeto JSON"]
    if not doc.get("contract_id") or not isinstance(doc["contract_id"], str):
        errs.append("progress: falta 'contract_id'")
    if not isinstance(doc.get("iteration"), int) or doc["iteration"] < 0:
        errs.append("progress: 'iteration' debe ser entero >= 0")
    if not isinstance(doc.get("cost_usd"), (int, float)) or doc["cost_usd"] < 0:
        errs.append("progress: 'cost_usd' debe ser numero >= 0")
    tasks = doc.get("tasks")
    if not isinstance(tasks, list):
        errs.append("progress: falta lista 'tasks'")
        return errs
    for i, t in enumerate(tasks):
        tag = f"tasks[{i}]"
        if not isinstance(t, dict):
            errs.append(f"{tag}: no es objeto")
            continue
        if not t.get("id") or not isinstance(t["id"], str):
            errs.append(f"{tag}: falta 'id'")
        st = t.get("status")
        if st not in ESTADOS_TAREA:
            errs.append(f"{tag} ({t.get('id', '?')}): status invalido '{st}'")
        if not isinstance(t.get("attempts"), int) or t["attempts"] < 0:
            errs.append(f"{tag} ({t.get('id', '?')}): 'attempts' debe ser entero >= 0")
        ev = t.get("evidence")
        if ev is not None and not isinstance(ev, list):
            errs.append(f"{tag} ({t.get('id', '?')}): 'evidence' debe ser lista")
        # PASS sin evidencia esta prohibido: la evidencia es lo unico que cuenta
        if st in ("passed", "blocked_with_evidence") and not ev:
            errs.append(f"{tag} ({t.get('id', '?')}): status '{st}' sin evidencia")
    return errs


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if len(args) == 2 and args[0] == "--check-state":
        try:
            doc = load(Path(args[1]))
            errors = check_state_errors(doc)
        except Exception as exc:
            print(f"VEREDICTO: FAIL\n - {type(exc).__name__}: {exc}")
            return 1
        if errors:
            print("VEREDICTO: FAIL")
            for e in errors:
                print(" -", e)
            return 1
        print(f"VEREDICTO: PASS (estado del bucle verificado, {len(doc.get('tasks', []))} tareas)")
        return 0
    if len(args) != 1:
        print("Uso: python validate_contract.py ruta/contrato.json | --check-state state/progress.json\nVEREDICTO: FAIL")
        return 2
    try:
        file = Path(args[0])
        doc = load(file)
        schema_path = file.parent / "loop_contract.schema.json"
        if not schema_path.exists():
            schema_path = Path(__file__).resolve().parent / "loop_contract.schema.json"
        schema = load(schema_path)
        errors = (schema_errors(doc, schema) + dag_errors(doc) + router_errors(doc) + loop_errors(doc))
    except Exception as exc:
        print(f"VEREDICTO: FAIL\n - {type(exc).__name__}: {exc}")
        return 1
    if errors:
        print("VEREDICTO: FAIL")
        for e in errors:
            print(" -", e)
        return 1
    print("VEREDICTO: PASS (esquema v1.0 + DAG + router + bucle verificados)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
