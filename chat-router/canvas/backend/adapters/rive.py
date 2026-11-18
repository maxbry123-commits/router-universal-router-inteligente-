"""Adaptador Rive (componente autorizado: rive-app/rive).

Fichero: adapters/rive.py  (1 componente = 1 fichero, FAIL_CLOSED)
CLI esperado: `rive`.
  - ping   -> `rive --version`
  - render -> `rive render <riv_path> --format mp4 [--state-machine X]`
Sin API key, sin secretos.

Contrato: ping()/render() devuelven SIEMPRE dict, nunca lanzan.
"""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional

TOOL_ID = "rive"
TOOL_NAME = "Rive"
SOURCE_REPO = "rive-app/rive"
CLI = "rive"
PING_COMMAND = "rive --version"
TIMEOUT = 30
RENDER_TIMEOUT = 300


def _run(cmd: List[str], timeout: int = TIMEOUT, cwd: Optional[str] = None) -> Dict[str, Any]:
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


def ping() -> Dict[str, Any]:
    """Comprueba si `rive` esta disponible. NUNCA lanza."""
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
    """Renderiza un archivo .riv a video mp4.

    payload: dict {"riv_path": str, "state_machine": str, "out": str}
    Comando: `rive render <riv_path> --format mp4 [--state-machine X]`
    Devuelve SIEMPRE dict: {"ok","tool","video_path","error"}.
    """
    try:
        if not isinstance(payload, dict):
            return {
                "ok": False,
                "tool": TOOL_ID,
                "error": "payload invalido: se esperaba dict con clave 'riv_path'",
                "video_path": None,
            }
        riv_path = payload.get("riv_path") or payload.get("path")
        if not isinstance(riv_path, str) or not riv_path.strip():
            return {
                "ok": False,
                "tool": TOOL_ID,
                "error": "payload invalido: falta 'riv_path'",
                "video_path": None,
            }
        if not Path(riv_path).exists():
            return {
                "ok": False,
                "tool": TOOL_ID,
                "error": f"riv_path no existe: {riv_path}",
                "video_path": None,
            }
        state_machine = payload.get("state_machine")
        out_path = payload.get("out")

        exe = shutil.which(CLI)
        if not exe:
            return {
                "ok": False,
                "tool": TOOL_ID,
                "error": f"CLI '{CLI}' no encontrado en PATH (OMITIDO) - ping: {PING_COMMAND}",
                "video_path": None,
            }

        cmd = [exe, "render", riv_path, "--format", str(payload.get("format", "mp4"))]
        if isinstance(state_machine, str) and state_machine.strip():
            cmd += ["--state-machine", state_machine.strip()]
        if isinstance(out_path, str) and out_path.strip():
            cmd += ["--output", out_path]

        res = _run(cmd, timeout=RENDER_TIMEOUT, cwd=os.path.dirname(os.path.abspath(riv_path)))
        if not res["ok"]:
            return {
                "ok": False,
                "tool": TOOL_ID,
                "error": f"rive render fallo (rc={res['returncode']}): {res['stderr'][:500]}",
                "command": " ".join(cmd),
                "video_path": None,
            }
        produced = out_path if isinstance(out_path, str) and out_path else None
        if produced and Path(produced).exists():
            return {
                "ok": True,
                "tool": TOOL_ID,
                "error": None,
                "video_path": str(Path(produced).resolve()),
                "command": " ".join(cmd),
                "bytes": Path(produced).stat().st_size,
            }
        # Sin --output el CLI decide el nombre: se busca junto al .riv
        stem = Path(riv_path).with_suffix("")
        candidates = [
            Path(f"{stem}.mp4"),
            Path(riv_path).parent / f"{stem.name}.mp4",
        ]
        for candidate in candidates:
            if candidate.exists():
                return {
                    "ok": True,
                    "tool": TOOL_ID,
                    "error": None,
                    "video_path": str(candidate.resolve()),
                    "command": " ".join(cmd),
                    "bytes": candidate.stat().st_size,
                }
        return {
            "ok": False,
            "tool": TOOL_ID,
            "error": f"rive termino con rc=0 pero no se localizo el mp4 generado: {res['stdout'][:300]}",
            "command": " ".join(cmd),
            "video_path": None,
        }
    except Exception as exc:  # pragma: no cover - defensivo
        return {
            "ok": False,
            "tool": TOOL_ID,
            "error": f"{type(exc).__name__}: {exc}",
            "video_path": None,
        }
