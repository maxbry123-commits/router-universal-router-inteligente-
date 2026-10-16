"""Fix A: Ficha 1 -> Qwen por SSE; _http_stream reconstruye content/tool_calls/reasoning_content."""
import importlib.util, json, sys, threading
from contextvars import copy_context
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
import pytest

BASE = Path(__file__).resolve().parents[1] / 'router inteligente universal'
sys.path[:0] = [str(BASE), str(BASE / 'plugins')]


def _load(nombre, rel):
    spec = importlib.util.spec_from_file_location(nombre, BASE / 'plugins' / rel)
    m = importlib.util.module_from_spec(spec); sys.modules[nombre] = m; spec.loader.exec_module(m); return m


pc = _load('fixa_puente_chat', 'puente_chat/plugin.py')
VISTOS = []
SSE = [
    {'choices': [{'delta': {'reasoning_content': 'Pienso '}}]},
    {'choices': [{'delta': {'reasoning_content': 'mucho.'}}]},
    {'choices': [{'delta': {'content': 'Soy '}}]},
    {'choices': [{'delta': {'content': 'Qwen.'}}]},
    {'choices': [{'delta': {'tool_calls': [{'index': 0, 'id': 'c1', 'function': {'name': 'buscar', 'arguments': '{"q":'}}]}}]},
    {'choices': [{'delta': {'tool_calls': [{'index': 0, 'function': {'arguments': '"x"}'}}]}}]},
    {'choices': [], 'usage': {'total_tokens': 7}},
]


class H(BaseHTTPRequestHandler):
    def log_message(self, *a): pass

    def do_POST(self):
        b = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
        VISTOS.append(b)
        if b.get('stream'):
            self.send_response(200); self.send_header('Content-Type', 'text/event-stream'); self.end_headers()
            for ev in SSE:
                self.wfile.write(b'data: ' + json.dumps(ev).encode() + b'\n\n')
            self.wfile.write(b'data: [DONE]\n\n')
        else:
            out = json.dumps({'choices': [{'index': 0, 'message': {'role': 'assistant', 'content': 'hola no-stream'}}]}).encode()
            self.send_response(200); self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(out))); self.end_headers(); self.wfile.write(out)


@pytest.fixture(scope='module')
def url():
    s = HTTPServer(('127.0.0.1', 0), H)
    threading.Thread(target=s.serve_forever, daemon=True).start()
    yield 'http://127.0.0.1:%d/v1' % s.server_port
    s.shutdown()


def test_http_stream_reconstruye(url):
    VISTOS.clear(); chunks = []
    s, d = pc._http_stream(url + '/chat/completions', 'k', {'model': 'qwen3.8-max', 'messages': []}, 10, chunks.append)
    m = d['choices'][0]['message']
    assert s == 200 and VISTOS[0]['stream'] is True
    assert m['content'] == 'Soy Qwen.' and chunks == ['Soy ', 'Qwen.']
    assert m['reasoning_content'] == 'Pienso mucho.'
    assert m['tool_calls'][0]['function'] == {'name': 'buscar', 'arguments': '{"q":"x"}'}
    assert d['usage']['total_tokens'] == 7


def _api(proveedor, modelo, sf):
    def run():
        pc._STREAM_FN.set(sf)
        return pc._llamar_api(proveedor, modelo, [{'role': 'user', 'content': 'hola'}], 50, 20, None)
    return copy_context().run(run)


def test_qwencloud_con_stream_fn_usa_sse(url, monkeypatch):
    VISTOS.clear()
    monkeypatch.setattr(pc, '_qwen_conf', lambda: ('sk-sp-fake', url))
    s, d = _api('qwencloud', 'qwen3.8-max', lambda c: None)
    assert VISTOS and all(v.get('stream') is True for v in VISTOS)
    assert d['choices'][0]['message']['content'] == 'Soy Qwen.'


@pytest.mark.parametrize('prov,modelo', [('groq', 'llama-x'), ('nvidia', 'meta/llama-x')])
def test_otros_proveedores_siguen_sin_stream(url, monkeypatch, prov, modelo):
    from integration.chat_mvp import providers
    monkeypatch.setattr(providers, 'env_keys', lambda p: ['k1'])
    monkeypatch.setattr(providers, 'base_url', lambda p: url)
    VISTOS.clear()
    s, d = _api(prov, modelo, lambda c: None)  # aunque haya stream_fn, solo qwencloud usa SSE
    assert VISTOS and not any(v.get('stream') for v in VISTOS)
    assert d['choices'][0]['message']['content'] == 'hola no-stream'


def test_ficha1_pasa_stream_fn(monkeypatch):
    fq = _load('fixa_fichas_qwen', 'fichas_qwen/plugin.py')
    capt = {}

    class Fake:
        FICHAS = {v: {} for v in fq._QW.values()}

        def _chat(self, p):
            capt.update(p); raise RuntimeError('STOP_TEST')
    monkeypatch.setattr(fq, '_pc', lambda: Fake())
    monkeypatch.setattr(fq, '_cfg', lambda f: (90, 0, 512, 100000))
    FICHA = {'ficha': 'ficha1'}
    with pytest.raises(RuntimeError, match='STOP_TEST'):
        fq._llamar_harness_1('ficha-qwen38max', 'que modelo eres', FICHA, {'id': 'N4'}, {})
    assert callable(capt.get('stream_fn')) and capt['model'] == 'qw-qwen-3-8-max'
    got = []
    with pytest.raises(RuntimeError, match='STOP_TEST'):
        fq._llamar_harness_1('ficha-qwen38max', 'x', FICHA, {'id': 'N4'}, {'stream_fn': got.append})
    capt['stream_fn']('a'); assert got == ['a']  # visor existente se respeta
