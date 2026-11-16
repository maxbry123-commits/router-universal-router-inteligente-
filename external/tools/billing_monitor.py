"""billing_monitor.py — Monitorea el tiempo de ejecución y avisa sobre costes."""
import time
import logging
from datetime import datetime
from .space_power_manager import SpacePowerManager

logger = logging.getLogger(__name__)

class BillingMonitor:
    # Estimación: cpu-upgrade cuesta ~$0.03/hora en HF
    COST_PER_HOUR = 0.03

    @staticmethod
    def check_runtime_cost() -> dict:
        status_compute = SpacePowerManager.get_status("compute")
        status_llm = SpacePowerManager.get_status("llm")
        
        active_compute = sum(1 for s in status_compute.values() if s == "RUNNING")
        active_llm = sum(1 for s in status_llm.values() if s == "RUNNING")
        
        total_active = active_compute + active_llm
        hourly_cost = total_active * BillingMonitor.COST_PER_HOUR
        
        alert = hourly_cost > 0.10  # Alerta si supera $0.10/hora
        
        if alert:
            logger.warning(f"⚠️ ALERTA DE FACTURACIÓN: {total_active} Spaces activos. Coste estimado: ${hourly_cost:.2f}/hora")
        
        return {
            "active_spaces": total_active,
            "hourly_cost_estimate_usd": round(hourly_cost, 4),
            "alert_triggered": alert,
            "timestamp": datetime.utcnow().isoformat()
        }
