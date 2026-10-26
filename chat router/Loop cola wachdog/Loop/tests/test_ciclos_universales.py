import asyncio, importlib.util, json, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _plugin():
    spec = importlib.util.spec_from_file_location('nct_plugin_cu', ROOT / 'plugin.py')
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _modelo(ok=True):
    def f(modelo, prompt, sesion):
        return {'reply': json.dumps({'status': 'PASS' if ok else 'FAIL'})}
    return f


class CiclosUniversales(unittest.TestCase):
    def test_skill_sin_verify_recibe_verify_universal(self):
        m = _plugin(); m._chat_modelo = _modelo()
        r = asyncio.run(m._ejecutar_skill_motor('ck', {'task_id': 'T1'}))
        self.assertEqual(r['status'], 'PASS', r)
        self.assertEqual(r['verify']['origen'], 'universal')
        self.assertTrue(r['verify']['ok'])

    def test_main_fallido_dispara_recovery_universal_y_no_finge_pass(self):
        m = _plugin(); m._chat_modelo = _modelo(ok=False)
        r = asyncio.run(m._ejecutar_skill_motor('ck', {'task_id': 'T1'}))
        self.assertFalse(r['ok'], r)
        self.assertEqual(r['recovery']['origen'], 'universal')
        self.assertEqual(r['recovery']['intentos'], 1)

    def test_todos_los_skills_tienen_verify_y_recovery(self):
        m = _plugin(); m._chat_modelo = _modelo()
        malos = []
        for sid in sorted(m._catalogo_ecc()):
            r = asyncio.run(m._ejecutar_skill_motor(sid, {'task_id': 'T1'}))
            if r.get('status') != 'PASS' or not r.get('verify'):
                malos.append(sid)
        self.assertEqual(malos, [])


if __name__ == '__main__':
    unittest.main()
