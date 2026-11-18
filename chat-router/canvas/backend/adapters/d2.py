"""Adaptador D2 / Terrastruct (componente autorizado: terrastruct/d2).

Fichero: adapters/d2.py  (1 componente = 1 fichero, FAIL_CLOSED)
Binario esperado: `d2`. Sin API key, sin secretos.

Contrato:
  ping()   -> {"tool", "status": "OK"|"OMITIDO", "reason"/"error", "version", ...}
  render() -> dict SIEMPRE (nunca lanza, nunca `check=True`)

Todo subprocess se ejecuta con `timeout` + `capture_output`.
"""

from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Dict, Optional

TOOL_ID = "d2"
TOOL_NAME = "D2/Terrastruct"
SOURCE_REPO = "terrastruct/d2"
CLI = "d2"
PING_COMMAND = "d2 --version"
TIMEOUT = 60
THEME = "200"


def _run(cmd: list, timeout: int = TIMEOUT, cwd: Optional[str] = None) -> Dict[str, Any]:
    """Ejecuta un comando sin lanzar excepciones. Nunca usa check=True."""
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=cwd,
            check=False,
        )
    except FileNotFoundError as exc:
        return {
            "ok": False,
            "returncode": 127,
            "stdout": "",
            "stderr": f"FileNotFoundError: {exc}",
            "missing": True,
        }
    except subprocess.TimeoutExpired as exc:
        return {
            "ok": False,
            "returncode": 124,
            "stdout": (exc.stdout or "") if isinstance(exc.stdout, str) else "",
            "stderr": f"TimeoutExpired: exceeded {timeout}s",
            "timeout": True,
        }
    except Exception as exc:  # pragma: no cover - defensivo
        return {
            "ok": False,
            "returncode": 1,
            "stdout": "",
            "stderr": f"{type(exc).__name__}: {exc}",
        }
    return {
        "ok": proc.returncode == 0,
        "returncode": proc.returncode,
        "stdout": (proc.stdout or "").strip(),
        "stderr": (proc.stderr or "").strip(),
        "missing": False,
    }


def _extract_code(payload: Any) -> Optional[str]:
    """Normaliza el payload a codigo d2 (str) o None."""
    if payload is None:
        return None
    if isinstance(payload, str):
        return payload
    if isinstance(payload, dict):
        for key in ("code", "d2", "source", "text"):
            value = payload.get(key)
            if isinstance(value, str) and value.strip():
                return value
    return None


def ping() -> Dict[str, Any]:
    """Comprueba si `d2` esta disponible. NUNCA lanza."""
    try:
        exe = shutil.which(CLI)
        if not exe:
            return {
                "tool": TOOL_ID,
                "status": "OMITIDO",
                "reason": f"CLI '{CLI}' no encontrado en PATH",
                "ping_command": PING_COMMAND,
                "version": None,
                "source_repo": SOURCE_REPO,
            }
        res = _run([exe, "--version"], timeout=20)
        if not res["ok"]:
            return {
                "tool": TOOL_ID,
                "status": "OMITIDO",
                "reason": f"'{CLI} --version' devolvio rc={res['returncode']}: {res['stderr'][:300]}",
                "ping_command": PING_COMMAND,
                "version": None,
                "source_repo": SOURCE_REPO,
            }
        raw = res["stdout"] or res["stderr"]
        version = raw.splitlines()[-1].strip() if raw else None
        return {
            "tool": TOOL_ID,
            "status": "OK",
            "reason": None,
            "version": version,
            "ping_command": PING_COMMAND,
            "executable": exe,
            "source_repo": SOURCE_REPO,
        }
    except Exception as exc:  # pragma: no cover - defensivo
        return {
            "tool": TOOL_ID,
            "status": "OMITIDO",
            "reason": f"{type(exc).__name__}: {exc}",
            "ping_command": PING_COMMAND,
            "version": None,
            "source_repo": SOURCE_REPO,
        }


def render(payload: Any) -> Dict[str, Any]:
    """Renderiza codigo d2 a SVG.

    payload: str con el codigo, o dict {"code": str, "theme": str}.
    Comando: `d2 --theme 200 in.d2 out.svg`.
    Devuelve SIEMPRE dict: {"ok","tool","svg","path","error"}.
    """
    code = _extract_code(payload)
    if not code:
        return {
            "ok": False,
            "tool": TOOL_ID,
            "error": "payload invalido: se esperaba codigo d2 (str) o dict con clave 'code'",
            "svg": None,
            "path": None,
        }

    options = payload if isinstance(payload, dict) else {}
    theme = options.get("theme", THEME)

    exe = shutil.which(CLI)
    if not exe:
        return {
            "ok": False,
            "tool": TOOL_ID,
            "error": f"CLI '{CLI}' no encontrado en PATH (OMITIDO) - ping: {PING_COMMAND}",
            "svg": None,
            "path": None,
        }

    with tempfile.TemporaryDirectory(prefix="d2_") as tmp:
        tmp_dir = Path(tmp)
        in_file = tmp_dir / "in.d2"
        out_file = tmp_dir / "out.svg"
        in_file.write_text(code, encoding="utf-8")

        cmd = [exe, "--theme", str(theme), str(in_file), str(out_file)]
        res = _run(cmd, timeout=TIMEOUT)
        if not res["ok"]:
            return {
                "ok": False,
                "tool": TOOL_ID,
                "error": f"d2 fallo (rc={res['returncode']}): {res['stderr'][:500]}",
                "command": " ".join(cmd),
                "svg": None,
                "path": None,
            }
        if not out_file.exists():
            return {
                "ok": False,
                "tool": TOOL_ID,
                "error": f"d2 termino con rc=0 pero no genero '{out_file.name}'",
                "command": " ".join(cmd),
                "svg": None,
                "path": None,
            }
        svg = out_file.read_text(encoding="utf-8", errors="replace")
        return {
            "ok": True,
            "tool": TOOL_ID,
            "error": None,
            "svg": svg,
            "path": str(out_file),
            "command": " ".join(cmd),
            "bytes": len(svg.encode("utf-8")),
        }
