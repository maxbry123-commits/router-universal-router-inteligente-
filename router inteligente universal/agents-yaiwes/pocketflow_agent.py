"""PocketFlow agent runner (agents 1 and 3).

PocketFlow only runs the graph:  Execute -> Validate -> (fix -> Execute) | done | blocked  (max 2 fixes, per the Director's DSL).
The model call goes through the Router core (route: NVIDIA/Groq/Cerebras first, then DeepSeek V4 Flash / MiniMax M3);
the Sheriff is deterministic. The LLM cannot invent nodes, skip steps or change the rules of the graph.

Run: python pocketflow_agent.py <agent_dir>   (env: RIU_BANK_PASSPHRASE)
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from common import boot  # noqa: E402
from kernel import dispatcher, sheriff  # noqa: E402
from pocketflow import Flow, Node  # noqa: E402

MAX_FIXES = 2


class Execute(Node):
    def prep(self, shared):
        user = f"INPUT_BLOCK (literal):\n{shared['input_block']}\n\nAGENTE: {shared['id']}\nTAREA:\n{shared['task']}\n"
        if shared["context"]:
            user += f"\nCONTEXTO:\n{shared['context']}\n"
        if shared.get("feedback"):
            user += "\nTU INTENTO ANTERIOR FALLÓ ESTAS COMPROBACIONES:\n- " + "\n- ".join(shared["feedback"]) + "\nCorrige y responde de nuevo.\n"
        return [{"role": "system", "content": boot.CONTRACT}, {"role": "user", "content": user}]

    def exec(self, messages):
        return dispatcher.call(self.params["cfg"], messages, int(self.params.get("max_tokens", 1500)))

    def exec_fallback(self, prep_res, exc):
        return {"error": str(exc)[:300]}

    def post(self, shared, prep_res, res):
        shared["attempt"] += 1
        if "error" in res:
            shared["feedback"] = None
            shared["gaps"] = [res["error"]]
            boot.write_state(shared["dir"], shared["id"], "pocketflow", "GAP", gaps=shared["gaps"], attempts=shared["attempt"])
            return "retry" if shared["attempt"] <= MAX_FIXES else "blocked"
        shared["res"] = res
        boot.write_state(shared["dir"], shared["id"], "pocketflow", "VALIDATING", provider=res["provider"], model=res["model"],
                         via=res["via"], attempts=shared["attempt"])
        return "validate"


class Validate(Node):
    def post(self, shared, prep_res, exec_res):
        res = shared["res"]
        sr = sheriff.run(shared["checks"], res["text"], Path(shared["dir"]) / "results", shared["owners"])
        if sr.passed:
            out = Path(shared["dir"]) / "results" / "output.txt"
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(res["text"], encoding="utf-8")
            shared["closed"] = True
            shared["evidence"] = sr.evidence
            boot.write_state(shared["dir"], shared["id"], "pocketflow", "CLOSED", gaps=[], evidence=sr.evidence, provider=res["provider"],
                             model=res["model"], via=res["via"], attempts=shared["attempt"], route_trace=res["trace"])
            return "done"
        shared["feedback"] = sr.failures
        shared["gaps"] = sr.failures
        boot.write_state(shared["dir"], shared["id"], "pocketflow", "GAP", gaps=sr.failures, attempts=shared["attempt"])
        return "fix" if shared["attempt"] <= MAX_FIXES else "blocked"


def main(agent_dir: str) -> int:
    cfg = boot.load_agent(agent_dir)
    agent = cfg["agent"]
    aid = agent["id"]
    n = boot.open_bank(aid)
    print(f"{aid}: {n} credenciales del banco abiertas en memoria")
    trigger = __import__("json").loads((Path(agent_dir) / "TRIGGER.json").read_text(encoding="utf-8"))
    shared = {"id": aid, "dir": str(agent_dir), "task": cfg["task"], "checks": cfg["checks"], "context": boot.load_context(cfg),
              "input_block": trigger["input_block"], "owners": set(), "attempt": 0, "feedback": None, "closed": False, "gaps": []}
    boot.write_state(agent_dir, aid, "pocketflow", "RUNNING", group=agent.get("group"), current_nodes=["execute"], next_nodes=["sheriff"])
    execute, validate = Execute(max_retries=1), Validate()
    params = {"cfg": {"route": agent.get("route", []), "fallback": agent.get("fallback", [])}, "max_tokens": agent.get("max_tokens", 1500)}
    execute.set_params(params)
    execute - "validate" >> validate
    execute - "retry" >> execute
    validate - "fix" >> execute
    Flow(start=execute).run(shared)
    if not shared["closed"]:
        boot.write_state(agent_dir, aid, "pocketflow", "BLOCKED", failed=["execute"], gaps=shared["gaps"], attempts=shared["attempt"])
    return boot.finish(agent_dir, aid, "pocketflow", shared["closed"], {
        "group": agent.get("group"), "attempts": shared["attempt"],
        "model": (f"{shared['res']['provider']}/{shared['res']['model']}" if shared.get("res") else "-"),
        "gaps": "; ".join(shared["gaps"])[:200] or "-"})


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1]))
