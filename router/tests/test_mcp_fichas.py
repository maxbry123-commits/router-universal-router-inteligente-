# -*- coding: utf-8 -*-
"""Pruebas offline (HTTP simulado) de la ampliacion del MCP original con fichas."""
import importlib.util
import json
import os
import sys

import pytest

AQUI = os.path.dirname(os.path.abspath(__file__))
CHAT = os.path.join(os.path.dirname(AQUI), 'integration', 'chat_mvp')
ROUTER = os.path.dirname(AQUI)


def _cargar(nombre, ruta):
    spec = importlib.util.spec_from_file_location(nombre, ruta)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


@pytest.fixture
def mods(monkeypatch):
    ruta = _cargar('mcp_route_t', os.path.join(CHAT, 'mcp_route.py'))
    fich = _cargar('mcp_fichas_t', os.path.join(CHAT, 'mcp_fichas.py'))
    fich.instalar(ruta)
    return ruta, fich


def _rpc(mod, metodo, params=None, i=1):
    return mod._mod().procesar_peticion({'jsonrpc': '2.0', 'id': i, 'method': metodo, 'params': params or {}})


def test_tools_list_seis(mods):
    ruta, _ = mods
    nombres = [t['name'] for t in _rpc(ruta, 'tools/list')['result']['tools']]
    assert nombres == ['github_leer', 'github_escribir', 'github_api', 'listar_fichas', 'chat', 'resultado']


def test_originales_sin_cambios(mods):
    ruta, _ = mods
    orig = _cargar('puente_orig', os.path.join(ROUTER, 'mcp_puente_github.py'))
    tools = _rpc(ruta, 'tools/list')['result']['tools']
    assert tools[:3] == orig.TOOLS


@pytest.mark.parametrize('tool,args,accion', [
    ('listar_fichas', {}, 'fichas'),
    ('chat', {'ficha_qwen': 'x', 'message': 'hola', 'sesion': 's1', 'request_id': 'r1', 'modelo': 'm'}, 'chat_async'),
    ('resultado', {'proceso_id': 'abc', 'espera': 5}, 'resultado'),
])
def test_nuevas_llaman_accion_real(mods, monkeypatch, tool, args, accion):
    ruta, fich = mods
    vistos = []
    resp = {'estado': 'procesando', 'proceso_id': 'abc'}
    monkeypatch.setattr(fich, '_llamar', lambda p, a, pl: vistos.append((p, a, pl)) or resp)
    r = _rpc(ruta, 'tools/call', {'name': tool, 'arguments': args})['result']
    assert vistos == [('fichas_qwen', accion, args)]
    assert r['isError'] is False
    assert json.loads(r['content'][0]['text']) == resp


def test_error_real_es_iserror(mods, monkeypatch):
    ruta, fich = mods
    monkeypatch.setattr(fich, '_llamar', lambda p, a, pl: {'error': 'HTTP 500', 'status': 'degraded'})
    r = _rpc(ruta, 'tools/call', {'name': 'listar_fichas', 'arguments': {}})['result']
    assert r['isError'] is True and 'HTTP 500' in r['content'][0]['text']


def test_faltan_requeridos(mods, monkeypatch):
    ruta, fich = mods
    monkeypatch.setattr(fich, '_llamar', lambda *a: pytest.fail('no debe llamar'))
    assert _rpc(ruta, 'tools/call', {'name': 'chat', 'arguments': {}})['result']['isError'] is True
    assert _rpc(ruta, 'tools/call', {'name': 'resultado', 'arguments': {}})['result']['isError'] is True


def test_tool_original_delegada(mods):
    ruta, _ = mods
    r = _rpc(ruta, 'tools/call', {'name': 'github_api', 'arguments': {}})['result']
    assert r['content'][0]['text'].startswith(('ERROR', 'FALTA'))


def test_http_plugins_url_y_llave(monkeypatch):
    hp = _cargar('hp_t', os.path.join(ROUTER, 'red', 'http_plugins.py'))
    capt = {}

    class R:
        def __enter__(s): return s
        def __exit__(s, *a): pass
        def read(s): return b'{"status":"ok","result":{"a":1}}'

    def fake(req, timeout=0):
        capt['url'] = req.full_url; capt['k'] = req.headers.get('X-api-key')
        return R()
    monkeypatch.setattr(hp.urllib.request, 'urlopen', fake)
    monkeypatch.delenv('RIU_ROUTER_URL', raising=False)
    monkeypatch.delenv('RIU_API_KEY', raising=False)
    monkeypatch.setenv('RIU_PUBLIC_CHAT_KEY', 'k1')
    assert hp.llamar('fichas_qwen', 'fichas', {}) == {'a': 1}
    assert capt['url'].endswith('/plugins/fichas_qwen/call/fichas') and capt['k'] == 'k1'


def _app(ruta, monkeypatch):
    fastapi = pytest.importorskip('fastapi')
    from fastapi.testclient import TestClient
    app = fastapi.FastAPI()
    app.include_router(ruta.build_mcp_router())
    return TestClient(app)


def test_auth_igual(mods, monkeypatch):
    ruta, _ = mods
    c = _app(ruta, monkeypatch)
    monkeypatch.delenv('RIU_MCP_KEY', raising=False)
    monkeypatch.setenv('RIU_PUBLIC_CHAT_KEY', 'pub')
    body = {'jsonrpc': '2.0', 'id': 1, 'method': 'tools/list'}
    assert c.post('/mcp', json=body).status_code == 401
    assert c.post('/mcp?key=mala', json=body).status_code == 401
    r = c.post('/mcp?key=pub', json=body)
    assert r.status_code == 200 and len(r.json()['result']['tools']) == 6
    monkeypatch.setenv('RIU_MCP_KEY', 'mcpk')
    assert c.post('/mcp?key=pub', json=body).status_code == 401
    assert c.post('/mcp?key=mcpk', json=body).status_code == 200
