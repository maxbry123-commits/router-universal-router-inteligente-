"""
control_bridge.py — Puente Data Plane a Control Plane (Salida 1/3)
Ubicacion: ROUTER MVP v1/system_prompt_py/control_bridge.py
Si router_llm_hf existe: watchdog 96s + heartbeat + recall disponibles.
Si no existe: passthrough total. El Data Plane nunca cae.
"""
import asyncio
import logging

logger = logging.getLogger(__name__)

try:
    from router_llm_hf import Watchdog as _Watchdog
    from router_llm_hf import RecallEngine as _RecallEngine
    CONTROL_PLANE = True
except Exception:
    _Watchdog = None
    _RecallEngine = None
    CONTROL_PLANE = False


class ControlBridge:
    def __init__(self):
        self.available = CONTROL_PLANE
        self.watchdog = _Watchdog() if CONTROL_PLANE else None
        self.recall = _RecallEngine() if CONTROL_PLANE else None

    async def run(self, task_id, coro):
        if not self.available:
            return await coro
        await self.watchdog.heartbeat(task_id)
        return await self.watchdog.run_with_timeout(task_id, coro)

    async def run_with_recall(self, task_id, func, error_feedback=None):
        if not self.available:
            return await func(None)
        return await self.recall.execute_with_recall(task_id, func, error_feedback)

    def status(self):
        return {
            "control_plane": self.available,
            "watchdog": self.watchdog is not None,
            "recall": self.recall is not None,
        }


BRIDGE = ControlBridge()
