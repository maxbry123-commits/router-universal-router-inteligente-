"""Shared boot for the Yaiwes agents: paths, YAML loading (fail-closed), bank opening, context, Crazy Wall state file.

Tokens/keys: only through the encrypted bank (agent-microkernel/runtime-bank*): the passphrase comes from the environment.
Every agent gets ALL the keys (NVIDIA, Groq, Cerebras, Hugging Face, GitHub) through the provider key pools / GitHub accounts.
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path
from typing import Any

import yaml

HERE = Path(__file__).resolve().parents[1]  # agents-yaiwes
ROOT = HERE.parent  # router inteligente universal
MK = ROOT / "agent-microkernel"  # earlier agents stay untouched; only their Sheriff/dispatcher are reused
REPO = ROOT.parent
sys.path[:0] = [str(ROOT), str(MK)]

SCHEMA = "yaiwes.micro-agent/v1"
FRAMEWORKS = {"pocketflow", "smolagents"}
TOP_KEYS = {"schema", "execution", "agent", "task", "context", "checks", "nodes", "edges"}
CONTRACT = ("Rol: executor. Autoridad: NONE. No te autocertifiques. Lee el INPUT_BLOCK literal sin reinterpretarlo. "
            "REGLA PERMANENTE OSS/MOTORES: antes de escribir código nuevo, busca y reutiliza componentes existentes. MINIMUM NECESSARY CHANGE: cero sobreingeniería; usa la solución más corta que cumpla el objetivo; máximo 3 pasos por tarea: reutilizar/adaptar -> cablear -> probar. "
            "Si hace falta adquirir un componente externo, usa exclusivamente los motores canónicos de main. "
            "PROHIBIDO crear desde cero una solución equivalente sin autorización explícita del Director. "
            "El código nuevo solo puede adaptar, mejorar, integrar o cablear componentes existentes, salvo autorización explícita. "
            "No sustituyas motores por git clone, curl, wget, downloader propio ni otra vía de adquisición. "
            "Responde solo lo que pide la tarea, en el formato exacto pedido. Si no puedes o falta evidencia, responde exactamente: GAP: <motivo>.")


def load_agent(agent_dir: str | Path) -> dict[str, Any]:
    cfg = yaml.safe_load((Path(agent_dir) / "workflow.dag.yaml").read_text(encoding="utf-8"))
    errs: list[str] = []
    if cfg.get("schema") != SCHEMA:
        errs.append(f"schema debe ser {SCHEMA}")
    if (cfg.get("execution") or {}).get("mode") != "fail_closed":
        errs.append("execution.mode debe ser fail_closed")
    extra = set(cfg) - TOP_KEYS
    if extra:
        errs.append(f"campos desconocidos: {sorted(extra)}")
    a = cfg.get("agent") or {}
    if a.get("framework") not in FRAMEWORKS:
        errs.append("agent.framework debe ser pocketflow o smolagents")
    if not str(cfg.get("task", "")).strip() or not cfg.get("checks"):
        errs.append("task y checks son obligatorios")
    if errs:
        raise ValueError("; ".join(errs))
    return cfg


def bank_text() -> str:
    """The encrypted bank as base64+gzip text: the single file when it is valid, else the parts (`runtime-bank-v2.part1`, `.part2`, ...)."""
    single = MK / "runtime-bank.db.gz.b64"
    if single.exists():
        text = single.read_text().strip()
        if text.startswith("H4sI"):
            return text
    parts = sorted(MK.glob("runtime-bank-v2.part*"))
    if not parts:
        raise RuntimeError("BANK_FILE_NOT_FOUND")
    return "".join(p.read_text().strip() for p in parts)


def open_bank(agent_id: str) -> int:
    from integration.chat_mvp.vault_bridge import BankError, bridge

    os.environ["RIU_VAULT_PATH"] = f"/tmp/riu_vault_{agent_id}.db"
    try:
        bridge.import_b64gz(bank_text())
    except BankError as exc:
        if str(exc) != "VAULT_EXISTS":
            raise
    return bridge.unlock(os.environ["RIU_BANK_PASSPHRASE"])


def load_context(cfg: dict[str, Any]) -> str:
    ctx = cfg.get("context")
    if not ctx:
        return ""
    if "text" in ctx:
        return str(ctx["text"])[: int(ctx.get("max_chars", 4000))]
    return (REPO / ctx["file"]).read_text(encoding="utf-8")[: int(ctx.get("max_chars", 4000))]


def write_state(agent_dir: str | Path, agent_id: str, framework: str, status: str, **fields: Any) -> None:
    path = Path(agent_dir) / "crazy_wall.state.json"
    cur: dict[str, Any] = {}
    if path.exists():
        try:
            cur = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            cur = {}
    cur.update({"schema": "yaiwes.crazy-wall/v1", "agent": agent_id, "framework": framework, "status": status,
                "updated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}, **fields)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(cur, ensure_ascii=False, indent=1), encoding="utf-8")
    os.replace(tmp, path)


def finish(agent_dir: str | Path, agent_id: str, framework: str, ok: bool, detail: dict[str, Any]) -> int:
    Path(agent_dir, "HANDOFF.md").write_text(
        f"# HANDOFF — {agent_id} ({framework})\n\nEstado: **{'CLOSED' if ok else 'BLOCKED'}**\n\n"
        + "".join(f"- {k}: {v}\n" for k, v in detail.items())
        + "\nGenerado por el agente (determinista). El cerebro (Claude) lee `crazy_wall.state.json` y activa la siguiente tarea "
          "editando `chain.yaml` (o `workflow.dag.yaml`) y despachando `RIU Agents Run`. Ninguna clave aparece aquí.\n", encoding="utf-8")
    print(f"::notice title=RIU_AGENT_{agent_id}::{'CLOSED' if ok else 'BLOCKED'} " + " ".join(f"{k}={v}" for k, v in detail.items()))
    return 0 if ok else 1
