from __future__ import annotations
import ast
from pathlib import Path
from ..contracts import Status
from ._common import index_evidence, iter_files, result

LAYER = "L03_XRAY_CODE"


def run(node, ctx):
    root = Path(ctx.get("repo_root") or "")
    if not ctx.get("repo_root") or not root.is_dir():
        return result(node, Status.INCONCLUSIVE, gaps=["L03_INPUT_GAP:repo_root"])
    files = list(iter_files(root, (".py",)))
    gaps = []
    for f in files:
        try:
            ast.parse(f.read_text(encoding="utf-8"))
        except SyntaxError as e:
            gaps.append(f"SYNTAX_ERROR:{f.relative_to(root).as_posix()}:{e.lineno}")
        except Exception:
            gaps.append(f"UNREADABLE:{f.relative_to(root).as_posix()}")
    if not files:
        gaps.append("NO_CODE_FOUND")
    status = Status.PASS if files and not gaps else Status.INCONCLUSIVE
    return result(node, status, output={"python_files": len(files), "repo_priority": ctx.get("repo_priority", [])},
                  evidence=[index_evidence("code_index", root, files)] if files else [], gaps=gaps[:50])
