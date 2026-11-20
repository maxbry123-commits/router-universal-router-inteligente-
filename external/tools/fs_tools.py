"""fs_tools.py - Lectura/escritura/grep con sandbox de path."""
import os, re
from pathlib import Path

ROOT = Path(os.getenv("WORKSPACE_ROOT", os.getcwd())).resolve()

def _safe(p: str) -> Path:
    t = (ROOT / p).resolve()
    if ROOT not in t.parents and t != ROOT:
        raise PermissionError(f"path outside workspace: {p}")
    return t

def read_file(path: str, max_bytes: int = 500_000) -> dict:
    try:
        p = _safe(path)
        if not p.is_file(): return {"ok": False, "error": "not_file"}
        data = p.read_bytes()[:max_bytes]
        return {"ok": True, "path": path, "size": len(data),
                "content": data.decode("utf-8", "replace")}
    except PermissionError as e:
        return {"ok": False, "error": str(e)}

def write_file(path: str, content: str, mkdir: bool = True) -> dict:
    try:
        p = _safe(path)
        if mkdir: p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
        return {"ok": True, "path": path, "bytes": len(content)}
    except PermissionError as e:
        return {"ok": False, "error": str(e)}

def list_dir(path: str = ".") -> dict:
    try:
        p = _safe(path)
        if not p.is_dir(): return {"ok": False, "error": "not_dir"}
        items = []
        for e in sorted(p.iterdir()):
            items.append({"name": e.name,
                          "type": "dir" if e.is_dir() else "file",
                          "size": e.stat().st_size if e.is_file() else 0})
        return {"ok": True, "items": items}
    except PermissionError as e:
        return {"ok": False, "error": str(e)}

def grep(pattern: str, path: str = ".", max_hits: int = 500) -> dict:
    try:
        p = _safe(path)
        rx = re.compile(pattern)
        hits, total = [], 0
        files = [p] if p.is_file() else p.rglob("*")
        for f in files:
            if not f.is_file() or f.stat().st_size > 2_000_000:
                continue
            try:
                txt = f.read_text("utf-8", "replace")
            except Exception:
                continue
            for i, line in enumerate(txt.splitlines(), 1):
                if rx.search(line):
                    hits.append({"file": str(f.relative_to(ROOT)),
                                 "line": i, "text": line[:300]})
                    total += 1
                    if total >= max_hits:
                        return {"ok": True, "hits": hits, "truncated": True}
        return {"ok": True, "hits": hits, "truncated": False}
    except PermissionError as e:
        return {"ok": False, "error": str(e)}
