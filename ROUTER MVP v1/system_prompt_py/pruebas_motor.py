import tempfile
import unittest
import asyncio
from pathlib import Path
from persistence_engine import PersistenceEngine

POLICY = {'allowed_ops': ['inspect_workspace', 'create_directory', 'write_text', 'read_text', 'verify_exists', 'verify_contains', 'finish'], 'max_ops': 32, 'max_text_chars': 10000}

class TestMotor(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.engine = PersistenceEngine(self.root, POLICY)

    def tearDown(self):
        self.temp.cleanup()

    async def test_smoke(self):
        doc = {
            "meta": {"name": "test-smoke"},
            "ops": [
                {'id':'a','op':'create_directory','path':'x'},
                {'id':'b','op':'write_text','path':'x/a.txt','text':'hola','depends_on':['a']},
                {'id':'c','op':'verify_contains','path':'x/a.txt','text':'hola','depends_on':['b']}
            ]
        }
        result = await self.engine.run_async(doc)
        self.assertTrue(result["ok"])
        self.assertEqual(len(result["receipts"]), 3)

    async def test_unknown_op(self):
        doc = {"meta": {"name": "test-fail"}, "ops": [{'id':'a','op':'exec'}]}
        with self.assertRaises(ValueError):
            await self.engine.run_async(doc)

if __name__ == '__main__':
    unittest.main()
