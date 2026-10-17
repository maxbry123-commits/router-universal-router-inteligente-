'''Pool de herramientas para agentes (PydanticAI FunctionToolset) con las mismas funciones deterministas del orquestador.
El LLM (el 5%) es el agente que consume el pool; estas funciones no usan LLM.'''
from __future__ import annotations

from .runtime import Orquestador


def memoria_estado() -> dict:
    '''Estado CONNECTED o GAP de cada motor.'''
    return {'motores': Orquestador().estado()}


def memoria_guardar(scope: str, key: str, data: dict) -> dict:
    '''Guarda data en los motores conectados que permiten escribir.'''
    return Orquestador().guardar(scope, key, data)


def memoria_cargar(scope: str, key: str) -> dict:
    '''Lee (scope, key) del primer motor que lo tenga.'''
    return Orquestador().cargar(scope, key)


def memoria_buscar(scope: str, query: str, k: int = 10) -> dict:
    '''Busca en todos los motores y fusiona el resultado sin repetidos.'''
    return Orquestador().buscar(scope, query, k)


FUNCIONES = [memoria_estado, memoria_guardar, memoria_cargar, memoria_buscar]


def crear_toolset():
    from pydantic_ai.toolsets import FunctionToolset
    return FunctionToolset(FUNCIONES)
