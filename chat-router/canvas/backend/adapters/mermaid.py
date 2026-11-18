"""Adaptador Mermaid (componente autorizado: mermaid-js/mermaid).

Fichero: adapters/mermaid.py  (1 componente = 1 fichero, FAIL_CLOSED)
Binario esperado: `mmdc` (mermaid-cli). Sin API key, sin secretos.

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

TOOL_ID = "mermaid"
TOOL_NAME = "Mermaid"
SOURCE_REPO = "mermaid-js/mermaid"
CLI = "mmdc"
PING_COMMAND = "mmdc --version"
TIMEOUT = 60


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
    """Normaliza el payload a código mermaid (str) o None."""
    if payload is None:
        return None
    if isinstance(payload, str):
        return payload
    if isinstance(payload, dict):
        for key in ("code", "mermaid", "source", "text"):
            value = payload.get(key)
            if isinstance(value, str) and value.strip():
                return value
    return None


def ping() -> Dict[str, Any]:
    """Comprueba si `mmdc` está disponible. NUNCA lanza."""
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
    """Renderiza código mermaid a SVG.

    payload: str con el código, o dict {"code": str, "theme": str, "background": str}.
    Comando: `mmdc -i in.mmd -o out.svg -b transparent`.
    Devuelve SIEMPRE dict: {"ok","tool","svg","path","error"}.
    """
    code = _extract_code(payload)
    if not code:
        return {
            "ok": False,
            "tool": TOOL_ID,
            "error": "payload invalido: se esperaba codigo mermaid (str) o dict con clave 'code'",
            "svg": None,
            "path": None,
        }

    options = payload if isinstance(payload, dict) else {}
    theme = options.get("theme")
    background = options.get("background", "transparent")

    exe = shutil.which(CLI)
    if not exe:
        return {
            "ok": False,
            "tool": TOOL_ID,
            "error": f"CLI '{CLI}' no encontrado en PATH (OMITIDO) - ping: {PING_COMMAND}",
            "svg": None,
            "path": None,
        }

    with tempfile.TemporaryDirectory(prefix="mermaid_") as tmp:
        tmp_dir = Path(tmp)
        in_file = tmp_dir / "in.mmd"
        out_file = tmp_dir / "out.svg"
        in_file.write_text(code, encoding="utf-8")

        cmd = [exe, "-i", str(in_file), "-o", str(out_file), "-b", str(background)]
        if isinstance(theme, str) and theme.strip():
            cmd += ["-t", theme.strip()]

        res = _run(cmd, timeout=TIMEOUT)
        if not res["ok"]:
            return {
                "ok": False,
                "tool": TOOL_ID,
                "error": f"mmdc fallo (rc={res['returncode']}): {res['stderr'][:500]}",
                "command": " ".join(cmd),
                "svg": None,
                "path": None,
            }
        if not out_file.exists():
            return {
                "ok": False,
                "tool": TOOL_ID,
                "error": f"mmdc termino con rc=0 pero no genero '{out_file.name}'",
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
