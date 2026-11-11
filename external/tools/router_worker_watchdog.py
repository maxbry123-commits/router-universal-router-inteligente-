"""
router_worker_watchdog.py — Ejecucion aislada con heartbeat y cancelacion
Ubicacion: external/tools/router_worker_watchdog.py
Patron: 100 lineas asyncio (Router/Worker/Watchdog)
"""
import asyncio
import time
import logging
from typing import Callable, Any, Dict

logger = logging.getLogger(__name__)


class Worker:
    def __init__(self, wid: str, fn: Callable, router: 'Router'):
        self.wid = wid
        self.fn = fn
        self.router = router
        self.heartbeat = time.monotonic()
        self.status = "running"
        self.task = None
        self.result = None

    async def run(self):
        try:
            self.result = await self.fn()
            self.heartbeat = time.monotonic()
            await self.router.report(self.wid, self.result, success=True)
        except asyncio.CancelledError:
            self.status = "cancelled"
            logger.warning(f"[Worker] {self.wid} cancelado por Watchdog")
            await self.router.report(self.wid, "Cancelled", success=False)
        except Exception as e:
            self.status = "failed"
            logger.error(f"[Worker] {self.wid} fallo: {e}")
            await self.router.report(self.wid, str(e), success=False)


class Router:
    def __init__(self, watchdog_timeout: float = 96.0):
        self.workers: Dict[str, Worker] = {}
        self.watchdog_timeout = watchdog_timeout
        self._watchdog_task = None

    async def start_watchdog(self):
        self._watchdog_task = asyncio.create_task(self._watchdog_loop())

    async def _watchdog_loop(self):
        while True:
            await asyncio.sleep(5)
            now = time.monotonic()
            for wid, w in list(self.workers.items()):
                if w.status == "running" and (now - w.heartbeat) > self.watchdog_timeout:
                    logger.warning(f"[Watchdog] Timeout en {wid}. Cancelando...")
                    w.task.cancel()

    async def dispatch(self, name: str, fn: Callable) -> str:
        wid = f"worker-{len(self.workers)+1:02d}"
        w = Worker(wid, fn, self)
        self.workers[wid] = w
        w.task = asyncio.create_task(w.run())
        return wid

    async def report(self, wid: str, result: Any, success: bool):
        logger.info(f"[Router] {wid} reporto: {'EXITO' if success else 'FALLO'} -> {result}")
        self.workers.pop(wid, None)

    async def shutdown(self):
        if self._watchdog_task:
            self._watchdog_task.cancel()
        for w in self.workers.values():
            w.task.cancel()
