"""riu.dag/v1 — DSL DAG runner: Claude (the brain) writes the plan, the Router executes it with the chosen models.

Design rules (aligned with the executor/auditor DSL family, tel.workflow/v3):
  * `input_block` is the Director's instruction, passed to every node LITERALLY (no reinterpretation).
  * The executor model has authority NONE and never certifies itself: PASS comes only from deterministic `expect` checks.
  * A node without `expect` ends as DONE_UNVERIFIED, never PASS.
  * Every attempt is written to a hash-chained ledger (tamper-evident); `verify_ledger` re-checks it.
  * Failure path: retries (with the failed checks fed back) -> `escalate_to` model -> FAIL; dependents become BLOCKED.
NOTE: the exact field names of Fables' DAG schema are pending the link from the Director; this schema is provisional.
"""
from __future__ import annotations

import hashlib
import json
import re
from typing import Any, Callable

SCHEMA = "riu.dag/v1"
RESULT_SCHEMA = "riu.dag.result/v1"
EXECUTOR_CONTRACT = (
    "Rol: executor. Autoridad: NONE. No te autocertifiques: nunca declares la tarea verificada ni cerrada. "
    "Lee el INPUT_BLOCK literal, sin reinterpretarlo. Responde únicamente lo que pide el nodo. "
    "Si no puedes o falta evidencia, responde exactamente: GAP: <motivo>."
)
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
        m = n.get("model") or {}
        if not m.get("provider") or not m.get("model"):
            errs.append(f"{nid}: model.provider y model.model son obligatorios")
        elif known_providers is not None and m["provider"] not in known_providers:
            errs.append(f"{nid}: proveedor desconocido {m['provider']}")
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
    user = f"INPUT_BLOCK (literal):\n{dag['input_block']}\n\nNODO {node['id']}" + (f" [{node['stage']}]" if node.get("stage") else "")
    user += f"\nINSTRUCCIONES:\n{node['instructions']}"
    if deps:
        user += "\n\nSALIDAS DE NODOS PREVIOS:\n" + "\n".join(f"[{k}]\n{v[:dep_chars]}" for k, v in deps.items())
    if feedback:
        user += "\n\nTU INTENTO ANTERIOR FALLÓ ESTAS COMPROBACIONES:\n- " + "\n- ".join(feedback) + "\nCorrige y responde de nuevo."
    return [{"role": "system", "content": system}, {"role": "user", "content": user}]


def run_dag(dag: dict[str, Any], executor: Executor, *, agents: dict[str, str] | None = None,
            known_providers: set[str] | None = None, dep_chars: int = 3000) -> dict[str, Any]:
    errs = validate(dag, known_providers)
    if errs:
        raise DagError("; ".join(errs))
    agents = agents or {}
    nodes_out: dict[str, dict[str, Any]] = {}
    replies: dict[str, str] = {}
    ledger: list[dict[str, Any]] = []
    totals = {"calls": 0, "input": 0, "output": 0, "cached_input": 0, "cached_responses": 0}
    prev = "GENESIS"
    for node in topo_order(dag["nodes"]):
        nid = node["id"]
        bad_deps = [d for d in node.get("needs", []) if nodes_out[d]["status"] not in ("PASS", "DONE_UNVERIFIED")]
        if bad_deps:
            nodes_out[nid] = {"status": "BLOCKED", "blocked_by": bad_deps}
            continue
        deps = {d: replies[d] for d in node.get("needs", [])}
        prompt_agent = agents.get(node.get("agent", "")) if node.get("agent") else None
        models = [node["model"]] + ([node["escalate_to"]] if node.get("escalate_to") else [])
        attempts: list[dict[str, Any]] = []
        status, last_reply, last_fails = "FAIL", "", []
        for mi, model in enumerate(models):
            tries = 1 + (int(node.get("retries", 0)) if mi == 0 else 0)
            feedback: list[str] | None = None
            for _ in range(tries):
                msgs = _messages(dag, node, deps, prompt_agent, feedback, dep_chars)
                try:
                    res = executor(provider=model["provider"], model=model["model"], messages=msgs, max_tokens=int(node.get("max_tokens", 512)))
                    reply = res["message"].get("content") or ""
                    usage, cached, exc_txt = res.get("usage") or {}, bool(res.get("cached")), None
                except Exception as exc:  # noqa: BLE001 - executor failures are evidence, not crashes
                    reply, usage, cached, exc_txt = "", {}, False, f"{type(exc).__name__}: {str(exc)[:160]}"
                fails = [f"EXECUTOR_ERROR {exc_txt}"] if exc_txt else check_expect(reply, node.get("expect"))
                verdict = "PASS" if (not fails and node.get("expect")) else ("DONE_UNVERIFIED" if not fails else "FAIL")
                entry = {"node": nid, "attempt": len(attempts) + 1, "provider": model["provider"], "model": model["model"],
                         "prompt_sha256": _sha(json.dumps(msgs, sort_keys=True, ensure_ascii=False)), "reply_sha256": _sha(reply),
                         "cached": cached, "verdict": verdict, "checks_failed": fails}
                item = {**entry, "prev": prev, "hash": _entry_hash(prev, entry)}
                prev = item["hash"]
                ledger.append(item)
                attempts.append({"model": f"{model['provider']}/{model['model']}", "verdict": verdict, "checks_failed": fails})
                totals["calls"] += 0 if cached else 1
                totals["cached_responses"] += 1 if cached else 0
                totals["input"] += int(usage.get("prompt_tokens") or 0) if not cached else 0
                totals["output"] += int(usage.get("completion_tokens") or 0) if not cached else 0
                totals["cached_input"] += int(usage.get("prompt_cache_hit_tokens") or (usage.get("prompt_tokens_details") or {}).get("cached_tokens") or 0) if not cached else 0
                last_reply, last_fails = reply, fails
                if verdict in ("PASS", "DONE_UNVERIFIED"):
                    status = verdict
                    break
                feedback = fails
            if status in ("PASS", "DONE_UNVERIFIED"):
                break
        nodes_out[nid] = {"status": status, "attempts": attempts, "reply": last_reply[:6000], "reply_sha256": _sha(last_reply),
                          "checks_failed": [] if status != "FAIL" else last_fails}
        replies[nid] = last_reply
    statuses = {v["status"] for v in nodes_out.values()}
    overall = "FAIL" if statuses & {"FAIL", "BLOCKED"} else ("UNVERIFIED" if "DONE_UNVERIFIED" in statuses else "PASS")
    return {"schema": RESULT_SCHEMA, "id": dag.get("id"), "status": overall, "nodes": nodes_out, "totals": totals,
            "ledger": ledger, "ledger_head": prev, "ledger_valid": verify_ledger(ledger),
            "input_block_sha256": _sha(dag["input_block"])}
