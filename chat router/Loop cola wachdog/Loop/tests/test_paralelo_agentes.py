import importlib.util, json, tempfile, time, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _cargar():
    spec = importlib.util.spec_from_file_location('nct_plugin_par', ROOT / 'plugin.py')
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


class ParaleloAgentes(unittest.TestCase):
    def test_espejo_de_agentes(self):
        r = _cargar().handle('agentes', {})
        self.assertGreater(r['total'], 40)
        ids = {a['id'] for a in r['agentes']}
        self.assertTrue({'qwen3.8-max', 'glm-5.3', 'deepseek-v4-pro', 'claude-code', 'OpenHands'} <= ids)
        solo = _cargar().handle('agentes', {'tipo': 'modelo'})
        self.assertTrue(all(a['tipo'] == 'modelo' for a in solo['agentes']))

    def test_paralelo_acepta_hasta_4_y_rechaza_5(self):
        m = _cargar()
        self.assertIn('error', m.handle('paralelo', {'objetivos': ['x'] * 5}))
        self.assertIn('error', m.handle('paralelo', {'objetivos': []}))

    def test_cuatro_procesos_en_paralelo_completan(self):
        from nct_loop.ports import DemoModel
        m = _cargar()
        prop = json.loads((ROOT / 'examples/mock_proposals.json').read_text())
        mision = json.loads((ROOT / 'examples/mission_smoke.json').read_text())
        with tempfile.TemporaryDirectory() as t:
            t = Path(t)
            m._WS_ROOT, m._MEM = t / 'ws', t / 'mem'
            m._PuertoModelo = lambda modelo, sesion: DemoModel(prop)
            objs = [{'objetivo': 'Crear evidencia %d y verificarla en el workspace' % i,
                     'mision': dict(mision, mission_id='PAR_%d' % i)} for i in range(4)]
            g = m.handle('paralelo', {'objetivos': objs})
            self.assertEqual(len(g['procesos']), 4)
            for _ in range(200):
                e = m.handle('estado_paralelo', {'grupo_id': g['grupo_id']})
                if e['estado'] == 'completado':
                    break
                time.sleep(0.1)
            self.assertEqual(e['estado'], 'completado', e)
            self.assertEqual([x['resultado']['status'] for x in e['procesos']], ['DONE_VERIFICADO'] * 4, e)


if __name__ == '__main__':
    unittest.main()
