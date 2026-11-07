# health_monitor.py
import signal
import threading
import time
import json
import os
from core_recovery import atomic_write_json

_shutdown_event = threading.Event()

def install_shutdown_handlers():
    """Captura SIGTERM/SIGINT para guardar estado antes de morir."""
    def _handler(signum, frame):
        _shutdown_event.set()
        print(f"⚠️ Señal {signum} capturada. Iniciando apagado seguro...")
    try:
        signal.signal(signal.SIGTERM, _handler)
        signal.signal(signal.SIGINT, _handler)
    except (ValueError, OSError):
        pass

def is_shutting_down() -> bool:
    return _shutdown_event.is_set()

class HealthChecker:
    HEALTH_PATH = "health.json"

    @classmethod
    def refresh(cls, in_flight_node: str = None, status: str = "alive"):
        try:
            atomic_write_json(cls.HEALTH_PATH, {
                "alive": status == "alive",
                "ts": time.time(),
                "in_flight_node": in_flight_node,
                "status": status,
            })
        except Exception:
            pass
