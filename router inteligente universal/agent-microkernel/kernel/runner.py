"""Micro-kernel runner.

Reads TRIGGER.json + workflow.dag.yaml, runs the agents (agents of the same DAG level in parallel), validates every result with the
deterministic Sheriff (retry max 2 with the failed checks fed back), writes the Crazy Wall state and HANDOFF.md. FAIL_CLOSED:
an agent that cannot pass its checks ends BLOCKED, never "PASS by the model's word". Keys: only from the unlocked bank.

Run (from `router inteligente universal/`):  RIU_BANK_PASSPHRASE=... python agent-microkernel/kernel/runner.py --trigger agent-microkernel/TRIGGER.json
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

MK = Path(__file__).resolve().parents[1]
ROOT = MK.parent  # router inteligente universal
REPO = ROOT.parent
sys.path[:0] = [str(ROOT), str(MK)]

from kernel import dag_loader, dispatcher, sheriff  # noqa: E402
from kernel.state_store import StateStore  # noqa: E402

CONTRACT = ("Rol: executor. Autoridad: NONE. No te autocertifiques. Lee el INPUT_BLOCK literal sin reinterpretarlo. "
            "Responde solo lo que pide la tarea, en el formato exacto pedido. Si no puedes o falta evidencia, responde exactamente: GAP: <motivo>.")
MAX_RETRIES = 2


def open_bank() -> int:
    from integration.chat_mvp.vault_bridge import BankError, bridge

    os.environ.setdefault("RIU_VAULT_PATH", "/tmp/riu_runtime_vault.db")
    try:
        bridge.import_b64gz((MK / "runtime-bank.db.gz.b64").read_text().strip())
    except BankError as exc:
        if str(exc) != "VAULT_EXISTS":
            raise
    return bridge.unlock(os.environ["RIU_BANK_PASSPHRASE"])


def load_context(cfg: dict[str, Any]) -> str:
    ctx = cfg.get("context")
    if not ctx:
        return ""
    text = (REPO / ctx["file"]).read_text(encoding="utf-8")
    if ctx.get("from"):
        start = text.find(ctx["from"])
        end = text.find(ctx["to"], start + 1) if ctx.get("to") else -1
        text = text[start:end if end > start else None] if start >= 0 else text
    return text[: int(ctx.get("max_chars", 3500))]


def run_agent(name: str, dag: dict[str, Any], store: StateStore, done: dict[str, dict[str, Any]], input_block: str) -> dict[str, Any]:
    cfg, wd = dag["agents"][name], MK / "results" / name
    owners = set(dag["agents"]) | {"director"}
    store.update(name, "RUNNING", current_nodes=[cfg["action"]], next_nodes=["sheriff"])
    blocked = [d for d in cfg.get("depends_on", []) if done.get(d, {}).get("status") != "CLOSED"]
    if blocked:
        store.update(name, "BLOCKED", failed=[cfg["action"]], gaps=[f"dependencia no cerrada: {b}" for b in blocked])
        return {"agent": name, "status": "BLOCKED", "gaps": [f"dependencia no cerrada: {b}" for b in blocked]}
    deps_text = "\n".join(f"- {d}: {done[d]['provider']}/{done[d]['model']} sha256={done[d]['output_sha256'][:12]} intentos={done[d]['attempts']}"
                          for d in cfg.get("depends_on", []))
    ctx = load_context(cfg)
    feedback: list[str] | None = None
    fails: list[str] = []
    for attempt in range(MAX_RETRIES + 1):
        user = f"INPUT_BLOCK (literal):\n{done['_input_block']}\n\nAGENTE: {name}\nTAREA:\n{cfg['task']}\n"
        if ctx:
            user += f"\nCONTEXTO:\n{ctx}\n"
        if deps_text:
            user += f"\nRESULTADOS DE AGENTES PREVIOS (cerrados por el Sheriff):\n{deps_text}\n"
        if feedback:
            user += "\nTU INTENTO ANTERIOR FALLÓ ESTAS COMPROBACIONES:\n- " + "\n- ".join(feedback) + "\nCorrige y responde de nuevo.\n"
        try:
            res = dispatcher.call(cfg, [{"role": "system", "content": CONTRACT}, {"role": "user", "content": user}], int(cfg.get("max_tokens", 1500)))
        except RuntimeError as exc:
            fails = [str(exc)[:300]]
            feedback = None
            store.update(name, "GAP", gaps=fails, attempts=attempt + 1)
            continue
        store.update(name, "VALIDATING", provider=res["provider"], model=res["model"], via=res["via"], attempts=attempt + 1)
        sr = sheriff.run(cfg.get("checks", []), res["text"], wd, owners)
        if sr.passed:
            wd.mkdir(parents=True, exist_ok=True)
            out = wd / "output.txt"
            out.write_text(res["text"], encoding="utf-8")
            evidence = sr.evidence + [{"kind": "file", "path": str(out.relative_to(REPO)), "sha256": sheriff.sha256(res["text"])}]
            store.update(name, "CLOSED", completed=[cfg["action"]], failed=[], gaps=[], evidence=evidence, provider=res["provider"], model=res["model"],
                         via=res["via"], attempts=attempt + 1, route_trace=res["trace"], next_nodes=[])
            return {"agent": name, "status": "CLOSED", "provider": res["provider"], "model": res["model"], "via": res["via"], "attempts": attempt + 1,
                    "output_sha256": sheriff.sha256(res["text"]), "trace": res["trace"]}
        fails = sr.failures
        feedback = sr.failures
        store.update(name, "GAP", gaps=sr.failures, attempts=attempt + 1, provider=res["provider"], model=res["model"])
    store.update(name, "BLOCKED", failed=[cfg["action"]], gaps=fails)
    return {"agent": name, "status": "BLOCKED", "gaps": fails}


def handoff(run_id: str, results: dict[str, dict[str, Any]], input_block: str) -> str:
    rows = "\n".join(
        f"| {n} | {r['status']} | {r.get('provider', '-')}/{r.get('model', '-')} | {r.get('via', '-')} | {r.get('attempts', '-')} | "
        f"{(r.get('output_sha256') or '-')[:12]} | {'; '.join(r.get('gaps', [])) or '-'} |" for n, r in results.items())
    return (f"# HANDOFF — {run_id}\n\nGenerado por el microkernel (determinista, sin LLM) el {time.strftime('%Y-%m-%d %H:%M:%SZ', time.gmtime())}.\n\n"
            f"## Input block (literal)\n\n{input_block}\n\n## Agentes\n\n| agente | estado | modelo | vía | intentos | sha256 (12) | GAPs |\n|---|---|---|---|---|---|---|\n{rows}\n\n"
            "## Cómo continuar\n\nEl cerebro (Claude) lee `crazy_wall.state.json` y `results/<agente>/`, y activa la siguiente ronda editando `TRIGGER.json` "
            "(o `workflow.dag.yaml`) y despachando el workflow `RIU Microkernel Run`. Ninguna clave aparece en estos archivos.\n")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--trigger", default=str(MK / "TRIGGER.json"))
    args = ap.parse_args(argv)
    trigger = json.loads(Path(args.trigger).read_text(encoding="utf-8"))
    dag = dag_loader.load(MK / "workflow.dag.yaml")
    run_id, input_block = trigger["run_id"], trigger["input_block"]
    print(f"bank: {open_bank()} credenciales abiertas en memoria")
    store = StateStore(MK, run_id)
    done: dict[str, Any] = {"_input_block": input_block}
    results: dict[str, dict[str, Any]] = {}
    for level in dag_loader.order(dag):
        with ThreadPoolExecutor(max_workers=max(1, min(int(dag["execution"].get("max_parallel", 8)), len(level)))) as pool:
            futs = {n: pool.submit(run_agent, n, dag, store, done, input_block) for n in level}
            for n, f in futs.items():
                results[n] = done[n] = f.result()
    (MK / "results").mkdir(parents=True, exist_ok=True)
    (MK / "results" / "summary.json").write_text(json.dumps({"run_id": run_id, "results": results}, ensure_ascii=False, indent=1), encoding="utf-8")
    (MK / "HANDOFF.md").write_text(handoff(run_id, results, input_block), encoding="utf-8")
    line = " ".join(f"{n}={r['status']}({r.get('provider', '-')}/{r.get('model', '-')},x{r.get('attempts', '-')})" for n, r in results.items())
    ok = all(r["status"] == "CLOSED" for r in results.values())
    print(f"::notice title=RIU_MICROKERNEL::run={run_id} overall={'CLOSED' if ok else 'BLOCKED'} {line}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
