import unittest
import rules_engine as R


class TestRulesEngine(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.reglas = R.load_rules('prompt_rules.yaml')

    def test_carga_87_reglas_ordenadas(self):
        self.assertEqual(len(self.reglas), 87)
        self.assertEqual([r['orden'] for r in self.reglas], sorted(r['orden'] for r in self.reglas))

    def test_kinds_esperados(self):
        self.assertEqual(len(R.listar_ids(self.reglas, 'patch')), 56)
        self.assertEqual(len(R.listar_ids(self.reglas, 'meta_patch')), 30)
        self.assertEqual(len(R.listar_ids(self.reglas, 'prompt_block')), 1)

    def test_build_system_subset_fail_closed(self):
        b = R.build_system(self.reglas, ids=['deep-reasoning', 'test-suite'])
        self.assertIn('edge cases', b.lower())
        with self.assertRaises(R.RulesError):
            R.build_system(self.reglas, ids=['no-existe'])

    def test_sin_ids_devuelve_todo(self):
        b = R.build_system(self.reglas, con_ids=False)
        for r in self.reglas:
            self.assertIn(r['contenido'][:60], b)


if __name__ == '__main__':
    unittest.main()
