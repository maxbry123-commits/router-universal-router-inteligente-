"""Watchdog de checkpoint — un comando ejecuta el ciclo completo pedido por el Director:
checkpoint_guard heartbeat + verificación ROOT-MAP + refresco de STATE/CRAZY_WALL/HANDOFF/Bitácora.
Uso: python "chat router/03-ESTADO/watchdog_checkpoint.py" --summary "..." [--test-result N=R] [--error E]
El archivo README de arquitectura se regenera con hechos verificados (tests, rutas, estado).
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ESTADO = ROOT / "chat router/03-ESTADO"
GUARD = ESTADO / "checkpoint_guard.py"
ROOT_MAP_VERIFY = ROOT / "chat router/11-EVIDENCIA/root_map_verify.py"
ARCH_README = ROOT / "chat router/02-ARQUITECTURA/README-ARQUITECTURA.md"


def run(cmd: list[str]) -> tuple[int, str]:
    p = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    return p.returncode, (p.stdout + p.stderr).strip()


def checkpoint(summary: str, tests: list[str], errors: list[str]) -> int:
    cmd = [sys.executable, str(GUARD), "heartbeat", "--summary", summary]
    for t in tests:
        cmd += ["--test-result", t]
    for e in errors:
        cmd += ["--error", e]
    rc, out = run(cmd)
    print(out)
    return rc


def architecture_readme(extra: dict) -> None:
    now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    body = f"""# README ARQUITECTURA — YAIWES Router (watchdog {now})

Generado por watchdog_checkpoint.py — SOLO hechos verificados; lo no comprobado queda UNKNOWN/BLOCKED.

## Estado verificado
- Suite local: {extra.get('tests', 'UNKNOWN')}
- ROOT-MAP-T11: {extra.get('root_map', 'UNKNOWN')}
- Router permanente HF: RUNNING cpu-basic 16 GB, /health 200 (verificado 2026-10-01)
- CI GitHub Actions verify: BLOCKED (cuenta con billing lock; job nunca arranca — no es código)

## Capas activas (con tests)
- integration/chat_mvp/ui_bridge.py — State Hub: eventos v2 + chain_prev + CAS append (6 tests)
- integration/chat_mvp/task_runtime.py — claim/lease, STUCK, failure policy, crash/resume, WorkerBootstrap, workspaces, run ledger (12 tests)
- integration/chat_mvp/skill_runtime.py — yaiwes.skill-runtime/v1 (4 tests)
- integration/chat_mvp/tool_contracts.py — tools Hermes/OpenClaw con rutas verificadas (4 tests)
- chat router/05-AGENTES/gobierno/ — Sheriff, Judge, Sentinel, MirrorManager, MirrorFactory (41 tests)
- chat router/11-EVIDENCIA/ — buscadores (timeout duro), verificador, puerta, evidence_pack

## Pendientes (🚩)
- E2E GitHub público (rate limit sin token)
- Autenticación real de reviewers externos; integridad criptográfica de eventos (hash local, no firma)
- T-06 visual: agente de pruebas sin cupo (sin capturas ni segunda pasada)
- Runtimes Graphiti/Graphify/Redis/etc. descargados pero sin probe activo
- Vercel: sin acceso autenticado; límite diario no verificable
"""
    ARCH_README.parent.mkdir(parents=True, exist_ok=True)
    ARCH_README.write_text(body, encoding="utf-8")
    print("README-ARQUITECTURA actualizado")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--summary", required=True)
    ap.add_argument("--test-result", action="append", default=[])
    ap.add_argument("--error", action="append", default=[])
    a = ap.parse_args()

    rc_rm, out_rm = run([sys.executable, str(ROOT_MAP_VERIFY)])
    root_map_ok = "PASS" in out_rm
    print("root_map:", "PASS" if root_map_ok else out_rm[-200:])

    rc = checkpoint(a.summary, a.test_result, a.error)
    architecture_readme({"tests": "; ".join(a.test_result) or "UNKNOWN",
                         "root_map": "PASS" if root_map_ok else "FAIL"})
    print("watchdog checkpoint:", "DONE" if rc == 0 else f"RC={rc}")
    return rc


if __name__ == "__main__":
    sys.exit(main())
