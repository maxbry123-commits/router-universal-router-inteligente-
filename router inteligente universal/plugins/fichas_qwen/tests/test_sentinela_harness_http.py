"""Graphiti / Graphify / grafo SQLite de la Constitucion como PLUGIN por el canal Harness (sin puentes directos):
componente -> HTTP -> Harness (puente_chat) -> HTTP -> Ficha (fichas_qwen) -> memoria real (SQLite + grafo SQLite + Graphify AST).
Servidor HTTP local con el mismo sobre del Router ({status, result}); memoria real en un directorio temporal; sin bucket ni claves."""
import importlib
import json
import os
import sys
import threading
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[3]
for _p in (RAIZ, RAIZ.parent / 'chat router' / '04-MEMORIA'):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))
RUTAS = []


class _Host(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def do_POST(self):  # /plugins/<id>/call/<accion>  (mismo contrato que el Router)
        partes = self.path.strip('/').split('/')
        RUTAS.append(self.path)
        body = json.loads(self.rfile.read(int(self.headers.get('Content-Length') or 0)) or b'{}')
        try:
            res = importlib.import_module('plugins.%s.plugin' % partes[1]).handle(partes[3], body)
            env = {'status': 'ok', 'result': res}
        except Exception as e:  # noqa: BLE001
            env = {'status': 'error', 'reason': type(e).__name__ + ': ' + str(e)[:200]}
        out = json.dumps(env, default=str).encode()
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(out)


@pytest.fixture(scope='module')
def router(tmp_path_factory):
    d = tmp_path_factory.mktemp('riu-data')
    viejo = {k: os.environ.get(k) for k in ('RIU_DATA_DIR', 'RIU_ROUTER_URL', 'HF_TOKEN', 'RIU_SENTINELA_GRAPHITI', 'RIU_GRAPHITI_ENABLE')}
    os.environ['RIU_DATA_DIR'] = str(d)
    for k in ('HF_TOKEN', 'RIU_SENTINELA_GRAPHITI', 'RIU_GRAPHITI_ENABLE'):
        os.environ.pop(k, None)  # sin bucket; Graphiti apagado como en produccion
    srv = ThreadingHTTPServer(('127.0.0.1', 0), _Host)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    os.environ['RIU_ROUTER_URL'] = 'http://127.0.0.1:%d' % srv.server_address[1]
    yield os.environ['RIU_ROUTER_URL']
    srv.shutdown()
    for k, v in viejo.items():
        if v is None:
            os.environ.pop(k, None)
        else:
            os.environ[k] = v


def _componente(base, accion, payload):  # lo que hace sentinela.js con window.RIU_ACCION (api.js accion -> harnessUrl)
    r = urllib.request.Request(base + '/plugins/puente_chat/call/' + accion, data=json.dumps(payload).encode(),
                               headers={'Content-Type': 'application/json'}, method='POST')
    env = json.loads(urllib.request.urlopen(r, timeout=30).read().decode())
    assert env['status'] == 'ok', env
    return env['result']


def test_anclar_va_por_el_harness_y_escribe_en_el_grafo(router):
    RUTAS.clear()
    r = _componente(router, 'sentinela_anclar', {'sesion': 'director', 'contrato': 'termina con SENTINELA7',
                                                  'system_prompt': {'nombre': 'sp', 'texto': 'Empieza con VALE'},
                                                  'archivos': [{'nombre': 'calc.py', 'contenido': 'def suma(a, b):\n    return a + b\n'}]})
    assert RUTAS == ['/plugins/puente_chat/call/sentinela_anclar', '/plugins/fichas_qwen/call/sentinela_anclar']  # Harness -> HTTP -> Ficha
    assert r['via'] == 'harness->http->fichas_qwen'
    assert r['graph_sqlite'] == 'SAVED' and len(r['escritos']) == 3, r
    assert str(r['graphiti']).startswith('GAP_DISABLED'), r  # produccion: Graphiti apagado (no sube la latencia del chat)
    if isinstance(r['graphify'], dict) and r['graphify'].get('status') == 'GAP_GRAPHIFY_DEPS':
        pytest.skip('Graphify no esta en este checkout (RIU_COMPONENTES_DIR): ' + json.dumps(r['graphify']))
    assert isinstance(r['graphify'], dict) and r['graphify'].get('status') == 'BUILT' and int(r['graphify'].get('nodos') or 0) > 0, r


def test_consultar_grafo_por_el_harness(router):
    RUTAS.clear()
    r = _componente(router, 'sentinela_grafo', {'sesion': 'director', 'consulta': ''})
    assert RUTAS == ['/plugins/puente_chat/call/sentinela_grafo', '/plugins/fichas_qwen/call/sentinela_grafo']
    assert isinstance(r['graph_sqlite'], list) and r['graph_sqlite'], r
    if r['graphify'] == 'SIN_GRAFO':
        pytest.skip('Graphify no esta en este checkout (RIU_COMPONENTES_DIR)')
    assert isinstance(r['graphify'], list) and any('suma' in json.dumps(x) for x in r['graphify']), r


def test_validar_por_el_harness(router):
    RUTAS.clear()
    r = _componente(router, 'sentinela_validar', {'contrato': 'termina con SENTINELA7', 'salida': 'hola',
                                                   'archivos': [{'nombre': 'malo.py', 'contenido': 'def f(:\n'}]})
    assert RUTAS == ['/plugins/puente_chat/call/sentinela_validar', '/plugins/fichas_qwen/call/sentinela_validar']
    assert r['violaciones'] == ['TERMINA CON: SENTINELA7'] and r['archivos'][0]['sintaxis_ok'] is False


def test_accion_desconocida_no_sale_del_harness(router):
    import plugins.puente_chat.plugin as pc
    assert pc.sentinela_call('borrar_todo', {}) == {'error': 'ACCION_DESCONOCIDA'}


def test_acciones_permitidas_en_las_fichas():
    for pid in ('puente_chat', 'fichas_qwen'):
        aa = json.loads((RAIZ / 'plugins' / pid / 'ficha.json').read_text())['ejecucion']['allowed_actions']
        assert {'sentinela_anclar', 'sentinela_grafo', 'sentinela_validar'} <= set(aa), pid


def test_llm_de_graphiti_va_por_harness_http_ficha4(router, monkeypatch):
    # Graphiti no llama a ningun modelo directo: _graphiti_llm_ficha -> llm_call -> HTTP -> fichas_qwen/llm (Ficha 4)
    import plugins.fichas_qwen.plugin as fq
    import plugins.puente_chat.plugin as pc
    vistos = []
    monkeypatch.setattr(fq, '_llamar', lambda modelo, prompt, ficha, **kw: vistos.append((modelo, ficha.get('ficha'))) or '{"ok": true}')
    RUTAS.clear()
    assert pc._graphiti_llm_ficha([{'role': 'user', 'content': 'extrae entidades'}], 200) == '{"ok": true}'
    assert RUTAS == ['/plugins/fichas_qwen/call/llm'] and vistos and 'ficha4' in str(vistos[0][1]), (RUTAS, vistos)


def test_graphiti_cede_el_paso_al_chat():
    # con un chat en curso la LLM de Graphiti espera (no ocupa cupos HTTP del chat) y va de a 1
    import time
    from plugins.fichas_qwen import sentinela_contrato as s

    class G:
        def __init__(self):
            self._call_ref = {'call': lambda m, t: 'r'}
        def _ensure_llm(self):
            return True
        def set_llm_client(self, c):
            self._call_ref['call'] = c
    g = G()
    s.limitar_llm_graphiti(g, None)
    s.ACTIVOS[0] += 1
    t0 = time.time()
    threading.Timer(0.6, lambda: s.ACTIVOS.__setitem__(0, s.ACTIVOS[0] - 1)).start()
    assert g._call_ref['call']([], 10) == 'r'
    assert time.time() - t0 >= 0.55  # espero a que el chat terminara
    g.set_llm_client(lambda m, t: 'nuevo')  # el Harness re-cablea: sigue limitado
    assert getattr(g._call_ref['call'], '_sent', False) and g._call_ref['call']([], 10) == 'nuevo'
