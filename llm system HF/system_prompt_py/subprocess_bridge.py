# subprocess_bridge.py
import subprocess
import time
import os
from pathlib import Path

def execute_code_safely(cmd: list, project_root: str, timeout_s: int = 300) -> dict:
    """
    Extraído de qwen_blender_adapter.py.
    Ejecuta un comando en un subproceso, captura logs y verifica el estado.
    """
    started = time.monotonic()
    try:
        # Ejecución del subproceso con timeout (regla estricta)
        completed = subprocess.run(
            cmd,
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=timeout_s,
            check=False
        )
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": "TIMEOUT", "elapsed_s": timeout_s}

    logs = completed.stdout + "\n" + completed.stderr
    
    return {
        "ok": completed.returncode == 0,
        "returncode": completed.returncode,
        "elapsed_s": round(time.monotonic() - started, 2),
        "logs": logs[-3000:], # Solo los últimos 3000 caracteres
        "artifacts": [] # Se llenaría si el script creó archivos
    }
