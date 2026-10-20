"""PARCHE_500K: escritura por partes hasta 500000 caracteres + auditoria (PARCHE_AUD)."""
import base64, json, sys, unittest
from pathlib import Path
P = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(P.parent / 'plugins' / 'puente_chat'))
sys.path.insert(0, str(P / 'fichas_qwen'))
import herramientas as H


class T(unittest.TestCase):
    def setUp(self):
        self.f = {}
        def gh(m, ruta, cuerpo=None):
            if m == 'GET':
                if 'x.py' in self.f:
                    return 200, {'content': base64.b64encode(self.f['x.py'].encode()).decode(), 'encoding': 'base64', 'sha': 's'}
                return 404, {}
            self.f['x.py'] = base64.b64decode(cuerpo['content']).decode()
            return 200, {'commit': {'sha': 'abcdef1234567890'}}
        self._o = H._gh
        H._gh = gh

    def tearDown(self):
        H._gh = self._o

    def w(self, c, **k):
        return H.github_escribir(dict(ruta='x.py', contenido=c, **k))

    def test_500k_en_25_partes(self):
        n = 0
        for i in range(25):
            r = self.w('a' * 20000, anexar=True, offset=n)
            self.assertTrue(r.startswith('OK commit'), r)
            n += 20000
        self.assertEqual(len(self.f['x.py']), 500000)
        self.assertIn('total=500000', r)

    def test_offset_erroneo(self):
        self.w('abc')
        r = self.w('d', anexar=True, offset=1)
        self.assertIn('OFFSET_DISTINTO', r)
        self.assertEqual(self.f['x.py'], 'abc')

    def test_excede_tope(self):
        self.w('a' * 499990)
        r = self.w('b' * 20, anexar=True, offset=499990)
        self.assertIn('ARCHIVO_EXCEDE', r)
        self.assertEqual(len(self.f['x.py']), 499990)

    def test_sobrescribir_sigue(self):
        self.w('uno')
        self.assertTrue(self.w('dos').startswith('OK commit'))
        self.assertEqual(self.f['x.py'], 'dos')

    def test_esquema(self):
        s = json.dumps(H.TOOLS, default=str)
        self.assertIn('anexar', s)
        self.assertIn('offset', s)

    def test_fichas_json(self):
        for n in ('ficha1-modelos', 'ficha2-dag-codigo', 'ficha3-frontend', 'ficha4-workflow-yaiwes'):
            d = json.loads((P / 'fichas_qwen' / 'fichas' / (n + '.json')).read_text(encoding='utf-8'))
            self.assertIn('"max_partes_codigo": 40', json.dumps(d, indent=1).replace('": 40', '": 40'))


if __name__ == '__main__':
    unittest.main()
