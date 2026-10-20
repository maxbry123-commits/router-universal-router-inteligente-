"""PARCHE_UPDATER / documento 3 (tests 2, 3 y 7), offline: capacidad POR NODO en la ficha 2.
 T2: el escritor N4 con tarea aprobada recibe github_escribir en su catalogo; los nodos de lectura no.
 T3: N4 lleva cap_tools='write'; los demas nodos 'read' o 'none'.
 T7: una escritura desde un nodo que no es N4 queda bloqueada (segunda puerta del Harness).
Ejecutar:  python3 -I plugins/fichas_qwen/tests/test_contrato_nodo_ficha2.py"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import plugins.fichas_qwen.plugin as fq  # noqa: E402
import plugins.puente_chat.plugin as pcm  # noqa: E402
from plugins.puente_chat import capacidad as cap  # noqa: E402
from plugins.puente_chat import herramientas as H  # noqa: E402

CAPT = []


class _FakePC:
    FICHAS = {'qw-qwen-3-8-max': ('x', 'x', 'Qwen 3.8 Max', 60)}

    @staticmethod
    def _chat(p):
        CAPT.append(p)
        return {'choices': [{'message': {'content': 'ok'}}], 'constitucion': None}


fq._pc = lambda: _FakePC
FICHA = dict(fq.FICHAS['ficha2-dag-codigo'])
NODOS = [n for n in FICHA['nodos'] if n.get('tipo') != 'goals']  # los 'goals' son datos: no llaman a ningun modelo


def _payload(nodo, **o):
    CAPT.clear()
    opts = {'fid': 'ficha2-dag-codigo', 'cap_in': 'write', 'sesion': 't', 'tarea_id': 'T1', 'aprobado': True, 'muta': True}
    opts.update(o)
    n = dict(nodo)
    n.setdefault('timeout_s', 30)
    try:
        fq._llamar_harness_1('ficha-qwen38max', 'hola', FICHA, n, opts)
    except RuntimeError as e:  # el fake no ejecuta herramientas: EJECUCION_SIN_EVIDENCIA es lo correcto para el escritor
        assert 'SIN_EVIDENCIA' in str(e), e
    return CAPT[-1]


def _nombres(cat):
    return {(t.get('function') or {}).get('name') for t in (cat or [])}


class Contrato(unittest.TestCase):
    def test_ficha2_tiene_a_N4_y_revisores(self):
        ids = {n['id'] for n in NODOS}
        self.assertIn('N4', ids); self.assertTrue({'N6', 'N7'} <= ids)

    def test_T2_catalogo_N4_incluye_github_escribir_y_lectura_no(self):
        for n in NODOS:
            p = _payload(n)
            cat = cap.catalogo_para(p['cap_tools'], H.TOOLS)
            if n['id'] == 'N4':
                self.assertIn('github_escribir', _nombres(cat), 'N4 aprobado debe recibir github_escribir')
                self.assertEqual(p['tools_habilitadas'], True)
            else:
                self.assertNotIn('github_escribir', _nombres(cat), n['id'])
                self.assertNotIn('hf_escribir', _nombres(cat), n['id'])

    def test_T2_el_puente_aplica_el_cap_del_payload(self):
        # el cap por nodo viaja en el payload y puente_chat lo toma de ahi (no del input global)
        src = (Path(pcm.__file__)).read_text(encoding='utf-8')
        self.assertIn("_CAP_TOOLS.set(str(p.get('cap_tools') or 'write'))", src)
        self.assertIn('tools_vis = _catalogo_para(_CAP_TOOLS.get(), h.TOOLS)', src)

    def test_T2_sin_aprobacion_N4_no_recibe_escritura(self):
        n4 = next(n for n in NODOS if n['id'] == 'N4')
        p = _payload(n4, aprobado=False)
        self.assertNotIn('github_escribir', _nombres(cap.catalogo_para(p['cap_tools'], H.TOOLS)))

    def test_T3_cap_por_nodo(self):
        for n in NODOS:
            p = _payload(n)
            if n['id'] == 'N4':
                self.assertEqual(p['cap_tools'], 'write')
            else:
                self.assertIn(p['cap_tools'], ('read', 'none'), n['id'])
                self.assertTrue(p['solo_lectura'], n['id'])

    def test_T7_escritura_desde_nodo_que_no_es_N4_bloqueada(self):
        args = {'repo': 'maxbry123-commits/x', 'ruta': 'a.txt', 'contenido': 'x'}
        for n in NODOS:
            p = _payload(n)
            tok = pcm._SOLO_LECTURA.set(bool(p['solo_lectura']))
            try:
                r = pcm._bloqueo('github_escribir', args)
            finally:
                pcm._SOLO_LECTURA.reset(tok)
            if n['id'] == 'N4':
                self.assertEqual(r, '', 'el escritor aprobado no debe estar bloqueado')
            else:
                self.assertIn('GAP_MUTACION_NO_AUTORIZADA', r, n['id'])

    def test_T7_nodo_revisor_con_escribe_true_declarado_sin_aprobacion_no_escribe(self):
        p = _payload({'id': 'N6', 'escribe': True}, aprobado=False)
        self.assertTrue(p['solo_lectura']); self.assertNotEqual(p['cap_tools'], 'write')


if __name__ == '__main__':
    unittest.main()
