import importlib.util, json, tempfile, time, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _cargar():
    spec = importlib.util.spec_from_file_location('nct_plugin_gob', ROOT / 'plugin.py')
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


class PluginGobernarTests(unittest.TestCase):
    def test_gobernar_recorre_c0_a_c7(self):
        from nct_loop.ports import DemoModel
        m = _cargar()
        prop = json.loads((ROOT / 'examples/mock_proposals.json').read_text())
        mision = json.loads((ROOT / 'examples/mission_smoke.json').read_text())
        with tempfile.TemporaryDirectory() as t:
            t = Path(t)
            m._WS_ROOT, m._MEM = t / 'ws', t / 'mem'
            m._PuertoModelo = lambda modelo, sesion: DemoModel(prop)
            r = m.handle('gobernar', {'objetivo': 'Crear evidencia real y verificarla en el workspace',
                                      'mision': mision})
            self.assertEqual(r['estado'], 'procesando')
            self.assertEqual(len(r['ciclos']), 8)
            for _ in range(100):
                e = m.handle('estado', {'proceso_id': r['proceso_id']})
                if e['estado'] != 'procesando':
                    break
                time.sleep(0.1)
            self.assertEqual(e['estado'], 'completado', e)
            self.assertEqual(e['resultado']['status'], 'DONE_VERIFICADO', e)
            self.assertEqual(e['resultado']['watchdog']['estado'], 'OK')

    def test_gobernar_sin_objetivo(self):
        self.assertIn('error', _cargar().handle('gobernar', {}))


if __name__ == '__main__':
    unittest.main()
