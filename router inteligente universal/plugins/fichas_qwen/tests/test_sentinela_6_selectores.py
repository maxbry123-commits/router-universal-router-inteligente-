"""Constitucion sentinela en los 6 selectores Qwen (simulacion hasta la frontera del Harness, sin red ni claves).

Ruta real ejecutada: fichas_qwen._chat -> sentinela (entrada) -> ficha 1/2/3/5 -> Harness (puente_chat._chat SIMULADO)
-> validador determinista -> 1 juez-corrector solo si falla. El "modelo" simulado obedece SOLO lo que le llega en el prompt:
si la Constitucion no viaja, la respuesta no termina en SENTINELA7 (asi se prueba que el texto llega al modelo)."""
import re
import sys
import types
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[3]
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))
import plugins.fichas_qwen.plugin as fq  # noqa: E402

CONST = 'Responde en español.\ntermina con SENTINELA7'
SELECTORES = {  # los 6 selectores del chat, con el payload que manda panel-chat.js
    'team-qwen-max': {'ficha_qwen': '1', 'modelo': 'Qwen 3.8 Max', 'task_type': 'chat'},
    'team-qwen-flash': {'ficha_qwen': '1', 'modelo': 'Qwen 3.8 Flash', 'task_type': 'chat'},
    'team5-max': {'ficha_qwen': '5', 'modelo': 'Qwen 3.8 Max', 'instrucciones_fijas': ''},
    'team5-flash': {'ficha_qwen': '5', 'modelo': 'Qwen 3.8 Flash', 'instrucciones_fijas': ''},
    'consil-code': {'ficha_qwen': '2', 'modelo': '', 'task_type': 'chat'},
    'consil-frontend': {'ficha_qwen': '3', 'modelo': '', 'task_type': 'chat'},
}
LLAMADAS = []


def _modelo(texto, desobediente):
    """Modelo simulado: cumple 'termina con X' / 'empieza con X' / system prompt SOLO si estan en lo que recibe."""
    if 'JUEZ-CORRECTOR' in texto:
        m = re.search(r'TERMINA CON: (\S+)', texto)
        return 'Respuesta corregida. ' + (m.group(1) if m else '')
    if 'VEREDICTO' in texto and ('N6' in texto or 'AUDITOR' in texto.upper()):
        return 'VEREDICTO: PASS'
    out = 'Hola, soy el modelo.'
    m = re.search(r'SYSTEM PROMPT DEL DIRECTOR[^\n]*\n(.+)', texto)
    if m and 'Empieza con VALE' in m.group(1):
        out = 'VALE. ' + out
    if not desobediente and 'CONSTITUCION SENTINELA' in texto:
        m = re.search(r'termina con (\S+)', texto, re.I)
        if m:
            out += ' ' + m.group(1)
    return out


def _pc_falso(desobediente=False):
    real = fq._pc()

    def _chat(body):
        texto = '\n'.join(str(m.get('content') or '') for m in body.get('messages') or [])
        LLAMADAS.append({'model': body.get('model'), 'nodo': body.get('nodo'), 'texto': texto})
        r = _modelo(texto, desobediente)
        if callable(body.get('stream_fn')):
            body['stream_fn'](r)
        return {'choices': [{'message': {'role': 'assistant', 'content': r}}], 'herramientas': []}
    m = types.SimpleNamespace(**{k: getattr(real, k) for k in dir(real) if not k.startswith('__')})
    m._chat = _chat
    m._qwen_conf = lambda: ('sk-sp-simulada', 'https://token-plan.simulado/v1')
    return m


def _correr(sel, extra, desobediente=False, monkeypatch=None):
    LLAMADAS.clear()
    pc = _pc_falso(desobediente)
    monkeypatch.setattr(fq, '_pc', lambda: pc)
    import plugins.fichas_qwen.mvp as mvp
    monkeypatch.setattr(mvp, '_fq', lambda: fq, raising=False)
    monkeypatch.setattr(fq, '_gov_prepare', lambda ficha, opts, ap, esperado='': {})
    p = dict(SELECTORES[sel], message='Di hola', sesion='sim-' + sel, **extra)
    return fq._chat(p)


