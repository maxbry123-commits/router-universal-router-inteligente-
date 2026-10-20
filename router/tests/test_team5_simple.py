"""Team 5 CAP_NONE: 1 sola llamada directa, en stream, sin tools/anexo/sentinela, tope 30 s, reasoning low."""
import plugins.fichas_qwen.mvp as mvp


class _PC:
    FICHAS = {'qw-38max': (None, 'qwencloud', 'qwen3.8-max', 120)}
    def __init__(self, k='sk-sp-x', u='https://token-plan.x/v1'):
        self.k, self.u, self.calls = k, u, []
    def _qwen_conf(self):
        return self.k, self.u
    def _chat(self, p):
        self.calls.append(p)
        return {'choices': [{'message': {'content': 'Soy Qwen 3.8 Max'}}]}


class _FQ:
    FICHAS = {'ficha1-modelos': {'selector': [{'id': 'ficha-qwen38max', 'nombre': 'Qwen 3.8 Max'}]}}
    _QW = {'ficha-qwen38max': 'qw-38max'}
    _NOTAS, _CANCEL = {}, set()
    def __init__(self, pc): self.pc = pc
    def _elegido(self, sel, m): return 'ficha-qwen38max'
    def _pc(self): return self.pc
    def _prog(self, *a): pass
    def _meta(self, *a): pass


def _run(monkeypatch, pc, msg):
    monkeypatch.setattr(mvp, '_fq', lambda: _FQ(pc))
    return mvp.chat({'modelo': 'ficha-qwen38max', 'anclados': ['x']}, {}, msg, 's', 0.0)


def test_simple_directo(monkeypatch):
    pc = _PC()
    r = _run(monkeypatch, pc, 'Que modelo eres')
    assert r['reply'] and len(pc.calls) == 1
    c = pc.calls[0]
    assert c['directo'] and c['presupuesto_s'] <= 30 and c['tools_habilitadas'] is False
    assert c['anclados'] == [] and c['extra_llm'] == {'reasoning_effort': 'low'} and c['stream_fn']


def test_gap_token_plan_instantaneo(monkeypatch):
    pc = _PC(k='sk-otro')
    r = _run(monkeypatch, pc, 'Que modelo eres')
    assert r['error'].startswith('GAP TOKEN_PLAN') and not pc.calls
