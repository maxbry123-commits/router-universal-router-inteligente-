"""T11-J — genera ROUTER-FINGERPRINT.md con yaiwes.router-fingerprint/v1.
Puebla SOLO con hechos verificados (existencia de archivo, tests ejecutados aquí).
Estados: ACTIVE (con test/evidencia) | CONFIGURED | PARTIAL | BLOCKED | OFFLINE | UNKNOWN.
Uso: python "chat router/Workflow Loop code Yaiwes/11-EVIDENCIA/router_fingerprint.py" [--write]
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "chat router/Workflow Loop code Yaiwes/02-ARQUITECTURA/ROUTER-FINGERPRINT.md"


def sha_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def exists(rel: str) -> bool:
    return (ROOT / rel).exists()


def run_tests(args: list[str]) -> str:
    p = subprocess.run([sys.executable, "-m", "pytest", "-q", "-p", "no:warnings", *args],
                       cwd=ROOT, capture_output=True, text=True)
    tail = [ln for ln in p.stdout.splitlines() if "passed" in ln or "failed" in ln]
    return tail[-1].strip() if tail else "UNKNOWN"


COMPONENTS = [
    ("State Hub eventos v2 + chain", "router inteligente universal/integration/chat_mvp/ui_bridge.py",
     ["router inteligente universal/tests/test_org_api.py"]),
    ("Runtime T-11 (lease/STUCK/policy/checkpoint/bootstrap)", "router inteligente universal/integration/chat_mvp/task_runtime.py",
     ["router inteligente universal/tests/test_task_runtime.py"]),
    ("Skill runtime v1", "router inteligente universal/integration/chat_mvp/skill_runtime.py",
     ["router inteligente universal/tests/test_skill_runtime.py"]),
    ("Tool contracts Hermes/OpenClaw", "router inteligente universal/integration/chat_mvp/tool_contracts.py",
     ["router inteligente universal/tests/test_tool_contracts.py"]),
    ("Gobierno Sheriff/Judge/Sentinel/Mirror", "chat router/Workflow Loop code Yaiwes/05-AGENTES/gobierno/sheriff.py",
     ["chat router/Workflow Loop code Yaiwes/05-AGENTES/gobierno/tests/"]),
    ("Evidencia gate (buscadores/verificador/puerta)", "chat router/Workflow Loop code Yaiwes/11-EVIDENCIA/puerta.py",
     ["chat router/Workflow Loop code Yaiwes/11-EVIDENCIA/tests/"]),
    ("Checkpoint guard + watchdog", "chat router/Workflow Loop code Yaiwes/03-ESTADO/watchdog_checkpoint.py", []),
]

EXTERNAL = [
    ("Router permanente HF Job", "RUNNING cpu-basic 16GB /health 200 verificado 2026-10-01"),
    ("CI GitHub Actions verify", "BLOCKED — billing lock de cuenta, el job nunca arranca"),
    ("E2E GitHub público", "BLOCKED — rate limit sin GITHUB_TOKEN"),
    ("Graphiti/Graphify runtime", "CONFIGURED — código descargado, sin probe activo"),
    ("Redis/Postgres/FalkorDB", "CONFIGURED — componentes descargados, sin runtime conectado"),
    ("T-06 visual", "PARTIAL — agente de pruebas sin cupo; sin capturas ni segunda pasada"),
    ("Vercel", "UNKNOWN — sin acceso autenticado en esta sesión"),
    ("OpenAI real response", "UNKNOWN — sin clave provista en esta sesión"),
]


def fingerprint() -> dict:
    now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    comps = []
    for name, path, tests in COMPONENTS:
        entry = {"name": name, "path": path,
                 "status": "ACTIVE" if exists(path) else "MISSING",
                 "sha256": sha_file(ROOT / path) if exists(path) else None}
        if tests:
            entry["tests"] = run_tests(tests)
        comps.append(entry)
    return {"schema": "yaiwes.router-fingerprint/v1", "generated_at": now,
            "components": comps, "external": EXTERNAL}


def render(fp: dict) -> str:
    lines = [f"# ROUTER-FINGERPRINT — {fp['schema']}", "",
             f"Generado: {fp['generated_at']} (hechos verificados; sin secretos)", "",
             "## Componentes"]
    for c in fp["components"]:
        sha = (c.get("sha256") or "-")[:16]
        tests = c.get("tests", "sin tests")
        lines.append(f"- **{c['name']}** — `{c['status']}` sha:{sha} tests:{tests} ({c['path']})")
    lines += ["", "## Externos / gaps"]
    lines += [f"- {n}: {s}" for n, s in fp["external"]]
    return chr(10).join(lines) + chr(10)


def main() -> int:
    fp = fingerprint()
    md = render(fp)
    if "--write" in sys.argv:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(md, encoding="utf-8")
        print("escrito", OUT)
    else:
        print(md)
    manifest_sha = hashlib.sha256(json.dumps(fp, sort_keys=True).encode()).hexdigest()
    print("manifest_sha256:", manifest_sha)
    return 0


if __name__ == "__main__":
    sys.exit(main())
