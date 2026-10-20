"""PARCHE_GH_URL_ENC: github_api con espacios, acentos y emoji no revienta con InvalidURL."""
import http.client, sys, unittest
from pathlib import Path
P = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(P.parent / 'plugins' / 'puente_chat'))
sys.path.insert(0, str(P / 'fichas_qwen'))
import herramientas as H


class T(unittest.TestCase):
    def test_espacios_y_emoji(self):
        r = H._ruta_gh_codificada('/repos/x/y/contents/router inteligente universal/\U0001F4CCa promt.md?ref=feat/m')
        self.assertNotIn(' ', r)
        self.assertTrue(r.isascii())
        http.client.HTTPConnection('x')._validate_path('GET ' + r if False else r)

    def test_idempotente(self):
        a = H._ruta_gh_codificada('/a b/\u00e9')
        self.assertEqual(a, H._ruta_gh_codificada(a))

    def test_bypass_punto_punto_codificado(self):
        s, d = H._gh('GET', '/repos/maxbry123-commits/x/%2e%2e/%2e%2e/y')
        self.assertEqual(s, 0)
        self.assertIn('no permitida', d)


if __name__ == '__main__':
    unittest.main()
