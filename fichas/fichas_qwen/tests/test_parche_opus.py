# PARCHE_OPUS tests offline: balance de marcadores MODOS, registros sin placeholders, selector de modos sano.
import json
import os
import re
import sys
import unittest
from pathlib import Path

_FQ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_FQ / 'modos'))


def _balance(p):
    t = (_FQ / p).read_text(encoding='utf-8')
    return len(re.findall(r'>>>\s*MODOS BEGIN', t)), len(re.findall(r'<<<\s*MODOS END', t))


class T(unittest.TestCase):
    def test_marcadores_modos_balanceados(self):
        for f in ('plugin.py', 'mvp.py'):
            b, e = _balance(f)
            self.assertEqual(b, e, '%s BEGIN=%d END=%d' % (f, b, e))

    def test_registros_sin_placeholders(self):
        for f in ('modos/modes_registry.json', 'fichas/modes_registry.json'):
            self.assertNotIn('<EDITAR', (_FQ / f).read_text(encoding='utf-8'), f)

    def test_registros_mismos_modos(self):
        a = json.loads((_FQ / 'modos/modes_registry.json').read_text(encoding='utf-8'))
        b = json.loads((_FQ / 'fichas/modes_registry.json').read_text(encoding='utf-8'))
        self.assertEqual([m['id'] for m in a['modes']], [m['id'] for m in b['modes']])
        self.assertEqual(a['self_modification'], b['self_modification'])

    def test_validate_modes_y_router(self):
        cwd = os.getcwd()
        os.chdir(str(_FQ / 'modos'))  # test_mode_router lee modes_registry.json relativo al importarse
        try:
            import validate_modes as vm
            import test_mode_router as tm
            suite = unittest.defaultTestLoader.loadTestsFromModule(tm)
            res = unittest.TextTestRunner(stream=open(os.devnull, 'w'), verbosity=0).run(suite)
        finally:
            os.chdir(cwd)
        self.assertTrue(res.wasSuccessful())
        self.assertTrue(callable(getattr(vm, 'main', None)))


if __name__ == '__main__':
    r = unittest.main(exit=False, verbosity=0).result
    print('PARCHE_OPUS PASS' if r.wasSuccessful() else 'PARCHE_OPUS FAIL')
    sys.exit(0 if r.wasSuccessful() else 1)
