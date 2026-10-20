"""PARCHE_VERIF: un exito de escritura solo cuenta si GitHub devuelve commit Y la relectura coincide (caso Qwen: dijo escribir y no habia nada).
Ejecutar: python3 -I fichas/fichas_qwen/tests/test_parche_verif.py"""
import base64, sys, unittest
from pathlib import Path
P = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(P.parent / 'plugins' / 'puente_chat'))
import herramientas as H


def _b64(t):
    return base64.b64encode(t.encode()).decode()


class Verif(unittest.TestCase):
    def setUp(self):
        self._o = H._gh

    def tearDown(self):
        H._gh = self._o

    def _gh(self, put=(201, {'commit': {'sha': 'abcdef1234567890'}}), get_tras=None, guardar=True):
        est = {'c': None}

        def gh(m, ruta, cuerpo=None):
            if m == 'PUT':
                if guardar:
                    est['c'] = base64.b64decode(cuerpo['content']).decode()
                est['puts'] = est.get('puts', 0) + 1
                return put
            if est.get('puts') and get_tras is not None:
                return get_tras
            if est['c'] is None:
                return 404, {}
            return 200, {'content': _b64(est['c']), 'encoding': 'base64', 'sha': 's'}
        H._gh = gh

    def test_ok_con_relectura(self):
        self._gh()
        r = H.github_escribir(dict(ruta='a.txt', contenido='hola', rama='r1'))
        self.assertTrue(r.startswith('OK commit abcdef1234'), r)
        for t in ('rama=r1', 'ruta=a.txt', 'verificado=relectura', 'total=4'):
            self.assertIn(t, r)

    def test_put_ok_sin_sha_de_commit_no_es_exito(self):
        self._gh(put=(200, {'commit': {}}))
        self.assertIn('SIN_SHA_DE_COMMIT', H.github_escribir(dict(ruta='a.txt', contenido='x')))

    def test_relectura_404_no_es_exito(self):  # escribio en otro sitio: la rama pedida no tiene el archivo
        self._gh(get_tras=(404, {}))
        r = H.github_escribir(dict(ruta='a.txt', contenido='x', rama='fichas-tareas-nuevas'))
        self.assertTrue(r.startswith('ERROR READBACK_NO_COINCIDE'), r)
        self.assertIn('rama=fichas-tareas-nuevas', r)

    def test_relectura_contenido_distinto_no_es_exito(self):
        self._gh(get_tras=(200, {'content': _b64('otra cosa'), 'encoding': 'base64', 'sha': 's'}))
        self.assertTrue(H.github_escribir(dict(ruta='a.txt', contenido='x')).startswith('ERROR READBACK_NO_COINCIDE'))

    def test_archivo_grande_compara_blob_sha(self):
        import hashlib
        c = 'é' * 10
        b = c.encode()
        sha = hashlib.sha1(b'blob %d\0' % len(b) + b).hexdigest()
        self._gh(get_tras=(200, {'content': '', 'encoding': 'none', 'sha': sha}))
        self.assertTrue(H.github_escribir(dict(ruta='a.txt', contenido=c)).startswith('OK commit'))
        self._gh(get_tras=(200, {'content': '', 'encoding': 'none', 'sha': 'x' * 40}))
        self.assertTrue(H.github_escribir(dict(ruta='a.txt', contenido=c)).startswith('ERROR READBACK'))

    def test_error_de_put_se_conserva(self):
        self._gh(put=(422, {'message': 'mal'}))
        self.assertTrue(H.github_escribir(dict(ruta='a.txt', contenido='x')).startswith('ERROR 422'))

    def test_sin_pat_con_push_mensaje_explicito(self):
        H._gh = self._o
        oll, opet, ores = H._llaves, H._peticion, H._resolver_repo
        H._llaves = lambda *a, **k: ['k1', 'k2']
        H._resolver_repo = lambda n: n
        H._peticion = lambda *a, **k: (403, {'message': 'Resource not accessible'})
        try:
            s, d = H._gh('PUT', '/repos/maxbry123-commits/r/contents/a.txt', {'content': 'eA=='})
        finally:
            H._llaves, H._peticion, H._resolver_repo = oll, opet, ores
        self.assertEqual(s, 403)
        self.assertIn('SIN_PAT_CON_PUSH', d)


class NotaNodoLectura(unittest.TestCase):
    def test_nota_para_nodos_de_lectura_va_antes_del_bloque_del_escritor(self):
        src = (P / 'fichas_qwen' / 'plugin.py').read_text(encoding='utf-8')
        i = src.index('nodo de lectura): tu nodo no escribe')
        j = src.index("PUBLICAR: para crear o cambiar archivos")
        self.assertLess(i, j)
        self.assertIn("n.get('id') not in ('N4', 'P3')", src[i - 400:i])
        self.assertIn('NO es un gap', src[i:i + 300])


if __name__ == '__main__':
    unittest.main()
