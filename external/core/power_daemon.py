"""power_daemon.py — Adaptador del núcleo (MINIMAX 4).

Expone `PowerDaemon` con start()/stop() sobre el monitor de inactividad
implementado en external/tools/power_daemon.py, de modo que el proxy pueda
cablear el auto-apagado por inactividad en su ciclo de vida sin duplicar
lógica ni reescribir el módulo ya entregado.
"""
import asyncio
import threading

from external.tools.power_daemon import (
    IDLE_TIMEOUT_SEC,
    LOCK_FILE,
    keep_alive,
    monitor_idle,
)

__all__ = [
    "PowerDaemon",
    "keep_alive",
    "monitor_idle",
    "IDLE_TIMEOUT_SEC",
    "LOCK_FILE",
]


class PowerDaemon:
    """Ejecuta monitor_idle() en un hilo de fondo y permite detenerlo."""

    def __init__(self):
        self._thread = None
        self._loop = None
        self._task = None

    @property
    def running(self) -> bool:
        return bool(self._thread and self._thread.is_alive())

    def start(self) -> bool:
        """Arranca el daemon. Devuelve False si ya estaba en marcha."""
        if self.running:
            return False
        self._thread = threading.Thread(
            target=self._run, name="power-daemon", daemon=True
        )
        self._thread.start()
        return True

    def _run(self):
        loop = asyncio.new_event_loop()
        self._loop = loop
        asyncio.set_event_loop(loop)
        self._task = loop.create_task(monitor_idle())
        try:
            loop.run_until_complete(self._task)
        except asyncio.CancelledError:
            pass
        except Exception as e:  # pragma: no cover
            print(f"[INFRA] power_daemon detenido por error: {e}")
        finally:
            try:
                loop.close()
            except Exception:  # pragma: no cover
                pass

    def stop(self, timeout: float = 5.0) -> bool:
        """Cancela el monitor y espera al hilo. Devuelve False si no corría."""
        if not self.running:
            return False
        if self._loop and self._task:
            self._loop.call_soon_threadsafe(self._task.cancel)
        if self._thread:
            self._thread.join(timeout=timeout)
        return True
