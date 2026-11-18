"""
router_llm_hf — Control Plane del sistema
Regla: nunca computa, solo controla
"""
import os as _os
import sys as _sys

# FIX (MINIMAX 2E): los agentes internos (chat_a_architect, chat_b_implementer,
# chat_ab_orchestrator) importan modulos del nucleo legado que viven en
# "ROUTER MVP v1/system_prompt_py" (loc_limits, semantic_checkpoint,
# generic_model_adapter, tool_call_validator, ...). Sin ese path en sys.path,
# `import router_llm_hf.chat_a_architect` reventaba con ModuleNotFoundError y
# los agentes NO eran importables desde ningun sitio (el registro de agentes
# los declaraba, pero no habia forma de cargarlos).
_LEGACY_CORE = _os.path.abspath(
    _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..", "ROUTER MVP v1", "system_prompt_py")
)
if _os.path.isdir(_LEGACY_CORE) and _LEGACY_CORE not in _sys.path:
    _sys.path.append(_LEGACY_CORE)

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
