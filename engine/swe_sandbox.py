"""swe_sandbox.py — Ejecucion acotada y determinista para el agente SWE (P5).
Sin shell, sin red, allowlist de binarios, timeout y salida truncada.
Fail-closed: binario fuera de allowlist -> degraded, nunca se ejecuta.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
ALLOWED_BINS = {"git", "python", "python3", "grep", "pytest"}
MAX_OUTPUT = 8000
DEFAULT_TIMEOUT = 60
FORBIDDEN_TOKENS = (
    "rm -rf", "sudo", "curl", "wget", "nc ", "ssh ", "chmod 777",
    "&&", "||", ";", "|", "`", "$(", ">", "<",
)


def _degraded(reason: str) -> dict[str, Any]:
    return {"status": "degraded", "reason": reason}


def _env_limpio() -> dict[str, str]:
    """Entorno minimo: sin credenciales, sin proxy, sin red heredada."""
    base = {
        "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
        "HOME": str(ROOT),
        "LANG": "C.UTF-8",
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONUNBUFFERED": "1",
        "GIT_PAGER": "cat",
        "GIT_TERMINAL_PROMPT": "0",
        "http_proxy": "", "https_proxy": "", "HTTP_PROXY": "", "HTTPS_PROXY": "",
        "no_proxy": "*", "NO_PROXY": "*",
    }
    return base


def validar_argv(argv: list[str]) -> str | None:
    """Devuelve motivo de rechazo o None si es seguro."""
    if not argv or not isinstance(argv, (list, tuple)):
        return "argv vacio"
    bin_name = Path(str(argv[0])).name
    if bin_name not in ALLOWED_BINS:
        return f"binario fuera de allowlist: {bin_name}"
    joined = " ".join(str(a) for a in argv)
    for tok in FORBIDDEN_TOKENS:
        if tok in joined:
            return f"token prohibido en argv: {tok!r}"
    return None


def run(argv: list[str], cwd: str | None = None,
        timeout: int = DEFAULT_TIMEOUT, stdin: str | None = None) -> dict[str, Any]:
    """Ejecuta argv sin shell. Devuelve {status, rc, stdout, stderr, ms, argv}."""
    motivo = validar_argv(argv)
    if motivo:
        return _degraded(motivo)
    exe = shutil.which(Path(str(argv[0])).name)
    if not exe:
        return _degraded(f"binario no encontrado en PATH: {argv[0]}")
    workdir = Path(cwd) if cwd else ROOT
    if not workdir.is_dir():
        return _degraded("cwd inexistente")
    argv_real = [exe] + [str(a) for a in argv[1:]]
    t0 = time.monotonic()
    try:
        proc = subprocess.run(
            argv_real, cwd=str(workdir), env=_env_limpio(),
            input=stdin, capture_output=True, text=True,
            timeout=max(1, min(int(timeout), 300)), shell=False, check=False,
        )
        ms = int((time.monotonic() - t0) * 1000)
        return {
            "status": "ok" if proc.returncode == 0 else "nonzero",
            "rc": proc.returncode,
            "stdout": (proc.stdout or "")[:MAX_OUTPUT],
            "stderr": (proc.stderr or "")[:MAX_OUTPUT],
            "truncado": len(proc.stdout or "") > MAX_OUTPUT,
            "ms": ms, "argv": [str(a) for a in argv],
        }
    except subprocess.TimeoutExpired:
        return {"status": "timeout", "rc": None, "stdout": "", "stderr": "",
                "ms": int((time.monotonic() - t0) * 1000),
                "argv": [str(a) for a in argv], "reason": f"timeout {timeout}s"}
    except Exception as exc:  # noqa: BLE001
        return _degraded("subprocess: " + type(exc).__name__)


def pytest_target(target: str, timeout: int = 120) -> dict[str, Any]:
    """Corre pytest sobre un archivo/nodo concreto, sin cobertura ni plugins raros."""
    return run(["python", "-m", "pytest", target, "-x", "-q",
                "--no-header", "-p", "no:cacheprovider"], timeout=timeout)


def grep_repo(patron: str, glob_ext: str = "*.py",
              max_lineas: int = 40) -> dict[str, Any]:
    """Busqueda acotada en el repo (P4). Sin shell, salida truncada."""
    r = run(["grep", "-rn", "--include", glob_ext, "--", patron, "."], timeout=30)
    if r.get("status") in ("ok", "nonzero"):
        lineas = (r.get("stdout") or "").splitlines()[:max_lineas]
        r["stdout"] = "\n".join(lineas)
        r["lineas"] = len(lineas)
    return r
