"""power_daemon.py — Auto-apagado por inactividad."""
import asyncio
import time
import os
import logging
from .space_power_manager import SpacePowerManager

logger = logging.getLogger(__name__)
LOCK_FILE = "/tmp/yaiwes_last_request.lock"
IDLE_TIMEOUT_SEC = 1800  # 30 minutos

def keep_alive():
    """Renueva el archivo de bloqueo para indicar que hay actividad."""
    with open(LOCK_FILE, "w") as f:
        f.write(str(time.time()))

async def monitor_idle():
    """Revisa cada 5 minutos si hay inactividad y apaga el Grupo 2."""
    while True:
        await asyncio.sleep(300)  # 5 min
        if not os.path.exists(LOCK_FILE):
            continue
            
        last_req = float(open(LOCK_FILE).read())
        idle_time = time.time() - last_req
        
        if idle_time > IDLE_TIMEOUT_SEC:
            logger.warning(f"Inactividad de {idle_time/60:.0f} min. Apagando Grupo 2 (LLM) por ahorro.")
            SpacePowerManager.set_power("llm", on=False)
            os.remove(LOCK_FILE)  # Evitar doble apagado
        else:
            logger.info(f"Actividad reciente. Tiempo restante antes de apagar: {(IDLE_TIMEOUT_SEC - idle_time)/60:.0f} min.")
