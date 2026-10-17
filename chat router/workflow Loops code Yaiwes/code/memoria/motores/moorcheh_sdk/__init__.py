'''Sustituto LOCAL minimo de moorcheh_sdk para memanto (sin nube): solo los nombres que memanto importa.
Los clientes reales se reemplazan por memanto/cliente_local.py (SQLite + busqueda por palabras).'''
from memanto.cliente_local import LocalClient as MoorchehClient  # noqa: F401
from memanto.cliente_local import LocalClient as AsyncMoorchehClient  # noqa: F401
