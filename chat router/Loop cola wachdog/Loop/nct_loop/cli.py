"""CLI demo: ejecuciones REALES de archivos locales, cero llamadas a IA/red."""
import argparse,asyncio,json,tempfile
from pathlib import Path
from .engine import NCTLoopEngine
from .ecc_runtime import ECCCodeRuntime
from .ports import InlineQueueDemo,DemoMemory,DemoModel
from .ricardo_adapter import RicardoOpsDemo,FileCheckerDemo

BASE=Path(__file__).resolve().parent.parent

async def run_demo(mission_file:Path,proposals_file:Path,workspace:Path):
    mission=json.loads(mission_file.read_text(encoding='utf8'))
    fixture=json.loads(proposals_file.read_text(encoding='utf8'))
    policy=BASE/'referencia_ricardo/allowed_ops.json'
    ops=set(json.loads(policy.read_text())['allowed_ops'])
    engine=NCTLoopEngine(
        ecc=ECCCodeRuntime(BASE/'config/ecc_rules.json'),
        model=DemoModel(fixture),queue=InlineQueueDemo(),memory=DemoMemory(),
        tools=RicardoOpsDemo(workspace,policy),checker=FileCheckerDemo(workspace),
        resources_file=BASE/'config/resources.json',known_blocks={'executor'},
        approved_ops=ops,max_calls=60)
    return await engine.run(mission)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--demo',action='store_true',help='prueba local sin proveedor')
    ap.add_argument('--mission',default=str(BASE/'examples/mission_smoke.json'))
    ap.add_argument('--proposals',default=str(BASE/'examples/mock_proposals.json'))
    ap.add_argument('--workspace',help='carpeta de prueba aislada')
    ns=ap.parse_args()
    if not ns.demo:ap.error('Solo --demo. La integración con el scheduler real requiere sus contratos.')
    if ns.workspace:
        answer=asyncio.run(run_demo(Path(ns.mission),Path(ns.proposals),Path(ns.workspace)))
    else:
        with tempfile.TemporaryDirectory(prefix='nct_test_') as t:
            answer=asyncio.run(run_demo(Path(ns.mission),Path(ns.proposals),Path(t)))
    print(json.dumps(answer,ensure_ascii=False,indent=2))
    return 0 if answer['status']=='DONE_VERIFICADO' else 1

if __name__=='__main__':raise SystemExit(main())
