"""swe_patch.py — Extraccion, validacion y aplicacion reversible de diffs (P3).
Nunca escribe sin `git apply --check` previo. Aplicar al repo requiere
approval_gate (P7); sin gate -> fail-closed.
"""
from __future__ import annotations

import re
import time
from pathlib import Path
from typing import Any

from engine.swe_sandbox import run, ROOT

_FENCE = re.compile(r"```(?:diff|patch)?\s*\n(.*?)```", re.DOTALL)
_DIFF_HEAD = re.compile(r"^(?:diff --git |--- )", re.MULTILINE)


def _degraded(reason: str) -> dict[str, Any]:
    return {"status": "degraded", "reason": reason}


def extract_diff(text: str) -> str:
    """Extrae el diff de un bloque cercado o del texto plano. '' si no hay."""
    if not text:
        return ""
    for m in _FENCE.finditer(text):
        body = m.group(1)
        if _DIFF_HEAD.search(body):
            return body.strip() + "\n"
    if _DIFF_HEAD.search(text):
        lines = text.splitlines()
        start = next((i for i, l in enumerate(lines)
                      if l.startswith("diff --git ") or l.startswith("--- ")), None)
        if start is not None:
            return "\n".join(lines[start:]).strip() + "\n"
    return ""


def check(diff: str) -> dict[str, Any]:
    """git apply --check sin escribir nada."""
    if not diff.strip():
        return _degraded("diff vacio")
    if not _DIFF_HEAD.search(diff):
        return _degraded("diff sin cabecera ---/diff --git")
    r = run(["git", "apply", "--check", "--whitespace=nowarn", "-"],
            stdin=diff, timeout=30)
    if r.get("status") == "ok":
        return {"status": "ok", "aplicable": True}
    return {"status": "degraded", "aplicable": False,
            "reason": "git apply --check: " + (r.get("stderr") or r.get("reason") or "")[:400]}


def apply(diff: str, approved_by: str | None = None) -> dict[str, Any]:
    """Aplica el diff SOLO con aprobacion HITL explicita (P7)."""
    c = check(diff)
    if c.get("status") != "ok":
        return c
    if not approved_by:
        return _degraded("gate_rechazado: aplicar requiere approved_by (HITL)")
    try:
        from plugins.memoria.plugin import handle as mem
        mem("save", {"key": f"swe_apply_{int(time.time())}",
                     "data": {"approved_by": approved_by, "diff": diff[:4000]}})
    except Exception:  # noqa: BLE001
        pass
    r = run(["git", "apply", "--whitespace=nowarn", "-"], stdin=diff, timeout=60)
    if r.get("status") == "ok":
        return {"status": "ok", "aplicado": True, "approved_by": approved_by}
    return {"status": "degraded", "aplicado": False,
            "reason": "git apply: " + (r.get("stderr") or "")[:400]}


def revert() -> dict[str, Any]:
    """Revierte el working tree al HEAD (solo archivos rastreados)."""
    r = run(["git", "checkout", "--", "."], timeout=60)
    return {"status": "ok" if r.get("status") == "ok" else "degraded",
            "revertido": r.get("status") == "ok",
            "reason": (r.get("stderr") or "")[:300]}


def touched_files(diff: str) -> list[str]:
    """Lista de rutas afectadas, para acotar los tests a correr."""
    out: list[str] = []
    for line in diff.splitlines():
        if line.startswith("+++ b/"):
            p = line[6:].strip()
            if p and p != "/dev/null" and p not in out:
                out.append(p)
    return out


def tests_for(diff: str) -> list[str]:
    """Heuristica determinista: tests hermanos de los archivos tocados."""
    cands: list[str] = []
    for p in touched_files(diff):
        path = Path(p)
        if path.suffix != ".py":
            continue
        if path.name.startswith("test_"):
            cands.append(p)
            continue
        for guess in (path.parent / "tests" / f"test_{path.name}",
                      path.parent / f"test_{path.name}"):
            if (ROOT / guess).is_file():
                g = str(guess)
                if g not in cands:
                    cands.append(g)
    return cands
