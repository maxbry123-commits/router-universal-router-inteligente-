#!/usr/bin/env python3
"""Copia solo archivos nuevos de este DELTA al proyecto NCT existente.

No sobreescribe archivos diferentes y no modifica scheduler/router/memoria.
"""
from __future__ import annotations
import argparse
import shutil
import hashlib
from pathlib import Path

HERE=Path(__file__).resolve().parent
FILES=sorted([*HERE.glob('nct_loop/*.py'),*HERE.glob('tests/*.py'),
              HERE/'GENERAR_ECC_PY.py',HERE/'EJECUTAR_CODA_CORREGIDO.py',HERE/'PROBAR_DELTA.py'])

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--proyecto',required=True,type=Path)
    p.add_argument('--dry-run',action='store_true')
    a=p.parse_args()
    root=a.proyecto.resolve()
    if not (root/'nct_loop/engine.py').is_file() or not (root/'referencia_ricardo/motor_cli.py').is_file():
        raise SystemExit('El destino no es el proyecto NCT + Ricardo original; no se ha escrito nada.')
    for src in FILES:
        relative=src.relative_to(HERE)
        target=root/relative
        if target.is_symlink():raise SystemExit(f'Prohibido symlink: {relative}')
        if target.exists() and target.read_bytes()!=src.read_bytes():
            raise SystemExit(f'Conflicto: {relative}. Rechazo sobrescritura.')
    for src in FILES:
        target=root/src.relative_to(HERE)
        if not target.exists():
            if not a.dry_run:
                target.parent.mkdir(parents=True,exist_ok=True)
                shutil.copy2(src,target)
        print(('VERIFICAR' if a.dry_run else 'OK'),src.relative_to(HERE))
    print('Archivos previos preservados: sí')

if __name__=='__main__':main()
