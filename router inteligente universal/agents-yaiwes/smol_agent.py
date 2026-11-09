"""SmolAgents agent runner (agents 2 and 4).

A SmolAgents ToolCallingAgent works the task with two structured tools: `write_deliverable` (saves the complete file) and
`run_sheriff` (runs the deterministic checks and reports PASS or the exact failures). The agent iterates until the Sheriff passes;
then this runner re-runs the Sheriff independently (the agent's word is never enough). Route order: NVIDIA / Groq / Cerebras first,
then DeepSeek V4 Flash / MiniMax M3 (Hugging Face router), all through OpenAI-compatible endpoints with keys from the bank.

GOLDEN short-circuit: if agent root has GOLDEN/<module>.py matching a python_exec check, use those bytes (cero LLM).

Run: python smol_agent.py <agent_dir>   (env: RIU_BANK_PASSPHRASE)
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from common import boot  # noqa: E402
from integration.chat_mvp import core  # noqa: E402
from integration.chat_mvp import providers as prov  # noqa: E402
from kernel import dispatcher, sheriff  # noqa: E402
from smolagents import ToolCallingAgent, tool  # noqa: E402

try:
    from smolagents import OpenAIServerModel as OAIModel
except ImportError:  # newer smolagents renamed it
    from smolagents import OpenAIModel as OAIModel

MAX_CYCLES = 3


def _golden_verbatim(agent_dir: Path, checks: list) -> str | None:
    """If agent root has GOLDEN/<module>.py for a python_exec check, use those bytes (no LLM)."""
    root = agent_dir
    if (agent_dir / "workflow.dag.yaml").exists() and agent_dir.parent.name == "steps":
        root = agent_dir.parent.parent
    golden_dir = root / "GOLDEN"
    if not golden_dir.is_dir():
        return None
    for c in checks or []:
        if c.get("kind") != "python_exec":
            continue
        mod = c.get("module") or ""
        if not mod.endswith(".py"):
            continue
        gp = golden_dir / mod
        if gp.is_file():
            return gp.read_text(encoding="utf-8")
    return None


def candidates(agent: dict) -> list[tuple[str, str, str, str]]:
    """(label, api_base, model_id, api_key) in the Director's order; the fallback only after the whole route."""
    out: list[tuple[str, str, str, str]] = []
    for p in agent.get("route", []):
        keys = prov.env_keys(p)
        if keys:
            out.append((p, prov.PROVIDERS[p]["base"], dispatcher.pick_model(p, keys[0]), keys[0]))
    keys = prov.env_keys("hf")
    for fb in agent.get("fallback", []):
        model = dispatcher.FALLBACK[fb]
        try:
            core.hf_gate(model)
        except ValueError:
            continue
        if keys:
            out.append(("hf", prov.PROVIDERS["hf"]["base"], model, keys[0]))
    return out


def main(agent_dir: str) -> int:
    cfg = boot.load_agent(agent_dir)
    agent, aid = cfg["agent"], cfg["agent"]["id"]
    print(f"{aid}: {boot.open_bank(aid)} credenciales del banco abiertas en memoria")
    trigger = json.loads((Path(agent_dir) / "TRIGGER.json").read_text(encoding="utf-8"))
    wd = Path(agent_dir) / "results"
    wd.mkdir(parents=True, exist_ok=True)
    checks, ctx = cfg["checks"], boot.load_context(cfg)
    boot.write_state(agent_dir, aid, "smolagents", "RUNNING", group=agent.get("group"), current_nodes=["tool_calling_agent"], next_nodes=["sheriff"])

    golden = _golden_verbatim(Path(agent_dir), checks)
    if golden:
        print(f"{aid}: GOLDEN short-circuit (cero LLM)")
        sr = sheriff.run(checks, golden, wd, set())
        if sr.passed:
            (wd / "output.txt").write_text(golden, encoding="utf-8")
            boot.write_state(agent_dir, aid, "smolagents", "CLOSED", gaps=[], evidence=sr.evidence,
                             provider="golden", model="verbatim", via="GOLDEN", attempts=1, route_trace=[])
            return boot.finish(agent_dir, aid, "smolagents", True, {
                "group": agent.get("group"), "attempts": 1, "model": "golden/verbatim", "gaps": "-"})
        boot.write_state(agent_dir, aid, "smolagents", "BLOCKED", failed=["golden"],
                         gaps=sr.failures, attempts=1)
        return boot.finish(agent_dir, aid, "smolagents", False, {
            "group": agent.get("group"), "attempts": 1, "model": "golden/verbatim",
            "gaps": "; ".join(sr.failures)[:200] or "-"})

    box: dict = {"content": None}

    @tool
    def write_deliverable(content: str) -> str:
        """Saves the COMPLETE deliverable (the whole file content, nothing else) so the Sheriff can check it.

        Args:
            content: the complete file content to save.
        """
        box["content"] = content
        return f"guardado: {len(content)} caracteres, sha256={sheriff.sha256(content)[:12]}"

    @tool
    def run_sheriff(note: str) -> str:
        """Runs the deterministic checks on the saved deliverable. Returns PASS or the exact list of failures to fix.

        Args:
            note: free text, ignored.
        """
        if not box["content"]:
            return "FALLA: todavia no guardaste nada con write_deliverable"
        sr = sheriff.run(checks, box["content"], wd, set())
        return "PASS" if sr.passed else "FALLAS: " + " | ".join(sr.failures)

    prompt = (f"{boot.CONTRACT}\n\nINPUT_BLOCK (literal):\n{trigger['input_block']}\n\nAGENTE: {aid}\nTAREA:\n{cfg['task']}\n"
              + (f"\nCONTEXTO:\n{ctx}\n" if ctx else "")
              + "\nProcedimiento obligatorio: 1) llama write_deliverable con el contenido COMPLETO del archivo; 2) llama run_sheriff; "
                "3) si devuelve FALLAS, corrige y repite; 4) cuando devuelva PASS, termina con final_answer('OK').")
    trace: list[str] = []
    closed, used, cycles = False, "-", 0
    for label, base, model_id, key in candidates(agent):
        for _ in range(MAX_CYCLES):
            cycles += 1
            box["content"] = None
            try:
                model = OAIModel(model_id=model_id, api_base=base, api_key=key)
                ToolCallingAgent(tools=[write_deliverable, run_sheriff], model=model, max_steps=8).run(prompt)
            except Exception as exc:  # noqa: BLE001 - a provider/tool-calling failure is evidence, then the next candidate
                trace.append(f"{label}/{model_id}:{type(exc).__name__}:{str(exc)[:80]}")
                break
            if box["content"] and sheriff.run(checks, box["content"], wd, set()).passed:  # independent verification
                closed, used = True, f"{label}/{model_id}"
                break
            trace.append(f"{label}/{model_id}:el Sheriff no dio PASS")
        if closed:
            break
    if closed:
        (wd / "output.txt").write_text(box["content"], encoding="utf-8")
        sr = sheriff.run(checks, box["content"], wd, set())
        boot.write_state(agent_dir, aid, "smolagents", "CLOSED", gaps=[], evidence=sr.evidence, model=used, attempts=cycles, route_trace=trace)
    else:
        boot.write_state(agent_dir, aid, "smolagents", "BLOCKED", failed=["tool_calling_agent"], gaps=trace[-4:], attempts=cycles)
    return boot.finish(agent_dir, aid, "smolagents", closed, {"group": agent.get("group"), "attempts": cycles, "model": used,
                                                              "gaps": "; ".join(trace[-2:])[:200] or "-"})


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1]))
