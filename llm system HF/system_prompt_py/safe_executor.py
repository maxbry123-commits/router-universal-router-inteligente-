# safe_executor.py
import os
import json
from pathlib import Path

class SecurityError(Exception):
    pass

def safe_path(root: str, relative: str) -> Path:
    """
    Extraído de motor_cli.py (función path).
    Evita que la IA escriba fuera del workspace usando '../'.
    """
    if not isinstance(relative, str) or not relative.strip():
        raise SecurityError('Ruta vacía o inválida')
    
    incoming = Path(relative)
    if incoming.is_absolute():
        raise SecurityError('Ruta absoluta prohibida')
    
    target = (Path(root) / incoming).resolve()
    if not target.is_relative_to(Path(root).resolve()):
        raise SecurityError('Ruta fuera del workspace (Path Traversal)')
    
    return target

def parse_model_json(answer: str) -> dict:
    """
    Extraído de qwen_blender_adapter.py.
    Limpia los bloques de Markdown y asegura que sea un JSON válido.
    """
    stripped = answer.strip()
    if stripped.startswith("```"):
        # Quitar el bloque de código de Markdown
        stripped = stripped.split("\n", 1)[-1]
        if stripped.endswith("```"):
            stripped = stripped[:-3]
    
    try:
        parsed = json.loads(stripped)
    except json.JSONDecodeError as e:
        raise ValueError(f"El modelo no devolvió un JSON válido: {e}")

    if not isinstance(parsed, dict):
        raise ValueError("La respuesta debe ser un objeto JSON")
    return parsed
