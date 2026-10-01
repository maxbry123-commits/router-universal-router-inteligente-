"""riu.dag/v1 — deterministic DSL DAG runner: Claude (the brain) writes the plan, the Router executes it.

What it does:
  * `input_block` is the Director's instruction, passed to every node LITERALLY (no reinterpretation).
  * Nodes run in topological order (`needs`); the outputs of the needed nodes are given as context. A node whose dependency
    did not end PASS/DONE_UNVERIFIED is BLOCKED.
  * A node picks its model in exactly one of two ways: `model: {provider, model}` (explicit) or `route: {group}` (group in
    ROUTE_GROUPS: the executor runs that group's model CHAIN, same policy as /chat/route).
  * The executor model has authority NONE and never certifies itself: PASS comes only from deterministic `expect` checks
    (`check_expect`). A node without `expect` ends as DONE_UNVERIFIED, never PASS.
  * Failure path: `retries` (failed checks fed back) -> `escalate_to` model -> FAIL.
  * `loop: {until, max_iterations 1..20}` re-runs the node (previous failed checks fed back) until `until` (same syntax as
    `expect`) passes. Stop reasons: PASSED | MAX_ITERATIONS | REPEATED_x3 (same output+checks 3 times in a row). No sleeping,
    no randomness. A loop node makes exactly one executor call per iteration (so it cannot combine with retries/escalate_to).
  * Every attempt/iteration is written to a hash-chained ledger (tamper-evident); `verify_ledger` re-checks it.
NOTE: the exact field names of Fables' DAG schema are pending the link from the Director; this schema is provisional.
"""
from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Callable
from typing import Any

from . import agent_gates

SCHEMA = "riu.dag/v1"
RESULT_SCHEMA = "riu.dag.result/v1"
EXECUTOR_CONTRACT = (
    "Rol: executor. Autoridad: NONE. No te autocertifiques: nunca declares la tarea verificada ni cerrada. "
    "Lee el INPUT_BLOCK literal, sin reinterpretarlo. Responde únicamente lo que pide el nodo. "
    "Si no puedes o falta evidencia, responde exactamente: GAP: <motivo>."
)
ROUTE_GROUPS = ("default", "code", "minor", "g2")
MAX_LOOP_ITERATIONS = 20
Executor = Callable[..., dict[str, Any]]


class DagError(ValueError):
    pass


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def validate(dag: dict[str, Any], known_providers: set[str] | None = None) -> list[str]:
    errs: list[str] = []
    if dag.get("schema") != SCHEMA:
        errs.append(f"schema debe ser {SCHEMA}")
    if not str(dag.get("input_block", "")).strip():
        errs.append("input_block vacío")
    nodes = dag.get("nodes")
    if not isinstance(nodes, list) or not nodes:
        return errs + ["nodes vacío"]
    ids = [n.get("id") for n in nodes if isinstance(n, dict)]
    if len(ids) != len(nodes) or any(not i for i in ids):
        errs.append("todo nodo necesita id")
    if len(set(ids)) != len(ids):
        errs.append("ids duplicados")
    for n in nodes:
        nid = n.get("id", "?")
        if n.get("type") == "agent":
            errs.extend(f"{nid}: {error}" for error in agent_gates.validate_node(n))
        elif n.get("type") not in (None, "model"):
            errs.append(f"{nid}: tipo desconocido")
        m = n.get("model") or {}
        if n.get("route") is not None:
            r = n["route"]
            if n.get("model"):
                errs.append(f"{nid}: usa model o route, no ambos")
            elif not isinstance(r, dict) or r.get("group") not in ROUTE_GROUPS:
                errs.append(f"{nid}: route.group debe ser uno de {'/'.join(ROUTE_GROUPS)}")
        elif not m.get("provider") or not m.get("model"):
            errs.append(f"{nid}: model.provider y model.model son obligatorios (o route.group)")
        elif known_providers is not None and m["provider"] not in known_providers:
            errs.append(f"{nid}: proveedor desconocido {m['provider']}")
        if n.get("loop") is not None:
            lp = n["loop"]
            mi = lp.get("max_iterations") if isinstance(lp, dict) else None
            if not isinstance(lp, dict) or not isinstance(lp.get("until"), dict) or not lp["until"]:
                errs.append(f"{nid}: loop.until debe ser un expect no vacío")
            elif isinstance(mi, bool) or not isinstance(mi, int) or not 1 <= mi <= MAX_LOOP_ITERATIONS:
                errs.append(f"{nid}: loop.max_iterations debe ser entero 1..{MAX_LOOP_ITERATIONS}")
            if n.get("retries") or n.get("escalate_to"):
                errs.append(f"{nid}: loop no se combina con retries/escalate_to")
        if not str(n.get("instructions", "")).strip():
            errs.append(f"{nid}: instructions vacío")
        for d in n.get("needs", []):
            if d not in ids:
                errs.append(f"{nid}: needs desconocido {d}")
    if not errs:
        try:
            topo_order(nodes)
        except DagError as exc:
            errs.append(str(exc))
    return errs


