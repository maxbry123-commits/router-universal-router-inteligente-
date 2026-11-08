import argparse
import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path

SYSTEM_PROMPT = "Eres PLANIFICADOR DECLARATIVO DE ESCENAS. Tu unica salida es JSON puro."

ALLOWED = {"new_scene", "set_world", "add_material", "add_mesh", "assign_material", "add_light", "add_camera", "track_to", "set_render", "render", "save"}

def parse_model_json(answer: str) -> dict:
    stripped = answer.strip()
    if stripped.startswith("```"):
        stripped = stripped.split("\n", 1)[-1]
    if stripped.endswith("```"):
        stripped = stripped[:-3]
    return json.loads(stripped)

def validate_scene(doc: dict) -> dict:
    if set(doc) - {"meta", "ops"}:
        raise ValueError("Campos desconocidos")
    ops = doc.get("ops")
    if not isinstance(ops, list):
        raise ValueError("ops debe ser lista")
    for idx, item in enumerate(ops):
        if item.get("op") not in ALLOWED:
            raise ValueError(f"Operacion prohibida en {idx}")
    return doc
