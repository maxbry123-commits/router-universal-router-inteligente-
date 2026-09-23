"""Chain runner: gives an agent a CHAIN of steps (DSL DAG in <agent_dir>/chain.yaml) and runs them in order.

Each step is executed by the agent's own framework runner (pocketflow_agent.py, smol_agent.py or auditor_agent.py): the step gets its own
directory `steps/<id>/` (workflow.dag.yaml + TRIGGER.json + results/), the previous step's verified output is added to its context, and the
chain is FAIL_CLOSED: if a step ends BLOCKED, the next steps do not run. Steps that already closed (state CLOSED + output) are SKIPPED, so a
re-run only works on what is pending. `agents-yaiwes/ROUTE.json` (edited by Claude) sets the model route. Priority order:
1) `route_by_group[agent.group]`, if the agent's group has an explicit route (e.g. "chat" -> DeepSeek V4 Flash first, per the Director's order);
2) otherwise `route_code` for steps that produce code (their checks compile or run Python/JavaScript: MiniMax M3 first) or `route_jobs` for
   every other step (NVIDIA first); 3) `route` as a last default. Every agent still records which provider/model actually answered
(crazy_wall.state.json `provider`/`model`), so results can be compared per engine, not just per agent. A step may add
`context_file: [repo-relative paths]` to its context. `agent.post: audit_report` builds the auditor's checklist after the chain.
Time limits (an agent must never hang the run for an hour): every step has a wall-clock budget (STEP_SECONDS, raised 2026-09-22 per the
Director so long steps like the auditor's model passes can finish) and every SmolAgents model call has an HTTP timeout (CALL_SECONDS).

Run: python chain.py <agent_dir>     (env: RIU_BANK_PASSPHRASE)
"""
from __future__ import annotations

import json
import os
import sys
import threading
from pathlib import Path
from typing import Any

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))

from common import boot  # noqa: E402

MAX_PREV_CHARS = 5000
MAX_FILE_CHARS = 14000
STEP_SECONDS = 2400
CALL_SECONDS = 120.0
CODE_CHECKS = ("python_exec", "python_ast", "js_syntax")


def step_agent(agent: dict[str, Any], st: dict[str, Any], routes: dict[str, Any]) -> dict[str, Any]:
    """The agent block for one step. route_by_group[agent.group] wins if set; else route_code/route_jobs by whether the step is code."""
    out = dict(agent)
    by_group = (routes.get("route_by_group") or {}).get(agent.get("group") or "")
    if by_group:
        out["route"] = by_group
    else:
        is_code = any(c.get("kind") in CODE_CHECKS for c in st.get("checks", []))
        key = "route_code" if is_code else "route_jobs"
        if routes.get(key):
            out["route"] = routes[key]
        elif routes.get("route"):
            out["route"] = routes["route"]
    if "fallback" in routes:
        out["fallback"] = routes["fallback"]
    return out


def step_cfg(chain: dict[str, Any], agent: dict[str, Any], st: dict[str, Any], prev: str, prev_id: str | None) -> dict[str, Any]:
    ctx = str((chain.get("context") or {}).get("text", ""))
    for rel in st.get("context_file", []) or []:
        p = boot.REPO / rel
        if p.exists():
            ctx += f"\n\n=== ARCHIVO {rel} ===\n" + p.read_text(encoding="utf-8", errors="ignore")[:MAX_FILE_CHARS]
    if prev:
        ctx += f"\n\nSALIDA VERIFICADA DEL PASO ANTERIOR ({prev_id}):\n{prev[:MAX_PREV_CHARS]}"
    return {"schema": boot.SCHEMA, "execution": {"mode": "fail_closed", "max_parallel": 1, "continue_on_failure": False, "retries": 2},
            "agent": agent, "context": {"text": ctx, "max_chars": 40000}, "task": st["task"], "checks": st["checks"]}


