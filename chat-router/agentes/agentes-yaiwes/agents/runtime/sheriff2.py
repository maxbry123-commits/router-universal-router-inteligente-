"""Sheriff v2: the micro-kernel Sheriff (deterministic) plus a JavaScript syntax check (node --check)."""
from __future__ import annotations

import re
import subprocess
from pathlib import Path
from typing import Any

from kernel import sheriff as base

SheriffResult = base.SheriffResult


def extract_js(text: str) -> str:
    m = re.search(r"```(?:javascript|js)\s*\n(.*?)```", text, re.S) or re.search(r"```\s*\n(.*?)```", text, re.S)
    return (m.group(1) if m else text).strip() + "\n"


def run(checks: list[dict[str, Any]], output: str, workdir: Path, owners: set[str]) -> SheriffResult:
    js = [c for c in checks if c["kind"] == "js_syntax"]
    res = base.run([c for c in checks if c["kind"] != "js_syntax"], output, workdir, owners)
    fails, evidence = list(res.failures), list(res.evidence)
    for c in js:
        code = extract_js(output)
        workdir.mkdir(parents=True, exist_ok=True)
        target = workdir / c["file"]
        target.write_text(code, encoding="utf-8")
        try:
            p = subprocess.run(["node", "--check", str(target)], capture_output=True, text=True, timeout=20)
            evidence.append({"kind": "node_check", "exit": p.returncode, "file": c["file"], "sha256": base.sha256(code)})
            if p.returncode != 0:
                fails.append("JavaScript inválido: " + ((p.stderr.strip().splitlines() or [""])[0])[:160])
        except FileNotFoundError:
            fails.append("node no está disponible")
        except subprocess.TimeoutExpired:
            fails.append("node --check superó el tiempo")
    return SheriffResult(passed=not fails, failures=fails, evidence=evidence)
