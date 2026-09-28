"""Registro determinista de acciones del chat YAIWES."""
from __future__ import annotations
from typing import Any, Callable

Action = Callable[[dict[str, Any]], dict[str, Any]]
_ACTIONS: dict[str, Action] = {}
_STATE: dict[str, Any] = {"watchdog": False, "workflow": "IDLE", "tasks": {}, "pool": [],
                          "documents": [], "commands": [], "memory_queries": [], "browser": []}

COMMAND_TO_ACTION = {
    "/run": "workflow.run", "/loop": "workflow.run", "/schedule": "task.schedule",
    "/watchdog": "watchdog.start", "/rewind": "rewind", "/compact": "compact",
    "/council": "council.ask", "/archify": "archify",
}

def register(action_id: str):
    def deco(fn: Action) -> Action:
        _ACTIONS[action_id] = fn
        return fn
    return deco

def _ok(action_id: str, **data: Any) -> dict[str, Any]:
    return {"status": "PASS", "action_id": action_id, **data}

def _need(payload: dict[str, Any], *keys: str) -> None:
    missing = [k for k in keys if k not in payload]
    if missing:
        raise ValueError(f"faltan campos: {', '.join(missing)}")

@register("watchdog.start")
def watchdog_start(payload):
    _STATE["watchdog"] = True
    return _ok("watchdog.start", running=True)

@register("watchdog.stop")
def watchdog_stop(payload):
    _STATE["watchdog"] = False
    return _ok("watchdog.stop", running=False)

@register("workflow.run")
def workflow_run(payload):
    _STATE["workflow"] = "RUNNING"
    return _ok("workflow.run", workflow=payload.get("workflow", "default"))

@register("workflow.pause")
def workflow_pause(payload):
    _STATE["workflow"] = "PAUSED"
    return _ok("workflow.pause")

@register("workflow.resume")
def workflow_resume(payload):
    _STATE["workflow"] = "RUNNING"
    return _ok("workflow.resume")

@register("task.schedule")
def task_schedule(payload):
    _need(payload, "task_id")
    _STATE["tasks"][payload["task_id"]] = {"status": "SCHEDULED", **payload}
    return _ok("task.schedule", task=_STATE["tasks"][payload["task_id"]])

@register("task.cancel")
def task_cancel(payload):
    _need(payload, "task_id")
    item = _STATE["tasks"].setdefault(payload["task_id"], {"task_id": payload["task_id"]})
    item["status"] = "CANCELLED"
    return _ok("task.cancel", task=item)

@register("pool.dispatch")
def pool_dispatch(payload):
    _need(payload, "task")
    _STATE["pool"].append(payload["task"])
    return _ok("pool.dispatch", queued=len(_STATE["pool"]))

@register("document.attach")
def document_attach(payload):
    _need(payload, "document")
    _STATE["documents"].append(payload["document"])
    return _ok("document.attach", count=len(_STATE["documents"]))

@register("command.execute")
def command_execute(payload):
    _need(payload, "command")
    _STATE["commands"].append(payload["command"])
    return _ok("command.execute", command=payload["command"])

@register("memory.search")
def memory_search(payload):
    _need(payload, "query")
    _STATE["memory_queries"].append(payload["query"])
    return _ok("memory.search", results=[])

@register("browser.open")
def browser_open(payload):
    _need(payload, "url")
    _STATE["browser"].append(payload["url"])
    return _ok("browser.open", url=payload["url"])

@register("council.ask")
def council_action(payload):
    _need(payload, "pregunta")
    return _ok("council.ask", pregunta=payload["pregunta"])

@register("rewind")
def rewind_action(payload):
    return _ok("rewind", conv_id=payload.get("conv_id"), pasos=int(payload.get("pasos", 1)))

@register("compact")
def compact_action(payload):
    return _ok("compact", items=len(payload.get("historial", [])))

@register("archify")
def archify_action(payload):
    _need(payload, "texto")
    return _ok("archify", texto=payload["texto"])

def ejecutar(action_id: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    if action_id not in _ACTIONS:
        raise KeyError(f"acción desconocida: {action_id}")
    payload = {} if payload is None else payload
    if not isinstance(payload, dict):
        raise TypeError("payload debe ser dict")
    out = _ACTIONS[action_id](payload)
    if not isinstance(out, dict) or "status" not in out:
        raise ValueError("salida inválida")
    return out

def comando_a_accion(texto: str) -> tuple[str, dict[str, Any]]:
    partes = texto.strip().split(maxsplit=1)
    cmd = partes[0] if partes else ""
    if cmd not in COMMAND_TO_ACTION:
        raise KeyError(f"comando desconocido: {cmd}")
    arg = partes[1] if len(partes) > 1 else ""
    aid = COMMAND_TO_ACTION[cmd]
    if aid == "task.schedule":
        return aid, {"task_id": arg or "task"}
    if aid == "council.ask":
        return aid, {"pregunta": arg}
    if aid == "archify":
        return aid, {"texto": arg}
    return aid, {"texto": arg} if arg else {}

def acciones() -> list[str]:
    return sorted(_ACTIONS)
