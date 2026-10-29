#!/usr/bin/env python3
"""Procesa todos los SKILL.md de una copia de ECC y genera módulos Python.

python GENERAR_ECC_PY.py --ecc-dir ./ECC --output ./ecc_generado
python GENERAR_ECC_PY.py --download-main --output ./ecc_generado

Los wrappers NO pueden ejecutar acciones sin handlers Python aprobados.
"""
import argparse
import json
from pathlib import Path
from nct_loop.ecc_phase_compiler import compile_directory,write_compiled_catalog,make_python_wrappers
from nct_loop.ecc_source_sync import fetch_ecc_skills

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--ecc-dir',type=Path)
    p.add_argument('--download-main',action='store_true')
    p.add_argument('--ref',default='main')
    p.add_argument('--output',required=True,type=Path)
    a=p.parse_args()
    if bool(a.ecc_dir)==a.download_main:
        p.error('Elija exactamente --ecc-dir o --download-main')
    root=a.ecc_dir
    if a.download_main:
        root=a.output/'ecc_sources'
        details=fetch_ecc_skills(root,a.ref)
    else: details={'root':str(root),'downloaded_skills':None}
    registry=compile_directory(root)
    write_compiled_catalog(registry,a.output/'ecc_compilado.json')
    generated=make_python_wrappers(registry,a.output/'motores_code')
    print(json.dumps({**details,'source_skills_compiled':len(registry),
                      'python_wrappers_generated':generated,
                      'functional_actions_authorized':0,
                      'reason':'Cada handler de fase requiere implementación y autorización verificadas'},
                     ensure_ascii=False))

if __name__=='__main__':main()
