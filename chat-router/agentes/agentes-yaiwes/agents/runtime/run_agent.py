"""Agent runner: ONE agent per process, built on the framework the Director named for it.

  framework: pocketflow  -> PocketFlow graph  Generate >> Check(Sheriff) with a fix loop (max 2 retries)
  framework: smolagents  -> SmolAgents CodeAgent with a `sheriff_check` tool (max_steps) + an authoritative Sheriff pass afterwards

The DSL DAG (agents/ORDERS.yaml) is written by Claude; the agent executes it, writes its own Crazy Wall state and result files.
PASS never comes from the model's word: only from the deterministic Sheriff. Keys: only from the unlocked bank.

Run (from `router inteligente universal/`):  RIU_BANK_PASSPHRASE=... python agents/runtime/run_agent.py --agent agent-1-chat
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Any

import yaml

AG = Path(__file__).resolve().parents[1]  # .../agents
ROOT = AG.parent  # router inteligente universal
MK = ROOT / "agent-microkernel"
REPO = ROOT.parent
sys.path[:0] = [str(ROOT), str(MK), str(AG / "runtime")]

import endpoint  # noqa: E402
import sheriff2  # noqa: E402
from kernel import dispatcher  # noqa: E402
from kernel.runner import open_bank  # noqa: E402
from kernel.state_store import StateStore  # noqa: E402

CONTRACT = ("Rol: executor. Autoridad: NONE. No te autocertifiques. Lee el INPUT_BLOCK literal sin reinterpretarlo. "
            "Responde solo lo que pide la tarea, en el formato exacto pedido. Si no puedes o falta evidencia, responde exactamente: GAP: <motivo>.")
MAX_RETRIES = 2


def user_prompt(orders: dict[str, Any], cfg: dict[str, Any], agent_id: str, feedback: list[str] | None) -> str:
    u = (f"INPUT_BLOCK (literal):\n{orders['input_block']}\n\nAGENTE: {agent_id} (área: {cfg['area']}, marco: {cfg['framework']})\n"
         f"TAREA:\n{cfg['task']}\n")
    if feedback:
        u += "\nTU INTENTO ANTERIOR FALLÓ ESTAS COMPROBACIONES:\n- " + "\n- ".join(feedback) + "\nCorrige y responde de nuevo.\n"
    return u


def close(store: StateStore, agent_id: str, cfg: dict[str, Any], wd: Path, text: str, sr: Any, meta: dict[str, Any], attempts: int) -> dict[str, Any]:
    wd.mkdir(parents=True, exist_ok=True)
    out = wd / "output.txt"
    out.write_text(text, encoding="utf-8")
    evidence = sr.evidence + [{"kind": "file", "path": str(out.relative_to(REPO)), "sha256": sheriff2.base.sha256(text)}]
    store.update(agent_id, "CLOSED", completed=["generate", "sheriff"], failed=[], gaps=[], evidence=evidence, next_nodes=[], attempts=attempts,
                 provider=meta["provider"], model=meta["model"], via=meta["via"], framework=cfg["framework"], route_trace=meta.get("trace", []))
    return {"agent": agent_id, "framework": cfg["framework"], "status": "CLOSED", "provider": meta["provider"], "model": meta["model"], "via": meta["via"],
            "attempts": attempts, "output_sha256": sheriff2.base.sha256(text), "gaps": []}


def blocked(store: StateStore, agent_id: str, cfg: dict[str, Any], fails: list[str], attempts: int) -> dict[str, Any]:
    store.update(agent_id, "BLOCKED", failed=["sheriff"], gaps=fails, attempts=attempts, framework=cfg["framework"])
    return {"agent": agent_id, "framework": cfg["framework"], "status": "BLOCKED", "attempts": attempts, "gaps": fails}


def run_pocketflow(agent_id: str, cfg: dict[str, Any], orders: dict[str, Any], store: StateStore, wd: Path, owners: set[str]) -> dict[str, Any]:
    from pocketflow import Flow, Node

    shared: dict[str, Any] = {"attempt": 0, "feedback": None, "gen": None, "result": None}

    class Generate(Node):
        def prep(self, sh: dict[str, Any]) -> dict[str, Any]:
            return sh

        def exec(self, sh: dict[str, Any]) -> dict[str, Any]:
            try:
                msgs = [{"role": "system", "content": CONTRACT}, {"role": "user", "content": user_prompt(orders, cfg, agent_id, sh["feedback"])}]
                return {"ok": dispatcher.call(cfg, msgs, int(cfg.get("max_tokens", 1500)))}
            except RuntimeError as exc:
                return {"error": str(exc)[:300]}

        def post(self, sh: dict[str, Any], prep_res: Any, exec_res: dict[str, Any]) -> str:
            sh["attempt"] += 1
            sh["gen"] = exec_res
            store.update(agent_id, "RUNNING", current_nodes=["generate"], next_nodes=["sheriff"], attempts=sh["attempt"], framework="pocketflow")
            return "check"

    class Check(Node):
        def prep(self, sh: dict[str, Any]) -> dict[str, Any]:
            return sh

        def exec(self, sh: dict[str, Any]) -> dict[str, Any]:
            gen = sh["gen"]
            if "error" in gen:
                return {"passed": False, "failures": [gen["error"]], "evidence": [], "text": ""}
            sr = sheriff2.run(cfg.get("checks", []), gen["ok"]["text"], wd, owners)
            return {"passed": sr.passed, "failures": sr.failures, "evidence": sr.evidence, "text": gen["ok"]["text"], "meta": gen["ok"]}

        def post(self, sh: dict[str, Any], prep_res: Any, res: dict[str, Any]) -> str:
            store.update(agent_id, "VALIDATING", current_nodes=["sheriff"], attempts=sh["attempt"])
            if res["passed"]:
                sr = sheriff2.SheriffResult(passed=True, failures=[], evidence=res["evidence"])
                sh["result"] = close(store, agent_id, cfg, wd, res["text"], sr, res["meta"], sh["attempt"])
                return "pass"
            store.update(agent_id, "GAP", gaps=res["failures"], attempts=sh["attempt"])
            sh["feedback"] = res["failures"]
            if sh["attempt"] > MAX_RETRIES:
                sh["result"] = blocked(store, agent_id, cfg, res["failures"], sh["attempt"])
                return "blocked"
            return "fix"

    class Done(Node):
        def exec(self, prep_res: Any) -> None:
            return None

    gen, chk, done = Generate(), Check(), Done()
    gen - "check" >> chk
    chk - "fix" >> gen
    chk - "pass" >> done
    chk - "blocked" >> done
    Flow(start=gen).run(shared)
    return shared["result"] or blocked(store, agent_id, cfg, ["el grafo terminó sin resultado"], shared["attempt"])


def run_smolagents(agent_id: str, cfg: dict[str, Any], orders: dict[str, Any], store: StateStore, wd: Path, owners: set[str]) -> dict[str, Any]:
    import smolagents

    model_cls = getattr(smolagents, "OpenAIModel", None) or getattr(smolagents, "OpenAIServerModel")
    ep = endpoint.pick(cfg)
    model = model_cls(model_id=ep["model"], api_base=ep["base"], api_key=ep["key"])
    state: dict[str, str] = {"last": ""}

    @smolagents.tool
    def sheriff_check(text: str) -> str:
        """Validates a candidate deliverable with the deterministic Sheriff. Returns PASS, or FAIL followed by the list of failed checks.

        Args:
            text: the complete candidate deliverable, exactly as it would be saved (code in one fenced block).
        """
        state["last"] = text
        r = sheriff2.run(cfg.get("checks", []), text, wd, owners)
        return "PASS" if r.passed else "FAIL: " + "; ".join(r.failures)

    agent = smolagents.CodeAgent(tools=[sheriff_check], model=model, max_steps=int(cfg.get("max_steps", 6)), additional_authorized_imports=[])
    feedback: list[str] | None = None
    fails: list[str] = []
    for attempt in range(1, MAX_RETRIES + 2):
        store.update(agent_id, "RUNNING", current_nodes=["smolagents.CodeAgent"], next_nodes=["sheriff"], attempts=attempt, framework="smolagents",
                     provider=ep["provider"], model=ep["model"], via=ep["via"])
        task = (user_prompt(orders, cfg, agent_id, feedback) +
                "\nUsa la herramienta sheriff_check(text=...) con tu entregable completo hasta que responda PASS. "
                "Cuando responda PASS, llama a final_answer con el entregable completo como una sola cadena (sin explicaciones).")
        try:
            out = str(agent.run(task))
        except Exception as exc:  # noqa: BLE001 - a framework error is evidence, not a crash
            fails = [f"{type(exc).__name__}: {str(exc)[:220]}"]
            store.update(agent_id, "GAP", gaps=fails, attempts=attempt)
            feedback = None
            continue
        text = out if out.strip() else state["last"]
        store.update(agent_id, "VALIDATING", current_nodes=["sheriff"], attempts=attempt)
        sr = sheriff2.run(cfg.get("checks", []), text, wd, owners)
        if sr.passed:
            return close(store, agent_id, cfg, wd, text, sr, ep, attempt)
        fails = feedback = sr.failures
        store.update(agent_id, "GAP", gaps=fails, attempts=attempt)
    return blocked(store, agent_id, cfg, fails, MAX_RETRIES + 1)


def handoff_md(res: dict[str, Any], orders: dict[str, Any]) -> str:
    return (f"# HANDOFF — {res['agent']} ({res['framework']}) — {orders['run_id']}\n\nGenerado por el runner (determinista) el "
            f"{time.strftime('%Y-%m-%d %H:%M:%SZ', time.gmtime())}.\n\n- estado: **{res['status']}**\n- modelo: {res.get('provider', '-')}/{res.get('model', '-')} "
            f"({res.get('via', '-')})\n- intentos: {res.get('attempts', '-')}\n- sha256 de la salida: {(res.get('output_sha256') or '-')[:16]}\n"
            f"- GAPs: {'; '.join(res.get('gaps', [])) or '-'}\n\nEntregables en `results/`. Estado en `crazy_wall.state.json`. "
            "Claude lee estos archivos y activa la siguiente tarea editando `agents/ORDERS.yaml`. Ninguna clave aparece aquí.\n")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--agent", required=True)
    args = ap.parse_args(argv)
    orders = yaml.safe_load((AG / "ORDERS.yaml").read_text(encoding="utf-8"))
    cfg = orders["agents"][args.agent]
    agent_dir = AG / args.agent
    agent_dir.mkdir(parents=True, exist_ok=True)
    store = StateStore(agent_dir, orders["run_id"])
    store.update(args.agent, "PENDING", framework=cfg["framework"], area=cfg["area"])
    owners = set(orders["agents"]) | {"director"}
    try:
        print(f"bank: {open_bank()} credenciales abiertas en memoria")
        fn = {"pocketflow": run_pocketflow, "smolagents": run_smolagents}[cfg["framework"]]
        res = fn(args.agent, cfg, orders, store, agent_dir / "results", owners)
    except Exception as exc:  # noqa: BLE001 - fail closed with the reason recorded
        res = blocked(store, args.agent, cfg, [f"{type(exc).__name__}: {str(exc)[:250]}"], 0)
    (agent_dir / "result.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    (agent_dir / "HANDOFF.md").write_text(handoff_md(res, orders), encoding="utf-8")
    print(f"::notice title=RIU_AGENT::{args.agent} framework={cfg['framework']} status={res['status']} "
          f"model={res.get('provider', '-')}/{res.get('model', '-')} via={res.get('via', '-')} attempts={res.get('attempts', '-')} gaps={'; '.join(res.get('gaps', []))[:200]}")
    return 0 if res["status"] == "CLOSED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
