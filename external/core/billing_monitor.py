"""billing_monitor.py — Adaptador del núcleo (MINIMAX 4).

Reexporta el monitor de facturación implementado en
external/tools/billing_monitor.py para el cableado del ciclo de vida del proxy
(expone GET /billing/status).
"""
from external.tools.billing_monitor import BillingMonitor

__all__ = ["BillingMonitor"]
