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
        return {'reply': json.dumps({'status': 'PASS' if ok else 'FAIL', 'evidencia': 'ok'})}
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


class CuerpoYMeta(unittest.TestCase):
    def test_la_fase_recibe_su_seccion_y_las_guias_META(self):
        m = _plugin()
        vistos = []
        m._chat_modelo = lambda modelo, prompt, sesion: (vistos.append(prompt), {'reply': json.dumps({'status': 'PASS', 'evidencia': 'ok'})})[1]
        asyncio.run(m._ejecutar_skill_motor('verification-loop', {'task_id': 'T1'}))
        fase_build = next(p for p in vistos if 'Build Verification' in p.split('\n')[0])
        self.assertIn('[INSTRUCCIONES DE ESTA FASE]', fase_build)
        self.assertIn('npm run build', fase_build)            # texto real del SKILL.md, no solo el titulo
        self.assertIn('After completing a feature', fase_build)  # guia META ("When to Use") inyectada

    def test_pass_sin_evidencia_o_sin_json_es_fail(self):
        m = _plugin()
        for reply in ('todo bien', '{"status":"PASS"}', '{"status":"PASS","evidencia":"  "}'):
            m._chat_modelo = lambda modelo, prompt, sesion, r=reply: {'reply': r}
            r = asyncio.run(m._ejecutar_skill_motor('ck', {'task_id': 'T1'}))
            self.assertFalse(r['ok'], reply)

    def test_ningun_motor_pierde_texto_en_sus_fases(self):
        m = _plugin()
        vacias = []
        for sid, spec in m._catalogo_ecc().items():
            sec = m._secciones(sid)
            vacias += [(sid, f['phase_id']) for f in spec['phases'] if not sec.get(f['phase_id'], (0, ''))[1]]
        self.assertEqual(vacias, [])