def _on():
    return {'sentinela': {'on': True, 'contrato': CONST}}


def test_on_los_6_selectores_terminan_con_sentinela7(monkeypatch):
    for sel in SELECTORES:
        r = _correr(sel, _on(), monkeypatch=monkeypatch)
        assert isinstance(r, dict) and not r.get('error'), (sel, r)
        assert r['reply'].rstrip().endswith('SENTINELA7'), (sel, r['reply'])
        assert any('termina con SENTINELA7' in c['texto'] for c in LLAMADAS), sel  # el texto de la Constitucion llego al modelo
        assert r['sentinela']['on'] is True and r['sentinela']['estado'] == 'PASO', (sel, r['sentinela'])
        assert not any('JUEZ-CORRECTOR' in c['texto'] for c in LLAMADAS), sel  # paso: 0 llamadas extra


def test_off_los_6_selectores_no_mandan_ni_validan(monkeypatch):
    for sel in SELECTORES:
        r = _correr(sel, {}, monkeypatch=monkeypatch)
        assert not r.get('error'), (sel, r)
        assert 'SENTINELA7' not in r['reply'], sel
        assert not any('CONSTITUCION SENTINELA' in c['texto'] or 'SENTINELA7' in c['texto'] for c in LLAMADAS), sel
        assert 'sentinela' not in r, sel  # OFF: el sentinela ni corre


def test_off_aunque_el_texto_exista(monkeypatch):
    for sel in SELECTORES:  # boton OFF: el chat manda sentinela.on=false (o nada) aunque haya texto guardado
        r = _correr(sel, {'sentinela': {'on': False, 'contrato': CONST}}, monkeypatch=monkeypatch)
        assert 'SENTINELA7' not in r['reply'] and not any('SENTINELA7' in c['texto'] for c in LLAMADAS), sel


def test_on_modelo_desobediente_juez_corrige_1_vez(monkeypatch):
    for sel in SELECTORES:
        r = _correr(sel, _on(), desobediente=True, monkeypatch=monkeypatch)
        assert r['reply'].rstrip().endswith('SENTINELA7'), (sel, r['reply'])
        assert r['sentinela']['estado'] == 'CORREGIDA' and r['sentinela']['via'] == 'juez_llm_1_reintento', sel
        assert sum('JUEZ-CORRECTOR' in c['texto'] for c in LLAMADAS) == 1, sel
        assert r.get('reply_original') and not r['reply_original'].endswith('SENTINELA7'), sel


def test_constitucion_texto_del_chat_tambien_llega(monkeypatch):
    # bug original: el chat manda constitucion.texto y fichas_qwen leia constitucion_texto
    for sel in SELECTORES:
        r = _correr(sel, {'sentinela': {'on': True}, 'constitucion': {'texto': CONST}}, monkeypatch=monkeypatch)
        assert r['reply'].rstrip().endswith('SENTINELA7'), (sel, r['reply'])


def test_system_prompt_aparte_viaja_sin_constitucion(monkeypatch):
    for sel in SELECTORES:
        r = _correr(sel, {'system_prompt': {'nombre': 'vale', 'texto': 'Empieza con VALE'}}, monkeypatch=monkeypatch)
        assert r['reply'].startswith('VALE.'), (sel, r['reply'])
        assert r['sentinela']['on'] is False and r['sentinela']['system_prompt'] == 'vale', sel
        assert 'estado' not in r['sentinela'], sel  # el system prompt NO se valida


def test_sin_modulo_sentinela_el_chat_no_se_rompe(monkeypatch):
    def roto():
        raise ImportError('x')
    monkeypatch.setattr(fq, '_sent_mod', roto)
    r = _correr('team-qwen-flash', _on(), monkeypatch=monkeypatch)
    assert not r.get('error') and r['reply'] and 'sentinela' not in r
