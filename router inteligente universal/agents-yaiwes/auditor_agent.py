"""AUDITOR agent (copy of smol_agent.py, SmolAgents): sheriff / policy / guardian / sentinel with forensic X-ray cross-verification.

Same procedure as the SmolAgents agents (write_deliverable -> run_sheriff until PASS, independent re-check by this runner), plus read-only
forensic tools over the repo (`read_repo_file`, `list_repo_dir`) so the auditor can open the agents' real deliverables and states and REFUTE
their work with evidence. Reads are limited to `Claude notas/`, `router inteligente universal/agents-yaiwes/` and `.github/workflows/`.
Route: every usable key of every provider in the route order (common/routes.py), then the fallback only after the whole route.

Run: python auditor_agent.py <step_dir>   (env: RIU_BANK_PASSPHRASE)   — normally launched by chain.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from common import boot  # noqa: E402
from common.routes import candidates  # noqa: E402
from kernel import sheriff  # noqa: E402
from smolagents import ToolCallingAgent, tool  # noqa: E402

try:
    from smolagents import OpenAIServerModel as OAIModel
except ImportError:  # newer smolagents renamed it
    from smolagents import OpenAIModel as OAIModel

MAX_CYCLES = 3
ALLOWED = ("Claude notas/", "router inteligente universal/agents-yaiwes/", ".github/workflows/")


def safe(rel: str) -> Path | None:
    rel = rel.strip().lstrip("/")
    p = (boot.REPO / rel).resolve()
    if ".." in rel or not any(rel.startswith(a) for a in ALLOWED) or boot.REPO.resolve() not in p.parents:
        return None
    return p


def main(agent_dir: str) -> int:
    cfg = boot.load_agent(agent_dir)
    agent, aid = cfg["agent"], cfg["agent"]["id"]
    print(f"{aid}: {boot.open_bank(aid)} credenciales del banco abiertas en memoria")
    trigger = json.loads((Path(agent_dir) / "TRIGGER.json").read_text(encoding="utf-8"))
    wd = Path(agent_dir) / "results"
    wd.mkdir(parents=True, exist_ok=True)
    checks, ctx = cfg["checks"], boot.load_context(cfg)
    boot.write_state(agent_dir, aid, "smolagents", "RUNNING", group=agent.get("group"), current_nodes=["auditor"], next_nodes=["sheriff"])
    box: dict = {"content": None}

    @tool
    def read_repo_file(path: str) -> str:
        """Reads a text file of the repo (read-only; only Claude notas/, router inteligente universal/agents-yaiwes/ and .github/workflows/).

        Args:
            path: repo-relative path, for example 'Claude notas/RIU-0124-agentes-cadena-chat-hf-y-puente-vercel.md'.
        """
        p = safe(path)
        if p is None or not p.is_file():
            return "NO_ENCONTRADO_O_NO_PERMITIDO"
        return p.read_text(encoding="utf-8", errors="ignore")[:6000]

    @tool
    def list_repo_dir(path: str) -> str:
        """Lists the entries of a repo directory (read-only, same allowed roots as read_repo_file).

        Args:
            path: repo-relative directory path, for example 'router inteligente universal/agents-yaiwes/agent-1-chat-hf/steps'.
        """
        p = safe(path)
        if p is None or not p.is_dir():
            return "NO_ENCONTRADO_O_NO_PERMITIDO"
        return "\n".join(sorted(e.name + ("/" if e.is_dir() else "") for e in p.iterdir())[:80])

    @tool
    def write_deliverable(content: str) -> str:
        """Saves the COMPLETE deliverable (the whole JSON/file content, nothing else) so the Sheriff can check it.

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
            return "FALLA: todavía no guardaste nada con write_deliverable"
        sr = sheriff.run(checks, box["content"], wd, set())
        return "PASS" if sr.passed else "FALLAS: " + " | ".join(sr.failures)

    prompt = (f"{boot.CONTRACT}\n\nERES EL AUDITOR (sheriff / guardián / centinela). No confías en nadie: cada afirmación se comprueba contra el texto "
              f"literal del Director y contra los archivos reales de los agentes (read_repo_file / list_repo_dir).\n\n"
              f"INPUT_BLOCK (literal):\n{trigger['input_block']}\n\nTAREA:\n{cfg['task']}\n"
              + (f"\nCONTEXTO:\n{ctx}\n" if ctx else "")
              + "\nProcedimiento obligatorio: 1) llama write_deliverable con el JSON COMPLETO; 2) llama run_sheriff; 3) si devuelve FALLAS, corrige y "
                "repite; 4) cuando devuelva PASS, termina con final_answer('OK'). Las citas deben copiarse LETRA POR LETRA del texto del Director.")
    trace: list[str] = []
    closed, used, cycles = False, "-", 0
    for label, base, model_id, key in candidates(agent):
        for _ in range(MAX_CYCLES):
            cycles += 1
            box["content"] = None
            try:
                model = OAIModel(model_id=model_id, api_base=base, api_key=key)
                ToolCallingAgent(tools=[read_repo_file, list_repo_dir, write_deliverable, run_sheriff], model=model, max_steps=10).run(prompt)
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
        boot.write_state(agent_dir, aid, "smolagents", "BLOCKED", failed=["auditor"], gaps=trace[-4:], attempts=cycles)
    return boot.finish(agent_dir, aid, "smolagents", closed, {"group": agent.get("group"), "attempts": cycles, "model": used,
                                                              "gaps": "; ".join(trace[-2:])[:200] or "-"})


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1]))
