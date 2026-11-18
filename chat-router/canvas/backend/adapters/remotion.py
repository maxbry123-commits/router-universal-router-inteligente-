"""Adaptador Remotion (componente autorizado: remotion-dev/remotion).

Fichero: adapters/remotion.py  (1 componente = 1 fichero, FAIL_CLOSED)
CLI esperado: `remotion` (local) o `npx remotion`.

REGLA DURA: NO se instala nada. Por eso el ping usa `npx --no-install`, que
falla de inmediato si el paquete no esta presente en node_modules, en lugar de
descargarlo (npm install / descarga de binarios esta PROHIBIDO).

  - ping   -> `npx --no-install remotion --version` (o binario local)
  - render -> `npx --no-install remotion render <composition_id> <out.mp4> --props=<json>`
Sin API key, sin secretos.

Contrato: ping()/render() devuelven SIEMPRE dict, nunca lanzan.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional

TOOL_ID = "remotion"
TOOL_NAME = "Remotion"
SOURCE_REPO = "remotion-dev/remotion"
CLI = "remotion"
PING_COMMAND = "npx --no-install remotion --version"
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


def _local_binary(project_dir: Optional[str] = None) -> Optional[str]:
    """Busca el binario local de remotion (sin instalar nada)."""
    direct = shutil.which(CLI)
    if direct:
        return direct
    roots: List[str] = []
    if project_dir:
        roots.append(project_dir)
    roots.append(os.getcwd())
    for root in roots:
        candidate = Path(root) / "node_modules" / ".bin" / CLI
        if candidate.exists():
            return str(candidate)
    return None


def _version_cmd(project_dir: Optional[str] = None) -> List[str]:
    local = _local_binary(project_dir)
    if local:
        return [local, "--version"]
    # --no-install: NO descarga ni instala nada.
    return ["npx", "--no-install", CLI, "--version"]


def ping() -> Dict[str, Any]:
    """Comprueba si Remotion esta disponible sin instalar nada. NUNCA lanza."""
    try:
        cmd = _version_cmd()
        res = _run(cmd, timeout=TIMEOUT)
        if not res["ok"]:
            return {
                "tool": TOOL_ID,
                "status": "OMITIDO",
                "reason": (
                    f"remotion no disponible (rc={res['returncode']}): "
                    f"{(res['stderr'] or res['stdout'])[:300]}"
                ),
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
            "command": " ".join(cmd),
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
    """Renderiza una composicion Remotion a mp4.

    payload: dict {"composition": str, "props": dict, "project_dir": str, "out": str}
    Comando: `npx --no-install remotion render <composition_id> <out.mp4> --props=<json>`
    Devuelve SIEMPRE dict: {"ok","tool","video_path","video_url","error"}.
    """
    try:
        if not isinstance(payload, dict):
            return {
                "ok": False,
                "tool": TOOL_ID,
                "error": "payload invalido: se esperaba dict con clave 'composition'",
                "video_path": None,
                "video_url": None,
            }
        composition = payload.get("composition") or payload.get("composition_id")
        if not isinstance(composition, str) or not composition.strip():
            return {
                "ok": False,
                "tool": TOOL_ID,
                "error": "payload invalido: falta 'composition' (id de composicion)",
                "video_path": None,
                "video_url": None,
            }
        project_dir = payload.get("project_dir")
        if project_dir and not os.path.isdir(str(project_dir)):
            return {
                "ok": False,
                "tool": TOOL_ID,
                "error": f"project_dir inexistente: {project_dir}",
                "video_path": None,
                "video_url": None,
            }
        props = payload.get("props") or {}
        if not isinstance(props, dict):
            props = {"value": props}

        workdir = str(project_dir) if project_dir else os.getcwd()
        out_path = payload.get("out")
        tmp_dir = None
        if out_path:
            out_file = Path(str(out_path))
        else:
            tmp_dir = tempfile.TemporaryDirectory(prefix="remotion_")
            out_file = Path(tmp_dir.name) / "out.mp4"

        try:
            cmd = _version_cmd(str(project_dir) if project_dir else None)
            cmd = cmd[:-1]  # quita '--version'
            cmd += ["render", composition, str(out_file), f"--props={json.dumps(props)}"]
            res = _run(cmd, timeout=RENDER_TIMEOUT, cwd=workdir)
        finally:
            if tmp_dir is not None:
                # el fichero temporal se conserva solo si el render fue correcto
                pass

        if not res["ok"]:
            return {
                "ok": False,
                "tool": TOOL_ID,
                "error": f"remotion render fallo (rc={res['returncode']}): {(res['stderr'] or res['stdout'])[:500]}",
                "command": " ".join(cmd),
                "video_path": None,
                "video_url": None,
            }
        if not out_file.exists():
            return {
                "ok": False,
                "tool": TOOL_ID,
                "error": f"remotion termino con rc=0 pero no genero '{out_file}'",
                "command": " ".join(cmd),
                "video_path": None,
                "video_url": None,
            }
        return {
            "ok": True,
            "tool": TOOL_ID,
            "error": None,
            "video_path": str(out_file),
            "video_url": f"file://{out_file}",
            "command": " ".join(cmd),
            "bytes": out_file.stat().st_size,
        }
    except Exception as exc:  # pragma: no cover - defensivo
        return {
            "ok": False,
            "tool": TOOL_ID,
            "error": f"{type(exc).__name__}: {exc}",
            "video_path": None,
            "video_url": None,
        }
