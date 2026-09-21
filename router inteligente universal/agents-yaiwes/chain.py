"""Chain runner: gives an agent a CHAIN of steps (DSL DAG in <agent_dir>/chain.yaml) and runs them in order.

Each step is executed by the agent's own framework runner (pocketflow_agent.py or smol_agent.py, unchanged): the step gets its own
directory `steps/<id>/` (workflow.dag.yaml + TRIGGER.json + results/), the previous step's verified output is added to its context,
and the chain is FAIL_CLOSED: if a step ends BLOCKED, the next steps do not run. The agent's Crazy Wall (crazy_wall.state.json) shows
which steps closed; deliverables are in steps/<id>/results/. The literal instruction of the Director travels in chain.yaml `input_block`.

Run: python chain.py <agent_dir>     (env: RIU_BANK_PASSPHRASE)
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))

from common import boot  # noqa: E402

MAX_PREV_CHARS = 5000


def step_cfg(chain: dict[str, Any], st: dict[str, Any], prev: str, prev_id: str | None) -> dict[str, Any]:
    ctx = str((chain.get("context") or {}).get("text", ""))
    if prev:
        ctx += f"\n\nSALIDA VERIFICADA DEL PASO ANTERIOR ({prev_id}):\n{prev[:MAX_PREV_CHARS]}"
    return {"schema": boot.SCHEMA, "execution": {"mode": "fail_closed", "max_parallel": 1, "continue_on_failure": False, "retries": 2},
            "agent": chain["agent"], "context": {"text": ctx, "max_chars": 9000}, "task": st["task"], "checks": st["checks"]}


def main(agent_dir: str) -> int:
    chain = yaml.safe_load((Path(agent_dir) / "chain.yaml").read_text(encoding="utf-8"))
    if chain.get("schema") != "yaiwes.chain/v1" or not chain.get("steps"):
        raise SystemExit("chain.yaml inválido (schema yaiwes.chain/v1 y steps son obligatorios)")
    agent = chain["agent"]
    aid, fw = agent["id"], agent["framework"]
    if chain.get("input_block"):
        trigger = json.dumps({"schema": "yaiwes.trigger/v1", "run_id": chain.get("run_id", "CHAIN-001"), "input_block": chain["input_block"]}, ensure_ascii=False)
    else:
        trigger = (Path(agent_dir) / "TRIGGER.json").read_text(encoding="utf-8")
    if fw == "pocketflow":
        import pocketflow_agent as runner
    else:
        import smol_agent as runner
    ids = [s["id"] for s in chain["steps"]]
    done: list[str] = []
    prev, prev_id, failed = "", None, None
    boot.write_state(agent_dir, aid, fw, "RUNNING", group=agent.get("group"), chain=ids, completed=[], failed=[], next_nodes=ids)
    for i, st in enumerate(chain["steps"]):
        sd = Path(agent_dir) / "steps" / st["id"]
        sd.mkdir(parents=True, exist_ok=True)
        (sd / "workflow.dag.yaml").write_text(yaml.safe_dump(step_cfg(chain, st, prev, prev_id), allow_unicode=True, sort_keys=False), encoding="utf-8")
        (sd / "TRIGGER.json").write_text(trigger, encoding="utf-8")
        boot.write_state(agent_dir, aid, fw, "RUNNING", current_nodes=[st["id"]], completed=done, next_nodes=ids[i + 1:])
        rc = runner.main(str(sd))
        if rc != 0:
            failed = st["id"]
            break
        done.append(st["id"])
        out = sd / "results" / "output.txt"
        prev, prev_id = (out.read_text(encoding="utf-8") if out.exists() else ""), st["id"]
    ok = failed is None
    boot.write_state(agent_dir, aid, fw, "CLOSED" if ok else "BLOCKED", current_nodes=[], completed=done, failed=[] if ok else [failed],
                     next_nodes=[] if ok else ids[len(done) + 1:])
    print(f"::notice title=RIU_CHAIN_{aid}::{'CLOSED' if ok else 'BLOCKED en ' + str(failed)} pasos_cerrados={len(done)}/{len(ids)} ({','.join(done)})")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1]))
