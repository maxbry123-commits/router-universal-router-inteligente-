#!/usr/bin/env python3
"""Ejecuta el orden correcto RED -> JSON Ricardo -> pruebas -> revisión.

Solo DEMO local: DemoModel produce respuestas preparadas.
Las ejecuciones reales de modelos usan ExistingModelHooks y el host existente.
"""
from __future__ import annotations
import argparse
import asyncio
import json
import tempfile
from pathlib import Path

async def run(project:Path):
    from nct_loop.ports import DemoMemory,DemoModel,InlineQueueDemo
    from nct_loop.ecc_runtime import ECCCodeRuntime
    from nct_loop.ricardo_adapter import RicardoOpsDemo,FileCheckerDemo
    from nct_loop.engine_coda_fixed import NCTLoopCodaFixed
    root=Path(project).resolve()
    mission=json.loads((root/'examples/mission_coda_2tasks.json').read_text(encoding='utf8'))
    proposals=json.loads((root/'examples/mock_proposals_2tasks.json').read_text(encoding='utf8'))
    allowed=json.loads((root/'referencia_ricardo/allowed_ops.json').read_text(encoding='utf8'))
    with tempfile.TemporaryDirectory(prefix='nct_coda_fixed_') as tmp:
        path=Path(tmp)
        engine=NCTLoopCodaFixed(ecc=ECCCodeRuntime(root/'config/ecc_rules.json'),
            model=DemoModel(proposals),queue=InlineQueueDemo(),memory=DemoMemory(),
            tools=RicardoOpsDemo(path,root/'referencia_ricardo/allowed_ops.json'),
            checker=FileCheckerDemo(path),resources_file=root/'config/resources.json',
            known_blocks={'executor'},approved_ops=set(allowed['allowed_ops']))
        result=await engine.run(mission)
        return {'status':result.get('status'),'phase':result.get('phase_reached'),
                'receipt_count':len(result.get('receipts',[])),'error':result.get('error'),
                'model_type':'FIXTURE_LOCAL_NOT_LIVE'}

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--proyecto',type=Path,default=Path(__file__).resolve().parent)
    args=p.parse_args()
    res=asyncio.run(run(args.proyecto))
    print(json.dumps(res,ensure_ascii=False,indent=2))
    raise SystemExit(0 if res['status']=='DONE_VERIFICADO' else 1)
