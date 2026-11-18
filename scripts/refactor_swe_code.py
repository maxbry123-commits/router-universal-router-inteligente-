"""refactor_swe_code.py — P2-2: split de SWE CODE si >200 LOC.
- Target: $SWE_CODE_PATH o heurística de paths comunes.
- Si ≤200 LOC o ya refactorizado (pkg existe) → SKIP.
- Preserva API pública (funciones/clases top-level reexportadas).
- Backup en `.bak` (NO se commitea).
"""
import ast
import os
import sys
import shutil
from pathlib import Path

MAX_LOC = 200
CANDIDATES = [
    "external/tools/swe_code.py",
    "external/swe_code.py",
    "router_llm_hf/swe_code.py",
]


def find_target() -> Path | None:
    env = os.getenv("SWE_CODE_PATH")
    if env and Path(env).exists():
        return Path(env)
    for c in CANDIDATES:
        if Path(c).exists():
            return Path(c)
    return None


def split_by_top_level(src: str):
    tree = ast.parse(src)
    lines = src.splitlines(keepends=True)
    header_end = 0
    top_defs = []
    for node in tree.body:
        if isinstance(node, (ast.Import, ast.ImportFrom, ast.Assign, ast.AnnAssign)):
            header_end = max(header_end, node.end_lineno)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            top_defs.append((node.name, node.lineno - 1, node.end_lineno,
                             isinstance(node, ast.ClassDef)))
    header = "".join(lines[:header_end])
    chunks, current, cur_loc = [], [], 0
    for name, s, e, _ in top_defs:
        body = "".join(lines[s:e])
        loc = body.count("\n")
        if cur_loc + loc > MAX_LOC and current:
            chunks.append(current)
            current, cur_loc = [], 0
        current.append((name, body))
        cur_loc += loc
    if current:
        chunks.append(current)
    return header, chunks


def main():
    target = find_target()
    if not target:
        print("SWE_CODE_NOT_FOUND: nada que refactorizar (SKIP).")
        return
    src = target.read_text(encoding="utf-8")
    loc = src.count("\n")
    if loc <= MAX_LOC:
        print(f"SWE_CODE_OK: {target} → {loc} LOC (≤{MAX_LOC}). SKIP.")
        return
    pkg = target.parent / f"{target.stem}_pkg"
    if pkg.exists():
        print(f"ALREADY_REFACTORED: {pkg} ya existe. SKIP.")
        return

    try:
        header, chunks = split_by_top_level(src)
    except SyntaxError as e:
        print(f"FATAL: ast.parse falló en {target}: {e}", file=sys.stderr)
        sys.exit(1)

    # Gap #1 (fix incorporado por el Director): bloque único >200 LOC -> split manual.
    if len(chunks) == 1 and loc > MAX_LOC:
        print(f"SWE_NEEDS_MANUAL_SPLIT: {target} es 1 bloque de {loc} LOC. "
              f"Requiere split manual por funciones internas.", file=sys.stderr)
        sys.exit(2)

    pkg.mkdir()
    public = []
    for i, chunk in enumerate(chunks, 1):
        part = pkg / f"part_{i:02d}.py"
        body = header + "\n\n" + "\n\n".join(c[1] for c in chunk)
        part.write_text(body, encoding="utf-8")
        public.extend(c[0] for c in chunk)
        print(f"[part] {part.name} — {body.count(chr(10))} LOC")

    init = '"""Auto-refactor (Salida 2C). Reexporta API pública."""\n'
    for i in range(1, len(chunks) + 1):
        init += f"from .part_{i:02d} import *  # noqa\n"
    init += f"\n__all__ = {public!r}\n"
    (pkg / "__init__.py").write_text(init, encoding="utf-8")

    backup = target.with_suffix(target.suffix + ".bak")
    shutil.copy2(target, backup)

    rel = target.relative_to(Path.cwd()).with_suffix("")
    pkg_module = ".".join(rel.parent.parts + (rel.name + "_pkg",))
    facade = (
        f'"""{target.stem} facade — delegado a {pkg_module} (Salida 2C)."""\n'
        f"from {pkg_module} import *  # noqa\n"
        f"from {pkg_module} import __all__  # noqa\n"
    )
    target.write_text(facade, encoding="utf-8")
    print(f"REFACTOR_OK: {target} → {pkg} ({len(chunks)} partes). Backup: {backup}")


if __name__ == "__main__":
    main()
