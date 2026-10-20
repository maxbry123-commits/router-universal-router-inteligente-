"""Capas L01-L06 del Wordflow LOOP. `execute` es el Executor que recibe LayerRunner."""
from __future__ import annotations
from ..contracts import LayerResult, NodeContract, Status
from . import (layer_01_research, layer_02_xray_documents, layer_03_xray_code,
               layer_04_copy_move, layer_05_download_extract, layer_06_source_evolution)

LAYERS = {m.LAYER: m for m in (layer_01_research, layer_02_xray_documents, layer_03_xray_code,
                               layer_04_copy_move, layer_05_download_extract, layer_06_source_evolution)}


def execute(node: NodeContract, ctx: dict) -> LayerResult:
    mod = LAYERS.get(node.layer)
    if mod is None:
        return LayerResult(node_id=node.node_id, layer=node.layer, status=Status.INCONCLUSIVE,
                           gaps=[f"UNKNOWN_LAYER:{node.layer}"])
    return mod.run(node, ctx)


__all__ = ["execute", "LAYERS"]