def append_step_output(st: dict[str, Any], out: Path) -> None:
    """Append a verified agent output verbatim to an explicitly configured repo file."""
    rel = st.get("append_output_to")
    if not rel or not out.exists():
        return
    target = (boot.REPO / str(rel)).resolve()
    repo = boot.REPO.resolve()
    if repo not in target.parents and target != repo:
        raise RuntimeError("append_output_to fuera del repo")
    if not target.exists():
        raise RuntimeError(f"append_output_to no existe: {rel}")
    text = out.read_text(encoding="utf-8")
    with target.open("a", encoding="utf-8") as fh:
        fh.write("\n\n" + text.rstrip() + "\n")


def append_output_to_director(st: dict[str, Any], text: str) -> None:
    """Append verified agent output to the Director channel in the checked-out repo.
    GitHub Actions later commits/pushes the modified file. No external compute trigger is used.
    """
    rel = st.get("append_output_to")
    if not rel:
        return
    target = boot.REPO / rel
    if not target.is_file():
        raise RuntimeError(f"DIRECTOR_CHANNEL_NOT_FOUND:{rel}")
    payload = text.rstrip() + "\n"
    current = target.read_text(encoding="utf-8")
    if payload.strip() in current:
        return
    target.write_text(current.rstrip() + "\n\n" + payload, encoding="utf-8")


def already_closed(sd: Path) -> str | None:
    state, out = sd / "crazy_wall.state.json", sd / "results" / "output.txt"
    if state.exists() and out.exists():
        try:
            if json.loads(state.read_text(encoding="utf-8")).get("status") == "CLOSED":
                return out.read_text(encoding="utf-8")
        except json.JSONDecodeError:
            return None
    return None


def run_with_budget(runner: Any, step_dir: str) -> int:
    box: dict[str, int] = {}
    t = threading.Thread(target=lambda: box.setdefault("rc", runner.main(step_dir)), daemon=True)
    t.start()
    t.join(STEP_SECONDS)
    return 98 if t.is_alive() else box.get("rc", 99)


