#!/usr/bin/env python3
"""Entrada ejecutable NCT LOOP ECC CODA. Solo demo local, sin conectar a la IA real."""
from __future__ import annotations
import argparse
import asyncio
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def execute_demo(kind: str, workdir: Path, *, show_json: bool) -> bool:
    from nct_loop.cli import run_demo
    files = {
        'smoke': ('mission_smoke.json', 'mock_proposals.json'),
        'coda': ('mission_coda_2tasks.json', 'mock_proposals_2tasks.json'),
    }
    mission, proposals = files[kind]
    result = asyncio.run(run_demo(ROOT / 'examples' / mission,
                                  ROOT / 'examples' / proposals, workdir))
    gates = [entry['gate'] for entry in result.get('trace', []) if 'gate' in entry]
    receipt_count = len(result.get('receipts', []))
    summary = {
        'status': result.get('status'), 'phase_reached': result.get('phase_reached'),
        'tasks_with_real_receipts': receipt_count,
        'ecc_python_gates_executed': len(gates),
        'ecc_python_actions_checked': sum(len(g['triggered']) for g in gates),
        'workspace': str(workdir),
        'note': 'Solo motor JSON/Python local. Las llamadas Qwen son fixtures, no inferencia real.',
    }
    if show_json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    return result.get('status') == 'DONE_VERIFICADO'


def run_tests() -> bool:
    # Contratos originales Ricardo ejecutados desde su propia carpeta (su import es local).
    commands = [
        (ROOT, [sys.executable, '-m', 'unittest', 'discover', '-s', 'tests', '-v']),
        (ROOT / 'referencia_ricardo', [sys.executable, '-m', 'unittest', '-v', 'pruebas_motor']),
    ]
    all_ok = True
    for directory, command in commands:
        print('TESTS:', directory.name, flush=True)
        cp = subprocess.run(command, cwd=directory, check=False)
        all_ok = all_ok and cp.returncode == 0
    return all_ok


def main():
    ap = argparse.ArgumentParser(description='NCT LOOP ECC CODA — Código Python ejecutable')
    ap.add_argument('--modo', choices=['smoke', 'coda', 'tests', 'verificar'], default='verificar')
    ap.add_argument('--workspace', help='Carpeta local de pruebas; nunca produccion')
    ap.add_argument('--json', action='store_true', help='Mostrar recibos, eventos y trazas completos')
    ns = ap.parse_args()
    if ns.modo == 'tests':
        return 0 if run_tests() else 1
    if ns.modo == 'verificar':
        if not run_tests():
            return 1
        with tempfile.TemporaryDirectory(prefix='nct_ecc_smoke_') as tmp:
            a = execute_demo('smoke', Path(tmp), show_json=ns.json)
        with tempfile.TemporaryDirectory(prefix='nct_ecc_coda_') as tmp:
            b = execute_demo('coda', Path(tmp), show_json=ns.json)
        return 0 if a and b else 1
    if ns.workspace:
        root = Path(ns.workspace).expanduser().resolve()
        root.mkdir(parents=True, exist_ok=True)
        return 0 if execute_demo(ns.modo, root, show_json=ns.json) else 1
    with tempfile.TemporaryDirectory(prefix='nct_ecc_demo_') as tmp:
        return 0 if execute_demo(ns.modo, Path(tmp), show_json=ns.json) else 1


if __name__ == '__main__':
    raise SystemExit(main())
