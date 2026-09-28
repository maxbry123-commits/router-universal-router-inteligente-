"""Registro determinista botón/comando -> acción."""
from __future__ import annotations
from typing import Any, Callable

Action=Callable[[dict[str,Any]],dict[str,Any]]
_REGISTRY:dict[str,Action]={}
COMMANDS={"/run":"workflow.run","/loop":"workflow.run","/schedule":"task.schedule","/watchdog":"watchdog.start","/rewind":"rewind","/compact":"compact","/council":"council.ask","/archify":"archify"}
ACTIONS=("watchdog.start","watchdog.stop","workflow.run","workflow.pause","workflow.resume","task.schedule","task.cancel","pool.dispatch","document.attach","command.execute","memory.search","browser.open","council.ask","rewind","compact","archify")

def _default(action_id:str)->Action:
    def run(payload:dict[str,Any])->dict[str,Any]: return {"status":"PASS","action_id":action_id,"payload":payload}
    return run
for _id in ACTIONS: _REGISTRY[_id]=_default(_id)

def registrar(action_id:str, fn:Action)->None:
    if not action_id or not callable(fn): raise ValueError("acción inválida")
    _REGISTRY[action_id]=fn

def ejecutar(action_id:str,payload:dict[str,Any]|None=None)->dict[str,Any]:
    if action_id not in _REGISTRY: raise KeyError(action_id)
    if payload is not None and not isinstance(payload,dict): raise TypeError("payload debe ser JSON object")
    return _REGISTRY[action_id](payload or {})

def traducir_comando(texto:str)->str:
    cmd=texto.strip().split(maxsplit=1)[0]
    if cmd not in COMMANDS: raise KeyError(cmd)
    return COMMANDS[cmd]
