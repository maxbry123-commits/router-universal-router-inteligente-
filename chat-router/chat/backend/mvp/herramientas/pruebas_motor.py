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

if __name__ == '__main__':
    unittest.main(verbosity=2)
