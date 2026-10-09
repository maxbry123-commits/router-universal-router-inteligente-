"""Puente de compatibilidad para XRAY-V2.

El YAML queda como especificacion verificable, pero YA NO se concatena al prompt.
La captura/bind del nodo se ejecuta nativamente en runtime_xray.py.
"""
from .runtime_xray import bind_node

CLAVES = ('schema: yaiwes.node-executor/xray-v2', '=== BEGIN_INPUT_BLOCK ===', '<user_query mode="verbatim">')


def faltan(plantilla):
    return [c for c in CLAVES if c not in plantilla]


def bloque_entrada(nodo, task_id, texto, paso, rutas):
    # CAPTURE_AS_DATA -> FREEZE_VERBATIM -> BIND_AS_TASK en Python.
    # El input se conserva completo; no se convierte en plantilla de texto.
    bind_node(nodo, task_id, texto, paso, rutas)
    return ''


def armar(plantilla, mejoras, bloque):
    # Compatibilidad con FichaOS: el DSL/MEJORAS no consume contexto del modelo.
    # Su control vive en runtime_xray.py y en las compuertas nativas de FichaOS.
    return ''
