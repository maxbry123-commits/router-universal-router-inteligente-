"""swe_context.py — Recuperacion acotada de contexto + ligas de artefactos (P4, P6).
Nunca lee archivos completos: grep + ventanas de lineas con tope de bytes.
Las ligas guardan el artefacto completo con intentos numerados (no sobrescribe).
"""
from __future__ import annotations

import hashlib
import re
import time
from pathlib import Path
from typing import Any

from engine.swe_sandbox import grep_repo, ROOT

STOP = {
    "the", "and", "for", "with", "that", "this", "from", "when", "then",
    "does", "not", "are", "was", "has", "have", "into", "upon", "should",
    "para", "como", "donde", "cuando", "este", "esta", "pero", "porque",
    "fix", "bug", "error", "issue", "please", "make", "code", "file",
}
MAX_BYTES = 12000
WINDOW = 12


def keywords(issue: str, max_kw: int = 6) -> list[str]:
    """Determinista: tokens alfabeticos >3 chars, sin stopwords, orden de aparicion."""
    out: list[str] = []
    for tok in re.findall(r"[A-Za-z_][A-Za-z0-9_]{3,}", (issue or "").lower()):
        if tok not in STOP and tok not in out:
            out.append(tok)
        if len(out) >= max_kw:
            break
    return out


def _ventana(path: Path, lineno: int) -> str:
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except Exception:  # noqa: BLE001
        return ""
    a = max(0, lineno - WINDOW)
    b = min(len(lines), lineno + WINDOW)
    body = "\n".join(f"{i + 1}: {lines[i]}" for i in range(a, b))
    return f"--- {path.relative_to(ROOT)} L{a + 1}-{b} ---\n{body}\n"


def build_context(issue: str, max_bytes: int = MAX_BYTES) -> dict[str, Any]:
    """grep por keyword -> ventanas acotadas. Devuelve {context, fuentes, bytes}."""
    kws = keywords(issue)
    trozos: list[str] = []
    fuentes: list[str] = []
    total = 0
    for kw in kws:
        r = grep_repo(kw, "*.py", max_lineas=12)
        for line in (r.get("stdout") or "").splitlines():
            m = re.match(r"^\./(.+?):(\d+):", line)
            if not m:
                continue
            rel, ln = m.group(1), int(m.group(2))
            if rel in fuentes or "/tests/" in rel or rel.startswith("engine/swe_"):
                continue
            p = ROOT / rel
            if not p.is_file():
                continue
            v = _ventana(p, ln)
            if not v or total + len(v) > max_bytes:
                continue
            trozos.append(v)
            fuentes.append(rel)
            total += len(v)
            if total >= max_bytes:
                break
        if total >= max_bytes:
            break
    return {"context": "\n".join(trozos), "fuentes": fuentes,
            "bytes": total, "keywords": kws}


def issue_id(issue: str) -> str:
    return hashlib.sha256((issue or "").encode("utf-8")).hexdigest()[:16]


def save_liga(issue: str, artefacto: dict[str, Any]) -> str | None:
    """Guarda intento numerado; nunca sobrescribe el anterior."""
    try:
        from plugins.memoria.plugin import handle as mem
        base = f"swe_{issue_id(issue)}"
        prev = mem("search", {"query": base, "limit": 100})
        n = int(prev.get("count", 0)) + 1
        key = f"{base}_i{n:03d}"
        r = mem("save", {"key": key, "data": {
            "issue": (issue or "")[:800],
            "intento": n,
            "ts": time.time(),
            **artefacto,
        }})
        return key if r.get("status") == "ok" else None
    except Exception:  # noqa: BLE001
        return None


def load_ligas(issue: str, limit: int = 10) -> list[dict[str, Any]]:
    try:
        from plugins.memoria.plugin import handle as mem
        r = mem("search", {"query": f"swe_{issue_id(issue)}", "limit": limit})
        return r.get("results", []) if r.get("status") == "ok" else []
    except Exception:  # noqa: BLE001
        return []
