"""Pruebas offline del ejemplo. No prueban la integración con el Router/Harness."""
import copy
import tempfile
import unittest
from pathlib import Path
from motor_cli import Motor

POLICY = {'allowed_ops': ['inspect_workspace', 'create_directory', 'write_text', 'read_text', 'verify_exists', 'verify_contains', 'finish'], 'max_ops': 32}

class TestMotor(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.engine = Motor(self.root, POLICY)

    def tearDown(self):
        self.temp.cleanup()

    def test_smoke(self):
        commands = [
          {'id':'a','op':'create_directory','path':'x'},
          {'id':'b','op':'write_text','path':'x/a.txt','text':'hola','depends_on':['a']},
          {'id':'c','op':'verify_contains','path':'x/a.txt','text':'hola','depends_on':['b']}]
        result = self.engine.run({'ops':commands})
        self.assertTrue(result['ok'], result['errors'])
        self.assertEqual(result['ops_executed'],3)

    def test_unknown_op(self):
        self.assertFalse(self.engine.run({'ops':[{'id':'a','op':'exec'}]})['ok'])

    def test_cycle(self):
        self.assertFalse(self.engine.run({'ops':[{'id':'a','op':'finish','depends_on':['b']},{'id':'b','op':'finish','depends_on':['a']}]})['ok'])

    def test_escape(self):
        self.assertFalse(self.engine.run({'ops':[{'id':'a','op':'write_text','path':'../bad.txt','text':'x'}]})['ok'])

    def test_protect_existing(self):
        (self.root/'a.txt').write_text('original')
        self.assertFalse(self.engine.run({'ops':[{'id':'a','op':'write_text','path':'a.txt','text':'otro'}]})['ok'])
        self.assertEqual((self.root/'a.txt').read_text(),'original')

    def test_unmet_dependency(self):
        self.assertFalse(self.engine.run({'ops':[{'id':'a','op':'finish','depends_on':['missing']}]})['ok'])

    def test_reordered_execution(self):
        plan = {'ops':[{'id':'b','op':'verify_exists','path':'x.txt','depends_on':['a']},{'id':'a','op':'write_text','path':'x.txt','text':'x'}]}
        result = self.engine.run(copy.deepcopy(plan))
        self.assertTrue(result['ok'])
        self.assertEqual([r['id'] for r in result['receipts']], ['a','b'])

# >>> PREFLIGHT_RB <<< 5 pruebas del motor YAIWES (validacion estricta, preflight, finish, lock): 7 + 5 = 12
from yaiwes_motor import MotorYaiwes  # noqa: E402


class TestMotorYaiwesEstricto(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def _run(self, ops):
        return MotorYaiwes(self.root, POLICY, 't').run({'meta': {'name': 't'}, 'ops': ops})

    def test_campo_desconocido_rechazado(self):
        r = self._run([{'id': 'a', 'op': 'write_text', 'path': 'x.txt', 'text': 'x', 'modo': 'forzar'}])
        self.assertFalse(r['ok'])
        self.assertIn('GAP_CAMPO_DESCONOCIDO', r['errors'][0]['message'])

    def test_preflight_no_ejecuta_nada_si_un_nodo_es_invalido(self):
        r = self._run([{'id': 'a', 'op': 'write_text', 'path': 'ok.txt', 'text': 'x'},
                       {'id': 'b', 'op': 'write_text', 'path': '../fuera.txt', 'text': 'x', 'depends_on': ['a']}])
        self.assertFalse(r['ok'])
        self.assertEqual(r['ops_executed'], 0)
        self.assertFalse((self.root / 'ok.txt').exists())

    def test_tipo_incorrecto_rechazado(self):
        self.assertFalse(self._run([{'id': 'a', 'op': 'write_text', 'path': 'x.txt', 'text': 123}])['ok'])

    def test_finish_debe_depender_de_todo(self):
        r = self._run([{'id': 'a', 'op': 'create_directory', 'path': 'd'},
                       {'id': 'b', 'op': 'inspect_workspace'},
                       {'id': 'f', 'op': 'finish', 'depends_on': ['a']}])
        self.assertFalse(r['ok'])
        self.assertIn('GAP_FINISH_SIN_DEPENDENCIAS', r['errors'][0]['message'])
        ok = self._run([{'id': 'a', 'op': 'create_directory', 'path': 'd'},
                        {'id': 'f', 'op': 'finish', 'depends_on': ['a']}])
        self.assertTrue(ok['ok'], ok['errors'])
        self.assertTrue(ok['batch_finished'])
        self.assertFalse(ok['objective_audited'])

    def test_checkpoint_idempotente_y_lock(self):
        ops = [{'id': 'a', 'op': 'write_text', 'path': 'x.txt', 'text': 'hola'}, {'id': 'f', 'op': 'finish', 'depends_on': ['a']}]
        r1 = self._run(ops)
        r2 = self._run(ops)
        self.assertTrue(r1['ok'] and r2['ok'])
        self.assertTrue(r2['receipts'][0]['reutilizado'])
        import yaiwes_motor as ym
        lk = ym._bloqueo_archivo(self.root / '.receipts' / 't.lock')
        try:
            r3 = self._run(ops)
            if lk is not None:
                self.assertFalse(r3['ok'])
                self.assertIn('GAP_PLAN_EN_EJECUCION', r3['errors'][0]['message'])
        finally:
            ym._soltar(lk)


if __name__ == '__main__':
    unittest.main(verbosity=2)
