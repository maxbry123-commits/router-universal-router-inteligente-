"""
watchdog.py — Heartbeat 30s y timeout 96s por llamada (Control Plane)
"""
from __future__ import annotations
import asyncio
import time
import logging
from typing import Dict, Optional, Callable, Awaitable, Any

logger = logging.getLogger(__name__)


class Watchdog:
    HEARTBEAT_INTERVAL_S = 30.0
    CALL_TIMEOUT_S = 96.0

    def __init__(self) -> None:
        self._heartbeats: Dict[str, float] = {}
        self._active_calls: Dict[str, float] = {}
        self._lock = asyncio.Lock()

    async def heartbeat(self, task_id: str) -> None:
        async with self._lock:
            self._heartbeats[task_id] = time.time()

    async def start_call(self, task_id: str) -> None:
        async with self._lock:
            self._active_calls[task_id] = time.time()

    async def end_call(self, task_id: str) -> None:
        async with self._lock:
            self._active_calls.pop(task_id, None)

    async def is_healthy(self, task_id: str) -> bool:
        async with self._lock:
            last = self._heartbeats.get(task_id)
            if not last:
                return False
            elapsed = time.time() - last
            return not (elapsed >= self.HEARTBEAT_INTERVAL_S * 2)

    async def check_timeout(self, task_id: str) -> bool:
        async with self._lock:
            start = self._active_calls.get(task_id)
            if not start:
                return False
            return (time.time() - start) >= self.CALL_TIMEOUT_S

    async def run_with_timeout(self, task_id: str, coro: Awaitable[Any],
                               on_timeout: Optional[Callable[[str], Awaitable[None]]] = None) -> Any:
        await self.start_call(task_id)
        try:
            return await asyncio.wait_for(coro, timeout=self.CALL_TIMEOUT_S)
        except asyncio.TimeoutError:
            logger.warning("Task %s timeout %.0fs", task_id, self.CALL_TIMEOUT_S)
            if on_timeout:
                await on_timeout(task_id)
            raise
        finally:
            await self.end_call(task_id)

    async def snapshot(self) -> Dict[str, Any]:
        async with self._lock:
            return {
                "active_heartbeats": len(self._heartbeats),
                "active_calls": len(self._active_calls),
            }
