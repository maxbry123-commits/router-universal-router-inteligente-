"""Simulacion de los 6 selectores Qwen (Team qwen Max/Flash, Team 5 MVP Max/Flash, Ask consil code/frontend) con la
Constitucion ON y OFF y la regla de prueba 'TERMINA CON: SENTINELA7'. Sin red: el modelo es un stub que SOLO termina con
SENTINELA7 si el contrato le llego en el prompt; asi PASO (sin correccion) prueba que el texto alcanzo al modelo final."""
import importlib
import sys
import time
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[3]  # 'router inteligente universal' (como el host: plugins.fichas_qwen.plugin)
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))
fq = importlib.import_module('plugins.fichas_qwen.plugin')
mvp = importlib.import_module('plugins.fichas_qwen.mvp')

CONTRATO = 'Responde en español.\nTERMINA CON: SENTINELA7'
PROMPTS = []


def _modelo(prompt):
    return ('respuesta del modelo' + chr(10) + 'VEREDICTO: PASS' + chr(10) + 'SENTINELA7') if 'SENTINELA7' in prompt else ('respuesta del modelo' + chr(10) + 'VEREDICTO: PASS')


@pytest.fixture(autouse=True)
def _stubs(monkeypatch):
    _instalar(monkeypatch)


def _instalar(monkeypatch):
    PROMPTS.clear()

    def llh(modelo, prompt, ficha, n, opts):
        PROMPTS.append((n['id'], prompt))
        return _modelo(prompt)

    def llh1(modelo, prompt, ficha, n, opts):
        PROMPTS.append((n.get('id'), prompt))
        return _modelo(prompt) if n.get('id') == 'JUEZ' else 'anexo (stub)'

    def mvp_chat(p, ficha, mensaje, ses, t0):  # Team 5: el modelo recibe instrucciones_fijas como system (mvp._mensajes)
        conv = mvp._mensajes(p, mensaje)
        txt = chr(10).join(m['content'] for m in conv)
        PROMPTS.append(('MVP', txt))
        r = _modelo(txt)
        return {'model': str(p.get('modelo')), 'reply': r, 'choices': [{'index': 0, 'message': {'role': 'assistant', 'content': r}}]}

    monkeypatch.setattr(fq, '_llamar_harness', llh)
    monkeypatch.setattr(fq, '_llamar_harness_1', llh1)
    monkeypatch.setattr(fq, '_gov_prepare', lambda ficha, opts, aprobado, esperado='': {'constitution_id': 'tc', 'constitution_hash': 'h1', 'source_snapshot_id': '', 'approved': bool(aprobado)})
    monkeypatch.setattr(mvp, 'chat', mvp_chat)


SELECTORES = [  # (nombre, payload del panel-chat.js)
    ('team-qwen max', {'ficha_qwen': '1', 'modelo': 'ficha-qwen38max', 'task_type': 'chat'}),
    ('team-qwen flash', {'ficha_qwen': '1', 'modelo': 'ficha-qwen38flash', 'task_type': 'chat'}),
    ('team-5-mvp max', {'ficha_qwen': '5', 'modelo': 'ficha-qwen38max', 'instrucciones_fijas': ''}),
    ('team-5-mvp flash', {'ficha_qwen': '5', 'modelo': 'ficha-qwen38flash', 'instrucciones_fijas': ''}),
    ('ask-consil code', {'ficha_qwen': '2', 'modelo': '', 'task_type': 'chat'}),
    ('ask-consil frontend', {'ficha_qwen': '3', 'modelo': '', 'task_type': 'chat'}),
]
MENSAJES = ['Di solo: hola', 'Explica en detalle como funciona el router y revisa el flujo completo de las fichas paso a paso con ejemplos']


def _reply(r):
    return str(r.get('reply') or ((r.get('choices') or [{}])[0].get('message') or {}).get('content') or '')


@pytest.mark.parametrize('nombre,sel', SELECTORES)
@pytest.mark.parametrize('msg', MENSAJES)
def test_on_sentinela7_llega_al_modelo(nombre, sel, msg):
    t0 = time.perf_counter()
    r = fq._chat(dict(sel, message=msg, sesion='sim-on-' + nombre.replace(' ', '-'), sentinela={'on': True, 'contrato': CONTRATO}))
    ms = (time.perf_counter() - t0) * 1000
    assert 'error' not in r, r
    assert _reply(r).rstrip().endswith('SENTINELA7'), (nombre, _reply(r)[-200:])
    modelo_final = [p for n, p in PROMPTS if n not in ('JUEZ', None)][-1]  # el ultimo modelo que escribio la respuesta
    assert 'SENTINELA7' in modelo_final, nombre  # el texto de la Constitucion llego al modelo final
    st = r['sentinela']
    # PASO = el modelo cumplio. En el flujo pesado de Ask consil el motor agrega CHECK LISTA/RUTAS DESPUES del modelo: ahi
    # la marca la repone el arreglo determinista (sin LLM); nunca hace falta el juez.
    assert st['estado'] == 'PASO' or (st['estado'] == 'CORREGIDA' and st['via'] == 'arreglo_determinista'), (nombre, st)
    assert not any(n == 'JUEZ' for n, _p in PROMPTS)
    print('SIM ON  %-20s %-6s %-9s %d s %03d ms' % (nombre, 'fast' if r.get('fast_lane') else 'heavy', st['estado'], ms // 1000, ms % 1000))


@pytest.mark.parametrize('nombre,sel', SELECTORES)
def test_off_no_viaja_ni_valida(nombre, sel):
    r = fq._chat(dict(sel, message='Di solo: hola', sesion='sim-off-' + nombre.replace(' ', '-'), constitucion={'texto': CONTRATO}))
    assert 'error' not in r, r
    assert 'sentinela' not in r and not any('SENTINELA7' in p for _n, p in PROMPTS)
    assert not _reply(r).rstrip().endswith('SENTINELA7')


def test_on_modelo_que_ignora_se_corrige_y_se_informa(monkeypatch):
    monkeypatch.setattr(fq, '_llamar_harness', lambda modelo, prompt, ficha, n, opts: 'hola' + chr(10) + 'VEREDICTO: PASS')
    r = fq._chat({'ficha_qwen': '1', 'modelo': 'ficha-qwen38max', 'message': 'Di solo: hola', 'sesion': 'sim-ign', 'sentinela': {'on': True, 'contrato': CONTRATO}})
    assert _reply(r).rstrip().endswith('SENTINELA7') and r['sentinela']['estado'] == 'CORREGIDA' and r['sentinela']['via'] == 'arreglo_determinista'
    assert r.get('reply_original') and not r['reply_original'].rstrip().endswith('SENTINELA7')
