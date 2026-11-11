"""router_worker_watchdog.py — Router/Worker/Watchdog con heartbeat real."""
import asyncio
import time
import logging
from typing import Callable, Any, Dict

logger = logging.getLogger(__name__)
HEARTBEAT_INTERVAL = 30.0


class Worker:
    def __init__(self, wid: str, fn: Callable, router: 'Router'):
        self.wid = wid
        self.fn = fn
        self.router = router
        self.heartbeat = time.monotonic()
        self.status = "running"
        self.task = None
        self.result = None
        self._heartbeat_task = None

    def tick(self):
        self.heartbeat = time.monotonic()

    async def _beat_loop(self):
        while self.status == "running":
            await asyncio.sleep(HEARTBEAT_INTERVAL)
            self.tick()

    async def run(self):
        self._heartbeat_task = asyncio.create_task(self._beat_loop())
        try:
            if asyncio.iscoroutinefunction(self.fn):
                self.result = await self.fn()
            else:
                self.result = await asyncio.get_event_loop().run_in_executor(None, self.fn)
            self.status = "done"
            await self.router.report(self.wid, self.result, success=True)
        except asyncio.CancelledError:
            self.status = "cancelled"
            await self.router.report(self.wid, "Cancelled", success=False)
        except Exception as e:
            self.status = "failed"
            await self.router.report(self.wid, str(e), success=False)
        finally:
            if self._heartbeat_task:
                self._heartbeat_task.cancel()


class Router:
    def __init__(self, watchdog_timeout: float = 96.0):
        self.workers: Dict[str, Worker] = {}
        self.watchdog_timeout = watchdog_timeout
        self._watchdog_task = None
        self._counter = 0

    async def start_watchdog(self):
        self._watchdog_task = asyncio.create_task(self._watchdog_loop())

    async def _watchdog_loop(self):
        while True:
            await asyncio.sleep(5)
            now = time.monotonic()
            for wid, w in list(self.workers.items()):
                if w.status == "running" and (now - w.heartbeat) > self.watchdog_timeout:
                    logger.warning(f"[Watchdog] timeout {wid}")
                    w.task.cancel()

    async def dispatch(self, name: str, fn: Callable) -> str:
        self._counter += 1
        wid = f"{name}-{self._counter:03d}"
        w = Worker(wid, fn, self)
        self.workers[wid] = w
        w.task = asyncio.create_task(w.run())
        return wid

    async def report(self, wid: str, result: Any, success: bool):
        logger.info(f"[Router] {wid} {'OK' if success else 'FAIL'}: {result}")
        self.workers.pop(wid, None)

    def active(self) -> list:
        return [w.wid for w in self.workers.values() if w.status == "running"]

    async def shutdown(self):
        if self._watchdog_task:
            self._watchdog_task.cancel()
        for w in self.workers.values():
            if w.task:
                w.task.cancel()
