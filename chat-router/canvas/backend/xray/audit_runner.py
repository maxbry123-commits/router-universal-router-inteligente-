"""RUNNER DEL AUDITOR X-RAY · 1 funcion = 1 fichero · yaiwes.node/v2

Por que existe: la API (POST /xray/audit) y el router MCP (tool xray_audit)
deben ejecutar EXACTAMENTE el mismo motor determinista. Antes cada uno tinha su
propia copia del comando -> cualquier divergencia entre ambos seria un gap
silencioso. Aqui vive el comando una sola vez.

Fichero: backend/xray/audit_runner.py
API:  run_audit(root, out, timeout=600) -> dict  (nunca lanza: devuelve el fallo real)
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict

AUDITOR_SCRIPT = Path(__file__).resolve().parent / "xray_audit.py"


def _tail(text: str, limit: int = 2000) -> str:
    text = text or ""
    return text[-limit:] if len(text) > limit else text


def run_audit(root: str, out: str, timeout: int = 600, env: Dict[str, str] = None) -> Dict[str, Any]:
    """Ejecuta el auditor X-Ray sobre `root` y escribe los artefactos en `out`.

    Devuelve SIEMPRE un dict con el estado real:
      {ok, exit_code, root, out, stdout_tail, stderr_tail, validation, fingerprint}

    FAIL_CLOSED: si el auditor no existe, falla o expira, `ok` es False y el
    motivo real viaja en el detalle. Nunca se inventa un PASS.
    """
    root_abs = os.path.abspath(root or os.getcwd())
    out_abs = os.path.abspath(out or os.path.join(root_abs, "xray"))

    if not AUDITOR_SCRIPT.is_file():
        return {
            "ok": False,
            "exit_code": -1,
            "root": root_abs,
            "out": out_abs,
            "stdout_tail": "",
            "stderr_tail": "xray_audit.py no encontrado: %s" % AUDITOR_SCRIPT,
            "validation": None,
            "fingerprint": None,
        }

    try:
        proc = subprocess.run(
            [sys.executable, str(AUDITOR_SCRIPT), "--root", root_abs, "--out", out_abs],
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=str(AUDITOR_SCRIPT.parent),
            env=env or os.environ,
        )
    except subprocess.TimeoutExpired:
        return {
            "ok": False,
            "exit_code": -2,
            "root": root_abs,
            "out": out_abs,
            "stdout_tail": "",
            "stderr_tail": "el auditor excedio el tiempo maximo (%d s)" % timeout,
            "validation": None,
            "fingerprint": None,
        }
    except OSError as exc:
        return {
            "ok": False,
            "exit_code": -3,
            "root": root_abs,
            "out": out_abs,
            "stdout_tail": "",
            "stderr_tail": "%s: %s" % (type(exc).__name__, exc),
            "validation": None,
            "fingerprint": None,
        }

    validation_path = Path(out_abs) / "raw" / "validation.json"
    fingerprint_path = Path(out_abs) / "FINGERPRINT.json"
    validation = None
    fingerprint = None
    try:
        if validation_path.is_file():
            validation = json.loads(validation_path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        validation = None
    try:
        if fingerprint_path.is_file():
            fingerprint = json.loads(fingerprint_path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        fingerprint = None

    return {
        "ok": proc.returncode == 0,
        "exit_code": proc.returncode,
        "root": root_abs,
        "out": out_abs,
        "stdout_tail": _tail(proc.stdout),
        "stderr_tail": _tail(proc.stderr),
        "validation": validation,
        "fingerprint": fingerprint,
    }
