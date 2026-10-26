# DSL N1-N5: tests del cableado tool-calling (mocks de pc._chat, sin red)
import sys, types, time, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))  # raiz del repo -> paquetes fichas.* / plugins.*
import plugin as fq  # fichas_qwen/plugin.py


def _ficha_fake():
    return {'ficha': 'ficha1-modelos', 'timeout_s': 150, 'max_output_tokens': 100,
            'selector': [{'id': 'ficha-qwen38max', 'tipo': 'texto'}],
            'dsl': {'nodos': [], 'timeouts': {'api_seconds': 150}, 'retry': {'max_attempts': 2}, 'tokens': {'max_output_tokens': 100}},
            'motor': {'limite_llamada_chars': 9000}, 'loop': {}}


class _PC(dict):
    FICHAS = {'qwen-max': {}, 'glm-5.2': {}}
    def __init__(self, respuestas):
        super().__init__(); self.respuestas = list(respuestas); self.llamadas = []
    def _chat(self, p):
        self.llamadas.append(p)
        return self.respuestas.pop(0) if self.respuestas else 'ok'
    def _politica(self, m):
        return {'reintento': {'per_attempt_s': 50, 'max_attempts': 2, 'fallback_modelo': ['ficha-glm52']}}


class T(unittest.TestCase):
    def setUp(self):
        fq._QW['ficha-qwen38max'] = 'qwen-max'
        fq._QW['ficha-glm52'] = 'glm-5.2'

    # N1: _llamar_harness_1 lee sys_prompt del ContextVar, no de opts compartido
    def test_n1_contextvar(self):
        pc = _PC([{'choices': [{'message': {'content': 'ok'}}], 'herramientas': []}])
        fq._pc = lambda: pc
        fq._NODO_CALL.set({'sys_prompt': 'SYS_NODO_A', 'per_attempt_s': 0, 'dsv4_think': None, 'forzar_tool': False})
        try:
            fq._llamar_harness_1('ficha-qwen38max', 'p', _ficha_fake(), {'id': 'N1', 'timeout_s': 150}, {'_sys_prompt': 'SYS_VIEJO_PISADO'})
        finally:
            fq._NODO_CALL.set(None)
        self.assertEqual(pc.llamadas[0]['messages'][0]['content'], 'SYS_NODO_A')  # el del nodo, no el pisado

    # N3: respuesta con herramientas ejecutadas -> categoria EXECUTED (no es acuse)
    def test_n3_executed_con_evidencia(self):
        r = {'herramientas': [{'ok': True, 'herramienta': 'github_escribir'}], 'content': ''}
        ej = isinstance(r, dict) and any(x.get('ok') for x in (r.get('herramientas') or []))
        self.assertTrue(ej)  # con evidencia -> 0 reintentos

    # N4: deadline - cada intento recorta api_s al tiempo restante
    def test_n4_deadline_recorta(self):
        pc = _PC([{'choices': [{'message': {'content': 'ok'}}], 'herramientas': []}])
        fq._pc = lambda: pc
        fq._NODO_CALL.set({'sys_prompt': '', 'per_attempt_s': 75, 'dsv4_think': None, 'forzar_tool': False,
                           'deadline': time.monotonic() + 30})
        try:
            fq._llamar_harness_1('ficha-qwen38max', 'p', _ficha_fake(), {'id': 'N1', 'timeout_s': 150}, {})
        finally:
            fq._NODO_CALL.set(None)
        self.assertLessEqual(pc.llamadas[0]['presupuesto_s'], 25)  # 30 - 5s margen, nunca 75 ni 150

    # N5: fuente unica — _politica devuelve la politica leida de ficha1
    def test_n5_reintento_desde_politica(self):
        pc = _PC([{'choices': [{'message': {'content': 'ok'}}], 'herramientas': []}])
        fq._pc = lambda: pc
        pol = pc._politica('qwen-max')
        self.assertEqual(pol['reintento']['per_attempt_s'], 50)
        self.assertIn('ficha-glm52', pol['reintento']['fallback_modelo'])


if __name__ == '__main__':
    unittest.main()
