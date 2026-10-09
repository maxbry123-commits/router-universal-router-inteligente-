"""Registro de motores de la Fábrica UI + ejecución en paralelo."""
from __future__ import annotations

import asyncio

from capability_engine import CapabilityEngine
from canvas_engine import CanvasEngine
from layout_engine import LayoutEngine
from action_flow_engine import ActionFlowEngine
from sandbox_engine import SandboxEngine
from qa_engine import QAEngine

ENGINE_REGISTRY = {
    "ui.capability": CapabilityEngine,
    "ui.canvas": CanvasEngine,
    "ui.layout": LayoutEngine,
    "ui.actions": ActionFlowEngine,
    "code.sandbox": SandboxEngine,
    "qa.visual": QAEngine,
}


def create_engines(**kwargs) -> dict:
    """Instancia todos los motores. kwargs: capability_components, etc."""
    engines = {}
    for eid, cls in ENGINE_REGISTRY.items():
        if eid == "ui.capability":
            engines[eid] = cls(
                components=kwargs.get("capability_components"),
                components_dir=kwargs.get("components_dir"),
            )
        else:
            engines[eid] = cls()
    return engines


async def ejecutar_en_paralelo(tareas: list[dict]) -> list[dict]:
    """Cada tarea: {"engine": <instancia|id>, "task": {...}, "context": {...}}"""
    async def run_one(t):
        engine = t["engine"]
        if isinstance(engine, str):
            engine = ENGINE_REGISTRY[engine]()
        return await engine.execute(t["task"], t.get("context"))
    return await asyncio.gather(*(run_one(t) for t in tareas))
