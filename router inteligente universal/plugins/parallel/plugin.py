"""parallel: N llamadas a plugins en paralelo via host.call (max 8 en vuelo, timeout por llamada). Sin logica nueva grande.

Acciones: status, run. payload: {"calls": [{"plugin": id, "action": a, "payload": {...}, "timeout_s": n}], "timeout_s": n}.
Un grupo es simplemente una lista de calls. No se puede llamar a si mismo (evita recursion).
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from typing import Any

MAX_IN_FLIGHT = 8
MAX_CALLS = 32
SELF_ID = "parallel"


def _one(host: Any, call: Any, default_timeout: float | None) -> dict[str, Any]:
    if not isinstance(call, dict) or not isinstance(call.get("plugin"), str) or not isinstance(call.get("action"), str):
        return {"status": "degraded", "reason": "call invalido: requiere plugin y action (texto)"}
    if call["plugin"] == SELF_ID:
        return {"status": "degraded", "reason": "parallel no puede llamarse a si mismo"}
    t = call.get("timeout_s", default_timeout)
    return host.call(call["plugin"], call["action"], call.get("payload"), t if isinstance(t, (int, float)) else None)


def handle(action: str, payload: dict[str, Any] | None) -> dict[str, Any]:
    payload = payload or {}
    if action == "status":
        return {"status": "ok", "max_in_flight": MAX_IN_FLIGHT, "max_calls": MAX_CALLS}
    if action != "run":
        return {"status": "degraded", "reason": "accion desconocida"}
    calls = payload.get("calls")
    if not isinstance(calls, list) or not calls:
        return {"status": "degraded", "reason": "payload.calls debe ser una lista no vacia"}
    if len(calls) > MAX_CALLS:
        return {"status": "degraded", "reason": f"maximo {MAX_CALLS} calls"}
    from integration.plugin_host.host import get_host

    host = get_host()
    t = payload.get("timeout_s")
    t = t if isinstance(t, (int, float)) else None
    with ThreadPoolExecutor(max_workers=min(MAX_IN_FLIGHT, len(calls))) as pool:
        results = list(pool.map(lambda c: _one(host, c, t), calls))
    ok = sum(1 for r in results if r.get("status") == "ok")
    return {"status": "ok" if ok == len(results) else "degraded", "ok": ok, "total": len(results), "results": results}