def topo_order(nodes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_id = {n["id"]: n for n in nodes}
    indeg = {n["id"]: len(set(n.get("needs", []))) for n in nodes}
    out: list[dict[str, Any]] = []
    ready = [n["id"] for n in nodes if indeg[n["id"]] == 0]
    while ready:
        nid = ready.pop(0)
        out.append(by_id[nid])
        for n in nodes:
            if nid in set(n.get("needs", [])):
                indeg[n["id"]] -= 1
                if indeg[n["id"]] == 0:
                    ready.append(n["id"])
    if len(out) != len(nodes):
        raise DagError("el DAG tiene un ciclo")
    return out


def check_expect(reply: str, expect: dict[str, Any] | None) -> list[str]:
    """Deterministic checks. Returns the list of failures (empty = all checks passed)."""
    fails: list[str] = []
    e = expect or {}
    low = reply.lower()
    if reply.strip().upper().startswith("GAP:"):
        fails.append("MODEL_REPORTED_GAP")
    for s in e.get("contains", []):
        if s.lower() not in low:
            fails.append(f"falta '{s}'")
    for s in e.get("not_contains", []):
        if s.lower() in low:
            fails.append(f"no debe contener '{s}'")
    if e.get("regex") and not re.search(e["regex"], reply, re.S):
        fails.append(f"no cumple regex {e['regex']}")
    if "max_chars" in e and len(reply) > int(e["max_chars"]):
        fails.append(f"excede max_chars {e['max_chars']}")
    if "min_chars" in e and len(reply) < int(e["min_chars"]):
        fails.append(f"menos de min_chars {e['min_chars']}")
    if e.get("json") or e.get("json_keys"):
        body = re.sub(r"^```(?:json)?\s*|\s*```$", "", reply.strip())
        try:
            parsed = json.loads(body)
        except json.JSONDecodeError:
            fails.append("no es JSON válido")
        else:
            for k in e.get("json_keys", []):
                if not isinstance(parsed, dict) or k not in parsed:
                    fails.append(f"JSON sin clave '{k}'")
    return fails


def _entry_hash(prev: str, entry: dict[str, Any]) -> str:
    return _sha(prev + json.dumps(entry, sort_keys=True, ensure_ascii=False))


def verify_ledger(ledger: list[dict[str, Any]]) -> bool:
    prev = "GENESIS"
    for item in ledger:
        entry = {k: v for k, v in item.items() if k not in ("prev", "hash")}
        if item.get("prev") != prev or item.get("hash") != _entry_hash(prev, entry):
            return False
        prev = item["hash"]
    return True


def _messages(dag: dict[str, Any], node: dict[str, Any], deps: dict[str, str], agent_prompt: str | None,
              feedback: list[str] | None, dep_chars: int) -> list[dict[str, str]]:
    system = EXECUTOR_CONTRACT + (f"\n\nAGENTE:\n{agent_prompt}" if agent_prompt else "")
    if node.get("type") == "agent":
        system += "\nDevuelve exclusivamente JSON compatible con yaiwes.result/v1. No declares aprobación de Sheriff o Judge."
    user = f"INPUT_BLOCK (literal):\n{dag['input_block']}\n\nNODO {node['id']}" + (f" [{node['stage']}]" if node.get("stage") else "")
    user += f"\nINSTRUCCIONES:\n{node['instructions']}"
    if node.get("type") == "agent":
        user += "\nJOB:\n" + json.dumps(node["input"], ensure_ascii=False, sort_keys=True)
    if deps:
        user += "\n\nSALIDAS DE NODOS PREVIOS:\n" + "\n".join(f"[{k}]\n{v[:dep_chars]}" for k, v in deps.items())
    if feedback:
        user += "\n\nTU INTENTO ANTERIOR FALLÓ ESTAS COMPROBACIONES:\n- " + "\n- ".join(feedback) + "\nCorrige y responde de nuevo."
    return [{"role": "system", "content": system}, {"role": "user", "content": user}]


def _call_node(executor: Executor, node: dict[str, Any], model: dict[str, Any], msgs: list[dict[str, str]]) -> tuple[str, dict[str, Any], bool, str | None, dict[str, str]]:
    """One executor call. Returns (reply, usage, cached, error_text, ledger_id) where ledger_id has provider/model (+group for route nodes)."""
    mt = int(node.get("max_tokens", 512))
    ident = {"provider": model["provider"], "model": model["model"]} if model else {"provider": "route", "model": node["route"]["group"]}
    try:
        if model:
            res = executor(provider=model["provider"], model=model["model"], messages=msgs, max_tokens=mt)
        else:
            res = executor(group=node["route"]["group"], messages=msgs, max_tokens=mt)
            ri = res.get("route") or {}
            ident = {"provider": ri.get("provider") or "route", "model": ri.get("model") or node["route"]["group"], "group": node["route"]["group"]}
        return res["message"].get("content") or "", res.get("usage") or {}, bool(res.get("cached")), None, ident
    except Exception as exc:  # noqa: BLE001 - executor failures are evidence, not crashes
        if not model:
            ident["group"] = node["route"]["group"]
        return "", {}, False, f"{type(exc).__name__}: {str(exc)[:160]}", ident


def run_dag(dag: dict[str, Any], executor: Executor, *, agents: dict[str, str] | None = None,
            known_providers: set[str] | None = None, dep_chars: int = 3000,
            active_truth: dict[str, dict[str, Any]] | None = None,
            state_emit: Callable[[dict[str, str]], dict[str, Any]] | None = None,
            reviews: dict[str, dict[str, dict[str, Any]]] | None = None,
            evidence: dict[str, dict[str, Any]] | None = None,
            archive: Callable[[dict[str, Any]], bool] | None = None) -> dict[str, Any]:
    errs = validate(dag, known_providers)
    if errs:
        raise DagError("; ".join(errs))
    agents = agents or {}
    nodes_out: dict[str, dict[str, Any]] = {}
    replies: dict[str, str] = {}
    ledger: list[dict[str, Any]] = []
    totals = {"calls": 0, "input": 0, "output": 0, "cached_input": 0, "cached_responses": 0}
    prev = "GENESIS"
    agent_nodes = [n["id"] for n in topo_order(dag["nodes"]) if n.get("type") == "agent"]
    halted_by: str | None = None
    for node in topo_order(dag["nodes"]):
        nid = node["id"]
        if halted_by:
            nodes_out[nid] = {"status": "BLOCKED", "blocked_by": [halted_by]}
            continue
        bad_deps = [d for d in node.get("needs", []) if nodes_out[d]["status"] not in ("PASS", "DONE_UNVERIFIED")]
        if bad_deps:
            nodes_out[nid] = {"status": "BLOCKED", "blocked_by": bad_deps}
            continue
        deps = {d: replies[d] for d in node.get("needs", [])}
        prompt_agent = agents.get(node.get("agent", "")) if node.get("agent") else None
        attempts: list[dict[str, Any]] = []
        status, last_reply, last_fails = "FAIL", "", []
        stop_reason: str | None = None

        def record(model: dict[str, Any], msgs: list[dict[str, str]], reply: str, usage: dict[str, Any], cached: bool,
                   exc_txt: str | None, ident: dict[str, str], fails: list[str], verdict: str, extra: dict[str, Any] | None = None) -> None:
            nonlocal prev
            entry = {"node": nid, "attempt": len(attempts) + 1, **ident, **(extra or {}),
                     "prompt_sha256": _sha(json.dumps(msgs, sort_keys=True, ensure_ascii=False)), "reply_sha256": _sha(reply),
                     "cached": cached, "verdict": verdict, "checks_failed": fails}
            item = {**entry, "prev": prev, "hash": _entry_hash(prev, entry)}
            prev = item["hash"]
            ledger.append(item)
            attempts.append({"model": f"{ident['provider']}/{ident['model']}", "verdict": verdict, "checks_failed": fails, **(extra or {})})
            totals["calls"] += 0 if cached else 1
            totals["cached_responses"] += 1 if cached else 0
            totals["input"] += int(usage.get("prompt_tokens") or 0) if not cached else 0
            totals["output"] += int(usage.get("completion_tokens") or 0) if not cached else 0
            totals["cached_input"] += int(usage.get("prompt_cache_hit_tokens") or (usage.get("prompt_tokens_details") or {}).get("cached_tokens") or 0) if not cached else 0

        if node.get("type") == "agent":
            position = agent_nodes.index(nid)
            previous_pass = position == 0 or nodes_out[agent_nodes[position - 1]]["status"] == "PASS"
            reason = agent_gates.preflight(node, position + 1, len(agent_nodes), previous_pass, active_truth)
            if position and agent_nodes[position - 1] not in node.get("needs", []):
                reason = "P1_STEP_DEPENDENCY_MISSING"
            if state_emit is None:
                reason = "STATE_HUB_UNAVAILABLE"
            checkpoint: dict[str, Any] | None = None
            did_call = False
            if reason is None:
                msgs = _messages(dag, node, deps, prompt_agent, None, dep_chars)
                reply, usage, cached, exc_txt, ident = _call_node(executor, node, node.get("model") or {}, msgs)
                did_call = True
                reason = "EXECUTOR_ERROR" if exc_txt else None
                if reason is None:
                    failures = check_expect(reply, node.get("expect"))
                    reason = "AGENT_EXPECT_FAILED" if failures else None
                if reason is None:
                    reason, checkpoint = agent_gates.postflight(node, reply, usage, (reviews or {}).get(nid),
                                                                (evidence or {}).get(nid), archive)
            status = "GAP" if reason else "PASS"
            if state_emit is not None:
                try:
                    receipt = state_emit(agent_gates.event(node, status, reason.split(":", 1)[0] if reason else "VERIFIED"))
                    if not receipt.get("ok"):
                        raise ValueError("STATE_HUB_NO_RECEIPT")
                except Exception:  # noqa: BLE001 - remote state failure must leave the agent blocked
                    reason, status = "STATE_HUB_EMIT_FAILED", "GAP"
            if did_call:
                record(node.get("model") or {}, msgs, reply, usage, cached, exc_txt, ident,
                       [reason] if reason else [], status, {"checkpoint": checkpoint} if checkpoint else None)
            nodes_out[nid] = {"status": status, "attempts": attempts, "checks_failed": [reason] if reason else [],
                              "checkpoint": checkpoint, "state": "needs_intervention" if reason else "verified"}
            if reason:
                nodes_out[nid]["rolled_back_to"] = agent_nodes[position - 1] if position else None
                halted_by = nid
            else:
                replies[nid] = reply
            continue

        if node.get("loop"):
            until, max_it = node["loop"]["until"], int(node["loop"]["max_iterations"])
            feedback = None
            seen: list[tuple[str, tuple[str, ...]]] = []
            for it in range(1, max_it + 1):
                msgs = _messages(dag, node, deps, prompt_agent, feedback, dep_chars)
                reply, usage, cached, exc_txt, ident = _call_node(executor, node, node.get("model") or {}, msgs)
                fails = [f"EXECUTOR_ERROR {exc_txt}"] if exc_txt else check_expect(reply, until)
                verdict = "PASS" if not fails else "FAIL"
                record(node.get("model") or {}, msgs, reply, usage, cached, exc_txt, ident, fails, verdict, {"iteration": it})
                last_reply, last_fails = reply, fails
                seen.append((_sha(reply), tuple(fails)))
                if not fails:
                    status, stop_reason = "PASS", "PASSED"
                    break
                if len(seen) >= 3 and seen[-1] == seen[-2] == seen[-3]:
                    stop_reason = "REPEATED_x3"
                    break
                feedback = fails
            else:
                stop_reason = "MAX_ITERATIONS"
        else:
            models = [node["model"]] if node.get("model") else [{}]
            if node.get("escalate_to"):
                models.append(node["escalate_to"])
            for mi, model in enumerate(models):
                tries = 1 + (int(node.get("retries", 0)) if mi == 0 else 0)
                feedback = None
                for _ in range(tries):
                    msgs = _messages(dag, node, deps, prompt_agent, feedback, dep_chars)
                    reply, usage, cached, exc_txt, ident = _call_node(executor, node, model, msgs)
                    fails = [f"EXECUTOR_ERROR {exc_txt}"] if exc_txt else check_expect(reply, node.get("expect"))
                    verdict = "PASS" if (not fails and node.get("expect")) else ("DONE_UNVERIFIED" if not fails else "FAIL")
                    record(model, msgs, reply, usage, cached, exc_txt, ident, fails, verdict)
                    last_reply, last_fails = reply, fails
                    if verdict in ("PASS", "DONE_UNVERIFIED"):
                        status = verdict
                        break
                    feedback = fails
                if status in ("PASS", "DONE_UNVERIFIED"):
                    break
        nodes_out[nid] = {"status": status, "attempts": attempts, "reply": last_reply[:6000], "reply_sha256": _sha(last_reply),
                          "checks_failed": [] if status != "FAIL" else last_fails}
        if stop_reason:
            nodes_out[nid]["stop_reason"] = stop_reason
            nodes_out[nid]["iterations"] = len(attempts)
        replies[nid] = last_reply
    statuses = {v["status"] for v in nodes_out.values()}
    overall = "GAP" if "GAP" in statuses else ("FAIL" if statuses & {"FAIL", "BLOCKED"} else ("UNVERIFIED" if "DONE_UNVERIFIED" in statuses else "PASS"))
    return {"schema": RESULT_SCHEMA, "id": dag.get("id"), "status": overall, "nodes": nodes_out, "totals": totals,
            "ledger": ledger, "ledger_head": prev, "ledger_valid": verify_ledger(ledger),
            "input_block_sha256": _sha(dag["input_block"])}
