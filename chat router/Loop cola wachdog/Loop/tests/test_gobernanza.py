import asyncio, json, tempfile, unittest
from pathlib import Path
from nct_loop.engine import NCTLoopEngine
from nct_loop.ecc_runtime import ECCCodeRuntime
from nct_loop.ports import DemoMemory, DemoModel, InlineQueueDemo
from nct_loop.ricardo_adapter import RicardoOpsDemo, FileCheckerDemo
from nct_loop.gobernanza import Gobernanza, CICLOS, MOTORES, MICROCICLO

ROOT = Path(__file__).resolve().parent.parent
OPS = set(json.loads((ROOT / 'referencia_ricardo/allowed_ops.json').read_text())['allowed_ops'])


class GobernanzaTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.mission = json.loads((ROOT / 'examples/mission_smoke.json').read_text())
        prop = json.loads((ROOT / 'examples/mock_proposals.json').read_text())
        self.eng = NCTLoopEngine(
            ecc=ECCCodeRuntime(ROOT / 'config/ecc_rules.json'), model=DemoModel(prop),
            queue=InlineQueueDemo(), memory=DemoMemory(),
            tools=RicardoOpsDemo(Path(self.tmp.name), ROOT / 'referencia_ricardo/allowed_ops.json'),
            checker=FileCheckerDemo(Path(self.tmp.name)),
            resources_file=ROOT / 'config/resources.json', known_blocks={'executor'},
            approved_ops=OPS, max_calls=60)

    def tearDown(self):
        self.tmp.cleanup()

    def gob(self, **kw):
        base = dict(ejecutar_mision=self.eng.run, ricardo=self.eng.tools, construir_mision=lambda p, s: self.mission,
                    ops_permitidas=OPS, checkpoint_dir=self.tmp.name)
        base.update(kw)
        return Gobernanza(**base)

    async def test_ciclos_en_orden_y_done_verificado(self):
        r = await self.gob().run({'objetivo': 'Crear evidencia real y verificarla en el workspace'})
        self.assertEqual(r['status'], 'DONE_VERIFICADO', r)
        self.assertEqual([c['ciclo'] for c in r['ciclos']], list(CICLOS))
        self.assertTrue(r['watchdog']['orden_valido'])
        self.assertEqual(r['watchdog']['estado'], 'OK')
        self.assertTrue(list(Path(self.tmp.name).glob('gobernanza_*.json')))

    async def test_cada_ciclo_tiene_un_motor(self):
        self.assertEqual(sorted(c for cs in MOTORES.values() for c in cs), sorted(CICLOS))

    async def test_microciclo_se_lee_del_trace(self):
        r = await self.gob().run({'objetivo': 'Crear evidencia real y verificarla en el workspace'})
        c5 = next(c for c in r['ciclos'] if c['ciclo'] == 'C5_EJECUCION')
        pasos = c5['microciclo'][0]['pasos']
        self.assertEqual(set(pasos), {m[0] for m in MICROCICLO})
        self.assertIs(pasos['IMPLEMENTAR'], True)
        self.assertIs(pasos['EJECUTAR_GREEN'], True)

    async def test_ricardo_participa_en_todos_los_ciclos(self):
        r = await self.gob().run({'objetivo': 'Crear evidencia real y verificarla en el workspace'})
        self.assertEqual(r['status'], 'DONE_VERIFICADO', r)
        for c in r['ciclos']:
            if c['ciclo'] != 'C2_DECISION':
                self.assertIsNotNone(c.get('ricardo'), c['ciclo'])
        c1 = r['ciclos'][1]['ricardo']
        self.assertEqual(c1['origen'], 'MOTOR_CLI_LOCAL_REAL')
        self.assertGreaterEqual(r['ciclos'][5]['ricardo']['recibos_motor'], 1)

    async def test_ricardo_rechaza_dag_con_dependencia_inexistente(self):
        m = json.loads(json.dumps(self.mission))
        m['units'][0]['depends_on'] = ['NO_EXISTE']
        r = await self.gob(construir_mision=lambda p, s: m).run({'objetivo': 'Crear evidencia real y verificarla'})
        self.assertEqual(r['status'], 'BLOQUEADO')

    async def test_objetivo_vacio_se_rechaza_en_c0(self):
        r = await self.gob().run({'objetivo': ''})
        self.assertEqual(r['status'], 'RECHAZADO')
        self.assertEqual(r['ciclo_alcanzado'], 'C0_ADMISION')

    async def test_guardian_bloquea(self):
        r = await self.gob(cancelado=lambda: True).run({'objetivo': 'Crear evidencia real y verificarla'})
        self.assertEqual(r['motivo'], 'bloqueado_por_guardian')

    async def test_ops_fuera_de_politica(self):
        r = await self.gob().run({'objetivo': 'Crear evidencia real y verificarla', 'allowed_ops': ['rm_rf']})
        self.assertEqual(r['status'], 'RECHAZADO')

    async def test_dag_con_ciclo_bloquea_en_c3(self):
        m = json.loads(json.dumps(self.mission))
        u = m['units'][0]
        v = dict(u, id='S2', depends_on=['S_UNIT'])
        u['depends_on'] = ['S2']
        m['units'].append(v)
        r = await self.gob(construir_mision=lambda p, s: m).run({'objetivo': 'Crear evidencia real y verificarla'})
        self.assertEqual(r['status'], 'BLOQUEADO')
        self.assertEqual(r['ciclo_alcanzado'], 'C3_PLANIFICACION')

    async def test_fallo_del_engine_no_declara_done(self):
        async def falla(_m):
            return {'status': 'BLOCKED', 'error': 'REAL_TOOL_FAILED'}
        r = await self.gob(ejecutar_mision=falla, max_reparaciones=1).run(
            {'objetivo': 'Crear evidencia real y verificarla'})
        self.assertEqual(r['status'], 'FALLO_VERIFICACION')
        self.assertEqual(r['watchdog']['estado'], 'ALERTA')
        c5 = next(c for c in r['ciclos'] if c['ciclo'] == 'C5_EJECUCION')
        self.assertEqual(c5['intentos'], 2)

    async def test_motores_de_cada_ciclo_corren_todos_y_uno_roto_impide_done(self):
        llamados = []

        async def motores(ciclo, objetivo):
            llamados.append(ciclo)
            return {'total': 3, 'pass': 3, 'fallos': []}
        r = await self.gob(motores=motores).run({'objetivo': 'Crear evidencia real y verificarla'})
        self.assertEqual(r['status'], 'DONE_VERIFICADO', r)
        self.assertEqual(llamados, list(CICLOS))

        async def roto(ciclo, objetivo):
            return {'total': 3, 'pass': 2 if ciclo == 'C4_PREPARACION' else 3, 'fallos': ['x']}
        r = await self.gob(motores=roto).run({'objetivo': 'Crear evidencia real y verificarla'})
        self.assertEqual(r['status'], 'FALLO_VERIFICACION')
        self.assertFalse(next(c for c in r['ciclos'] if c['ciclo'] == 'C4_PREPARACION')['ok'])


if __name__ == '__main__':
    unittest.main()