def main(agent_dir: str) -> int:
    chain = yaml.safe_load((Path(agent_dir) / "chain.yaml").read_text(encoding="utf-8"))
    if chain.get("schema") != "yaiwes.chain/v1" or not chain.get("steps"):
        raise SystemExit("chain.yaml inválido (schema yaiwes.chain/v1 y steps son obligatorios)")
    agent = chain["agent"]
    route_file = Path(agent_dir).parent / "ROUTE.json"
    routes = json.loads(route_file.read_text(encoding="utf-8")) if route_file.exists() else {}
    aid, fw = agent["id"], agent["framework"]
    if chain.get("input_block"):
        trigger = json.dumps({"schema": "yaiwes.trigger/v1", "run_id": chain.get("run_id", "CHAIN-001"), "input_block": chain["input_block"]}, ensure_ascii=False)
    else:
        trigger = (Path(agent_dir) / "TRIGGER.json").read_text(encoding="utf-8")
    if fw == "pocketflow":
        import pocketflow_agent as runner
    else:
        if agent.get("runner") == "auditor":
            import auditor_agent as runner
        else:
            import smol_agent as runner
            from common import routes as routes_mod
            runner.candidates = routes_mod.candidates  # every usable key of every provider, in the route order
        orig_model = runner.OAIModel

        def timed_model(**kw: Any) -> Any:
            try:
                return orig_model(client_kwargs={"timeout": CALL_SECONDS, "max_retries": 0}, **kw)
            except TypeError:
                return orig_model(**kw)

        runner.OAIModel = timed_model
    steps = list(chain["steps"])

    # Optional immutable JSON inbox task. The scheduler/push trigger points to one
    # repo-relative instruction file; chain.py turns it into a single ephemeral
    # step without modifying the agent's persistent chain.yaml.
    instruction_rel = os.getenv("RIU_INSTRUCTION_FILE", "").strip()
    if instruction_rel:
        instruction_path = (boot.REPO / instruction_rel).resolve()
        repo_root = boot.REPO.resolve()
        if repo_root not in instruction_path.parents:
            raise SystemExit("RIU_INSTRUCTION_FILE fuera del repo")
        payload = json.loads(instruction_path.read_text(encoding="utf-8"))
        if payload.get("schema") != "yaiwes.instruction/v1":
            raise SystemExit("instruction JSON inválido: schema")
        if payload.get("target_agent") != aid:
            raise SystemExit("instruction JSON target_agent no coincide con agente")
        task_id = str(payload.get("task_id") or "").strip()
        instruction = str(payload.get("instruction") or "").strip()
        if not task_id or not instruction:
            raise SystemExit("instruction JSON requiere task_id + instruction")
        safe_id = "".join(ch if ch.isalnum() or ch in "-_" else "-" for ch in task_id)[:96]
        context_files = [str(x) for x in (payload.get("context_files") or [])]
        director_file = Path(agent_dir) / "README-DIRECTOR.md"
        if payload.get("allow_delegation"):
            instruction += """

DELEGACIÓN AUTORIZADA:
Si necesitas activar agentes subordinados, al FINAL de tu respuesta añade EXACTAMENTE este bloque:
<YAIWES_DELEGATIONS_JSON>
{"delegations":[{"target_agent":"agent-...","instruction":"orden exacta"}]}
</YAIWES_DELEGATIONS_JSON>
Solo usa agentes de tu pool autorizado. Si no necesitas delegar, NO incluyas el bloque.
"""
        step = {
            "id": f"inbox_{safe_id}",
            "context_file": context_files + ([str(director_file.relative_to(boot.REPO))] if director_file.exists() else []),
            "task": instruction,
            "checks": payload.get("checks") or [{"kind": "no_secrets"}],
        }
        if director_file.exists():
            step["append_output_to"] = str(director_file.relative_to(boot.REPO))
        steps = [step]
        chain["input_block"] = json.dumps(payload, ensure_ascii=False, indent=2)

    only_step = os.getenv("RIU_ONLY_STEP")
    if only_step:
        steps = [s for s in steps if s.get("id") == only_step]
        if not steps:
            raise SystemExit(f"RIU_ONLY_STEP no existe en chain.yaml: {only_step}")
    ids = [s["id"] for s in steps]
    done: list[str] = []
    prev, prev_id, failed = "", None, None
    boot.write_state(agent_dir, aid, fw, "RUNNING", group=agent.get("group"), chain=ids, completed=[], failed=[], next_nodes=ids)
    for i, st in enumerate(steps):
        sd = Path(agent_dir) / "steps" / st["id"]
        text = already_closed(sd)
        if text is not None:
            done.append(st["id"])
            prev, prev_id = text, st["id"]
            continue
        sd.mkdir(parents=True, exist_ok=True)
        ag = step_agent(agent, st, routes)
        (sd / "workflow.dag.yaml").write_text(yaml.safe_dump(step_cfg(chain, ag, st, prev, prev_id), allow_unicode=True, sort_keys=False), encoding="utf-8")
        (sd / "TRIGGER.json").write_text(trigger, encoding="utf-8")
        boot.write_state(agent_dir, aid, fw, "RUNNING", current_nodes=[st["id"]], completed=done, next_nodes=ids[i + 1:], route=ag.get("route"))
        rc = run_with_budget(runner, str(sd))
        if rc != 0:
            failed = st["id"] + (" (tiempo agotado)" if rc == 98 else "")
            break
        done.append(st["id"])
        out = sd / "results" / "output.txt"
        append_step_output(st, out)
        prev, prev_id = (out.read_text(encoding="utf-8") if out.exists() else ""), st["id"]
        if st.get("append_output_to"):
            try:
                append_output_to_director(st, prev)
            except Exception as exc:
                failed = st["id"] + f" (director channel: {type(exc).__name__}:{str(exc)[:160]})"
                break
    ok = failed is None
    boot.write_state(agent_dir, aid, fw, "CLOSED" if ok else "BLOCKED", current_nodes=[], completed=done, failed=[] if ok else [failed],
                     next_nodes=[] if ok else ids[len(done) + 1:])
    if agent.get("post") == "audit_report":
        from common import audit_report
        audit_report.build(agent_dir)
    print(f"::notice title=RIU_CHAIN_{aid}::{'CLOSED' if ok else 'BLOCKED en ' + str(failed)} pasos_cerrados={len(done)}/{len(ids)} ({','.join(done)})")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1]))
