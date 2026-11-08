import copy
import tempfile
import unittest
from pathlib import Path
from persistence_engine import validate, operate

POLICY = {'allowed_ops': ['inspect_workspace', 'create_directory', 'write_text', 'read_text', 'verify_exists', 'verify_contains', 'finish'], 'max_ops': 32}

class TestMotor(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def test_smoke(self):
        commands = [
          {'id':'a','op':'create_directory','path':'x'},
          {'id':'b','op':'write_text','path':'x/a.txt','text':'hola','depends_on':['a']},
          {'id':'c','op':'verify_contains','path':'x/a.txt','text':'hola','depends_on':['b']}]
        result = validate({'ops':commands}, POLICY)
        self.assertEqual(len(result[1]), 3)

    def test_unknown_op(self):
        with self.assertRaises(ValueError):
            validate({'ops':[{'id':'a','op':'exec'}]}, POLICY)

    def test_cycle(self):
        with self.assertRaises(ValueError):
            validate({'ops':[{'id':'a','op':'finish','depends_on':['b']},{'id':'b','op':'finish','depends_on':['a']}]}, POLICY)

if __name__ == '__main__':
    unittest.main()
