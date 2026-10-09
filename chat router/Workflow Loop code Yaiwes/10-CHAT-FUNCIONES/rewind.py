"""Checkpoints de conversación en memoria."""
from __future__ import annotations
from copy import deepcopy
_STORE:dict[str,list[object]]={}

def guardar(conv_id:str,estado:object)->int:
    if not conv_id: raise ValueError("conv_id requerido")
    _STORE.setdefault(conv_id,[]).append(deepcopy(estado)); return len(_STORE[conv_id])

def volver(conv_id:str,pasos:int=1)->object:
    if pasos<1: raise ValueError("pasos >= 1")
    items=_STORE.get(conv_id,[])
    if not items: raise KeyError(conv_id)
    idx=max(0,len(items)-1-pasos)
    value=deepcopy(items[idx]); del items[idx+1:]; return value
