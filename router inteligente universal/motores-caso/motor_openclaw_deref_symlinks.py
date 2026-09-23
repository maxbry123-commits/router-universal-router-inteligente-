#!/usr/bin/env python3
"""Caso OpenClaw: motor NUEVO. No modifica los motores del skill.

Materializa symlinks a archivo regular y luego llama el engine canónico
sin editarlo. Fail-closed si un symlink apunta fuera del árbol.
"""
from __future__ import annotations
import importlib.util, os, pathlib, sys

HERE = pathlib.Path(__file__).resolve().parent
ENGINE = pathlib.Path(os.getenv("ENGINE_PATH", "/tmp/motor/engine.py"))

def deref(root: pathlib.Path) -> int:
    n = 0
    root = root.resolve()
    for p in sorted(root.rglob("*"), key=lambda x: x.as_posix()):
        if not p.is_symlink():
            continue
        target = p.resolve()
        if not str(target).startswith(str(root) + os.sep) and target != root:
            raise RuntimeError("SYMLINK_ESCAPES_TREE:" + str(p.relative_to(root)))
        if target.is_dir():
            raise RuntimeError("SYMLINK_DIR_GAP:" + str(p.relative_to(root)))
        data = target.read_bytes() if target.is_file() else b""
        p.unlink()
        p.write_bytes(data)
        n += 1
    return n

def main() -> None:
    if not ENGINE.is_file():
        raise SystemExit("CANONICAL_ENGINE_MISSING")
    spec = importlib.util.spec_from_file_location("yaiwes_engine", ENGINE)
    eng = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(eng)
    orig = eng.acquire

    def acquire_deref(work):
        src, commit = orig(work)
        deref(src)
        return src, commit

    eng.acquire = acquire_deref
    os.environ.setdefault("SOURCE_REPO", "openclaw/openclaw")
    os.environ.setdefault("SOURCE_REF", "v2026.9.5")
    os.environ.setdefault("SLUG", "openclaw")
    os.environ.setdefault("GIT_LFS_SKIP_SMUDGE", "1")
    eng.main()

if __name__ == "__main__":
    main()
