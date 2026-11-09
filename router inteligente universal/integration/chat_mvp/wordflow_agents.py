"""Mirror of the Wordflow LOOP Yaiwes fleet (repo `agentes`, `➡️📂 wordflow loop code Yaiwes/➡️📂 readme indice agentes.md`)
as chat agents. This mirrors the ROLES (personas with the Wordflow role and the executor contract); it does NOT run the
external tool runtimes (OpenHands, Aider, ...). Model preference follows the Director's rule: MiniMax for code,
DeepSeek for minor tasks, Kimi for review/audit. Only providers with a configured key are usable at run time.
"""
from __future__ import annotations

from typing import Any

from .store import Store

CONTRACT = ("Trabajas dentro del DSL DAG como executor con autoridad NONE: no te autocertificas, lees el INPUT_BLOCK literal, "
            "respondes solo lo que pide el nodo y, si no puedes o falta evidencia, respondes exactamente: GAP: <motivo>.")

CODE = ["hf/MiniMaxAI/MiniMax-M3", "nvidia/nvidia/nemotron-3-super-120b-a12b"]
MINOR = ["hf/deepseek-ai/DeepSeek-V4-Flash", "nvidia/nvidia/nemotron-3-super-120b-a12b"]
REVIEW = ["hf/moonshotai/Kimi-K3", "hf/deepseek-ai/DeepSeek-V4-Pro"]

# id, name, wordflow role, state in the engines repo, preferred models
FLEET: tuple[tuple[str, str, str, str, list[str]], ...] = (
    ("wf-opencode", "OpenCode", "writer/executor", "ENCONTRADO (OpenCode/)", CODE),
    ("wf-openhands", "OpenHands", "review/repair", "ENCONTRADO (OpenHands/)", CODE),
    ("wf-openclaw", "OpenClaw", "auditor/coordinador/gateway", "FAMILIA_ENCONTRADA (OpenClaw-RL/)", REVIEW),
    ("wf-claude-code", "Claude Code CLI", "flow/execution/wiring review", "RESUELTO_EN_STEP2", REVIEW),
    ("wf-mimo-code", "Mimo Code", "flow/execution/wiring review", "RESUELTO_EN_STEP2", CODE),
    ("wf-codex", "Codex", "auditor técnico", "RESUELTO_EN_STEP2", REVIEW),
    ("wf-hermes", "Hermes", "auditor/worker", "EXTERNAL_NOT_VENDORED", MINOR),
    ("wf-aider", "Aider", "editor/council", "RESUELTO_EN_STEP2", CODE),
    ("wf-muse-glimmer", "Muse/Glimmer Code", "council/revisión", "EXTERNAL_NOT_VENDORED", REVIEW),
    ("wf-kimi-k-code", "Kimi K Code CLI", "council/revisión", "RESUELTO_EN_STEP2", REVIEW),
    ("wf-smolagents", "SmolAgents", "auditor", "RESUELTO_EN_STEP2", MINOR),
    ("wf-qwen-code", "Qwen Code CLI", "council/contraste", "RESUELTO_EN_STEP2", CODE),
    ("wf-cline", "Cline", "programación auxiliar", "RESUELTO_EN_STEP2", CODE),
    ("wf-goose", "Goose", "investigación auxiliar", "EXTERNAL_NOT_VENDORED", MINOR),
)


def fleet_definitions() -> list[dict[str, Any]]:
    return [
        {"id": aid, "name": f"{name} (Wordflow)", "role": role,
         "system_prompt": f"Eres {name}, agente del fleet Wordflow LOOP Yaiwes. Rol en el Wordflow: {role}. Estado en el repo de motores: {state}. {CONTRACT}",
         "models": models}
        for aid, name, role, state, models in FLEET
    ]


def seed(store: Store) -> int:
    """Upsert the 14 fleet agents (idempotent). Returns how many were written."""
    defs = fleet_definitions()
    for d in defs:
        store.upsert_agent(d["id"], d["name"], d["role"], d["system_prompt"], d["models"])
    return len(defs)
