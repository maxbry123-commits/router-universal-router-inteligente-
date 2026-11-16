"""
router_llm_hf — Control Plane del sistema
Regla: nunca computa, solo controla
"""
from .queue_manager import QueueManager, Priority, Task
from .watchdog import Watchdog
from .recall_engine import RecallEngine
from .output_contract import OutputContract
from .escalation_guard import EscalationGuard
from .mode_router import route

__all__ = [
    "QueueManager",
    "Priority",
    "Task",
    "Watchdog",
    "RecallEngine",
    "OutputContract",
    "EscalationGuard",
    "route",
]

__version__ = "1.0.0"
