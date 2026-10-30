import json, os, re
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
    """Los modelos del plan con su tipo (texto, imagen, audio, video): 22 en Personal Standard."""
    k, d = ('p' if (plan_ or plan()) == 'personal' else 't'), cargar()
    return [(m['id'], t) for t in ('texto', 'imagen', 'audio', 'video') for m in d[t] if m[k]]


def _llave(nombre):  # "ficha-qwen38max", "qw-glm-5-3", "Qwen 3.8 Max", "dsv4pro" -> llave comparable
    s = re.sub(r'^(ficha|qw)[-_]', '', str(nombre).strip().lower())
    s = re.sub(r'^ds(?=v\d)', 'deepseek', s)
    return re.sub(r'[^a-z0-9]', '', s)


def canonico(nombre, plan_=None):
    """Nombres antiguos del frontend/fichas -> id del catálogo; si no hay coincidencia se devuelve tal cual."""
    if not nombre:
        return nombre
    ids = [i for i, _ in catalogo(plan_)]
    if nombre in ids:
        return nombre
    return {_llave(i): i for i in ids}.get(_llave(nombre), nombre)


def validar(modelo, plan_=None):
    from mvp import externos
    if externos.proveedor(modelo):  # groq/<id> o nvidia/<id>: lo valida su API
        return modelo
    d = cargar()
    modelo = canonico(modelo, plan_) or d['modelo_defecto']
    otros = {m['id'] for t in ('imagen', 'audio', 'video') for m in d[t]}
    if modelo in otros:
        raise ValueError('solo texto en el MVP: ' + modelo)
    if modelo not in permitidos(plan_):
        raise ValueError('modelo no permitido en el plan %s; permitidos: %s' % (plan_ or plan(), ', '.join(permitidos(plan_))))
    return modelo


def extra_body(modelo, plan_=None, opciones=None):
    opciones = opciones or {}
    th = {m['id']: m['th'] for m in cargar()['texto']}.get(modelo, False)  # modelos de Groq/NVIDIA: sin extras de Qwen
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


MARCAS = (("qwen", "Qwen (Alibaba)"), ("glm", "GLM (Zhipu AI)"), ("deepseek", "DeepSeek"), ("kimi", "Kimi (Moonshot AI)"), ("minimax", "MiniMax"), ("wan", "Wan (Alibaba)"), ("happyhorse", "HappyHorse"))  # marca oficial del catalogo del Token Plan


def marca(modelo):
    m = str(modelo).lower()
    return next((nombre for prefijo, nombre in MARCAS if m.startswith(prefijo)), "")


def bases(base=None):
    """URL base oficial primero y la de QwenCloud despues (misma ruta en las dos): si una no acepta la clave se prueba la otra."""
    d, base = cargar(), (base or base_url())
    alterna = d.get('base_url_alterna_qwencloud')
    return [base] + ([alterna] if alterna and base == d['base_url'] and base != alterna else [])


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
