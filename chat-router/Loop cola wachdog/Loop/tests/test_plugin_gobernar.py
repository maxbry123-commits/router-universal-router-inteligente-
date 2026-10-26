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
            m._chat_modelo = lambda modelo, prompt, sesion: {'reply': '{"status":"PASS","evidencia":"ok"}'}
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


class TodosLosMotoresCorren(unittest.TestCase):
    def _correr(self, chat):
        import json as _j
        from nct_loop.ports import DemoModel
        m = _cargar()
        prop = _j.loads((ROOT / 'examples/mock_proposals.json').read_text())
        mision = _j.loads((ROOT / 'examples/mission_smoke.json').read_text())
        self.t = tempfile.TemporaryDirectory()
        t = Path(self.t.name)
        m._WS_ROOT, m._MEM = t / 'ws', t / 'mem'
        m._PuertoModelo = lambda modelo, sesion: DemoModel(prop)
        m._chat_modelo = chat
        r = m.handle('gobernar', {'objetivo': 'Cualquier objetivo que no menciona ningun motor en particular', 'mision': mision})
        for _ in range(600):
            e = m.handle('estado', {'proceso_id': r['proceso_id']})
            if e['estado'] != 'procesando':
                break
            time.sleep(0.1)
        return m, e['resultado']

    def tearDown(self):
        getattr(self, 't', None) and self.t.cleanup()

    def test_los_311_motores_se_ejecutan_todos_sin_seleccion(self):
        m, res = self._correr(lambda modelo, prompt, sesion: {'reply': '{"status":"PASS","evidencia":"ok"}'})
        self.assertEqual(res['status'], 'DONE_VERIFICADO', {c['ciclo']: c.get('motores') for c in res['ciclos']})
        total = sum(c['motores']['total'] for c in res['ciclos'])
        ok = sum(c['motores']['pass'] for c in res['ciclos'])
        self.assertEqual((total, ok), (311, 311))
        self.assertEqual(total, len(m._registro_motores()))

    def test_un_motor_que_falla_deja_el_ciclo_en_rojo_y_no_hay_done(self):
        def chat(modelo, prompt, sesion):
            return {'reply': '{"status":"FAIL"}' if '[ECC accessibility ' in prompt else '{"status":"PASS","evidencia":"ok"}'}
        m, res = self._correr(chat)
        self.assertNotEqual(res['status'], 'DONE_VERIFICADO')
        malo = next(c for c in res['ciclos'] if c.get('motores') and 'accessibility' in c['motores']['fallos'])
        self.assertFalse(malo['ok'])
        self.assertEqual(res['watchdog']['estado'], 'ALERTA')
