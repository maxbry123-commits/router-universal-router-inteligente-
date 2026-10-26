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


class Mirrors(unittest.TestCase):
    def _plugin_tmp(self, t):
        m = _cargar()
        m._STATE = Path(t)
        return m

    def test_hermes_y_openclaw_estan_espejados_con_fork_y_upstream(self):
        with tempfile.TemporaryDirectory() as t:
            m = self._plugin_tmp(t)
            for aid in ('hermes-agent', 'openclaw'):
                d = m.handle('mirror_listar', {'agente': aid})['detalle'][aid]
                tipos = {x['tipo'] for x in d}
                self.assertEqual(tipos, {'fork', 'upstream'})
                self.assertTrue(any(x['url'].startswith('https://github.com/maxbry123-commits/') for x in d))

    def test_todo_agente_puede_tener_varios_espejos(self):
        with tempfile.TemporaryDirectory() as t:
            m = self._plugin_tmp(t)
            for i in range(3):
                r = m.handle('mirror_agregar', {'agente': 'OpenHands', 'url': 'https://github.com/x/oh%d' % i, 'tipo': 'fork'})
                self.assertTrue(r['ok'], r)
            lista = m.handle('mirror_listar', {'agente': 'OpenHands'})['detalle']['OpenHands']
            self.assertEqual(len(lista), 1 + 3)  # local + 3 agregados
            self.assertEqual(lista[0]['tipo'], 'local')
            visto = [a for a in m.handle('agentes', {})['agentes'] if a['id'] == 'OpenHands'][0]
            self.assertEqual(len(visto['mirrors']), 4)

    def test_rechaza_url_ajena_repetida_y_agente_inexistente(self):
        with tempfile.TemporaryDirectory() as t:
            m = self._plugin_tmp(t)
            self.assertIn('error', m.handle('mirror_agregar', {'agente': 'OpenHands', 'url': 'http://evil.com/a/b'}))
            self.assertIn('error', m.handle('mirror_agregar', {'agente': 'OpenHands', 'url': 'https://github.com/a/b/../c'}))
            self.assertIn('error', m.handle('mirror_agregar', {'agente': 'NoExiste', 'url': 'https://github.com/a/b'}))
            m.handle('mirror_agregar', {'agente': 'OpenHands', 'url': 'https://github.com/a/b'})
            self.assertEqual(m.handle('mirror_agregar', {'agente': 'OpenHands', 'url': 'https://github.com/a/b'})['error'], 'ESPEJO_REPETIDO')

    def test_quitar_solo_los_agregados_y_tope_de_diez(self):
        with tempfile.TemporaryDirectory() as t:
            m = self._plugin_tmp(t)
            r = m.handle('mirror_agregar', {'agente': 'OpenHands', 'url': 'https://github.com/a/b'})
            self.assertTrue(m.handle('mirror_quitar', {'agente': 'OpenHands', 'mirror_id': r['mirror']['id']})['ok'])
            self.assertIn('error', m.handle('mirror_quitar', {'agente': 'OpenHands', 'mirror_id': 'local'}))
            for i in range(9):
                self.assertTrue(m.handle('mirror_agregar', {'agente': 'OpenHands', 'url': 'https://github.com/a/r%d' % i})['ok'])
            self.assertIn('maximo', m.handle('mirror_agregar', {'agente': 'OpenHands', 'url': 'https://github.com/a/z'})['error'])

    def test_sync_actualiza_sha_sin_clonar(self):
        with tempfile.TemporaryDirectory() as t:
            m = self._plugin_tmp(t)
            m._sha_remoto = lambda url, rama: 'abc123'
            r = m.handle('mirror_agregar', {'agente': 'OpenHands', 'url': 'https://github.com/a/b'})
            s = m.handle('mirror_sync', {'agente': 'OpenHands'})
            self.assertEqual(s['revisados'], 1)
            visto = m.handle('mirror_listar', {'agente': 'OpenHands'})['detalle']['OpenHands']
            self.assertEqual([x for x in visto if x['id'] == r['mirror']['id']][0]['sha'], 'abc123')
