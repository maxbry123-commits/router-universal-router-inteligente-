import json, os
from pathlib import Path

_RUTA = Path(__file__).with_name('modelos.json')


def cargar():
    return json.loads(_RUTA.read_text(encoding='utf-8'))


def plan():
    p = os.environ.get('MVP_PLAN', 'personal').lower()
    return p if p in ('personal', 'team') else 'personal'


def permitidos(plan_=None):
    k = 'p' if (plan_ or plan()) == 'personal' else 't'
    return [m['id'] for m in cargar()['texto'] if m[k]]


def catalogo(plan_=None):
    """Los modelos del plan con su tipo (texto, imagen, audio, video): 23 en Personal Standard."""
    k, d = ('p' if (plan_ or plan()) == 'personal' else 't'), cargar()
    return [(m['id'], t) for t in ('texto', 'imagen', 'audio', 'video') for m in d[t] if m[k]]


def validar(modelo, plan_=None):
    d = cargar()
    modelo = modelo or d['modelo_defecto']
    otros = {m['id'] for t in ('imagen', 'audio', 'video') for m in d[t]}
    if modelo in otros:
        raise ValueError('solo texto en el MVP: ' + modelo)
    if modelo not in permitidos(plan_):
        raise ValueError('modelo no permitido en el plan %s; permitidos: %s' % (plan_ or plan(), ', '.join(permitidos(plan_))))
    return modelo


def extra_body(modelo, plan_=None, opciones=None):
    opciones = opciones or {}
    th = {m['id']: m['th'] for m in cargar()['texto']}[modelo]
    cuerpo = {}
    if th is True or (th == 'team' and (plan_ or plan()) == 'team'):
        cuerpo['enable_thinking'] = True
    if modelo == 'qwen3.8-max':
        if 'enable_thinking' in opciones:
            cuerpo['enable_thinking'] = bool(opciones['enable_thinking'])
        if opciones.get('reasoning_effort') in ('low', 'medium', 'xhigh'):
            cuerpo['reasoning_effort'] = opciones['reasoning_effort']
    return cuerpo


def clave_env():
    d = cargar()
    for n in [d['variable_clave']] + d['variables_alternas']:
        if os.environ.get(n):
            return os.environ[n]
    return None


def base_url():
    return os.environ.get('MVP_QWEN_BASE_URL') or cargar()['base_url']


def qwen_code_config(plan_=None):
    d = cargar()
    pl = plan_ or plan()
    entradas = []
    for mid in permitidos(pl):
        e = {'id': mid, 'name': '[Token Plan] ' + mid, 'baseUrl': base_url(), 'envKey': d['variable_clave']}
        eb = extra_body(mid, pl)
        if eb:
            e['generationConfig'] = {'extra_body': eb}
        entradas.append(e)
    return {'modelProviders': {'openai': entradas}, 'security': {'auth': {'selectedType': 'openai'}}, 'tokenPlan': {'region': d['region']}, 'model': {'name': d['modelo_defecto']}, '$version': 3}
