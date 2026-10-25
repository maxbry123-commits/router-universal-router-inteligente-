"""Sandbox Engine: ejecuta Python en subproceso aislado con timeout y límite
de salida. JS vía `node -e` si node existe (si no, GAP)."""
from __future__ import annotations

import asyncio
import shutil
import sys

from engine import Engine, ok, fail

MAX_OUTPUT = 64 * 1024  # 64 KB
DEFAULT_TIMEOUT = 10


class SandboxEngine(Engine):
    id = "code.sandbox"
    capabilities = ["code.sandbox"]

    def __init__(self, timeout: int = DEFAULT_TIMEOUT,
                 max_output: int = MAX_OUTPUT):
        self.timeout = timeout
        self.max_output = max_output

    async def _run(self, argv: list[str]) -> dict:
        try:
            proc = await asyncio.create_subprocess_exec(
                *argv,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
        except FileNotFoundError:
            return fail(f"intérprete no encontrado: {argv[0]}")
        try:
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(), timeout=self.timeout)
        except asyncio.TimeoutError:
            proc.kill()
            await proc.wait()
            return fail("timeout", rc=None)
        return {
            "status": "PASS",
            "rc": proc.returncode,
            "stdout": stdout.decode(errors="replace")[: self.max_output],
            "stderr": stderr.decode(errors="replace")[: self.max_output],
            "truncated": len(stdout) > self.max_output
            or len(stderr) > self.max_output,
        }

    async def run_python(self, code: str) -> dict:
        return await self._run([sys.executable, "-I", "-c", code])

    async def run_js(self, code: str) -> dict:
        if shutil.which("node") is None:
            return fail("GAP: node no disponible en este entorno")
        return await self._run(["node", "-e", code])

    async def execute(self, task: dict, context: dict | None = None) -> dict:
        lang = task.get("lang", "python")
        code = task.get("code", "")
        if not code:
            return fail("sin código")
        if lang == "python":
            return await self.run_python(code)
        if lang in ("js", "javascript"):
            return await self.run_js(code)
        return fail(f"lenguaje no soportado: {lang}")

    async def verify(self, result: dict) -> bool:
        return result.get("status") == "PASS" and result.get("rc") == 0
