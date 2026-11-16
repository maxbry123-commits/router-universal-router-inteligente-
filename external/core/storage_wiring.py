"""storage_wiring.py — Adaptador del núcleo (MINIMAX 4).

Reexporta el cableado de almacenamiento implementado en
external/tools/storage_wiring.py para el cableado del ciclo de vida del proxy
(verificación/creación del bucket de memoria en el startup).
"""
from external.tools.storage_wiring import StorageWiring

__all__ = ["StorageWiring"]
