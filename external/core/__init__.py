# external/core/__init__.py — Nucleo NCT/APEX (version extendida R4)
# Paquetes: classifier, input_validator, output_contract, escalation_guard,
# queue_manager, recall_engine, mode_router, hitl_integration
#
# IMPORTS PUBLICOS:
#   from external.core import clasificar, validar, OutputContract
#   from external.core import EscalationGuard, QueueManager, RecallEngine
#   from external.core import route as mode_route, HITL

__all__ = [
    "clasificar", "validar_formato",
    "validar",
    "OutputContract",
    "EscalationGuard",
    "QueueManager", "Priority", "Task",
    "RecallEngine",
    "route", "select_model_for_mode",
    "HITL",
]
