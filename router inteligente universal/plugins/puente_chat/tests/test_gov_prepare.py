# Test determinista (sin red, sin LLM, con stubs) de gov_prepare / sheriff_pre / _gov_pre_chat.
# Extrae el bloque ==GOV-BEGIN==..==GOV-END== de plugin.py y lo ejecuta con exec. Uso: python test_gov_prepare.py
import json
import re
import tempfile
import time
from pathlib import Path

PLUGIN = Path(__file__).resolve().parent.parent / 'plugin.py'
SRC = PLUGIN.read_text(encoding='utf-8')
BLOQUE = SRC[SRC.index('# ==GOV-BEGIN=='):SRC.index('# ==GOV-END==')]
CONST_OK = {'id': 'CONSTITUCION-YAIWES', 'version': '1.1.0', 'modo': 'FAIL_CLOSED', 'reglas': ['a', 'b']}


class MemStub:
    def __init__(self):
        self.datos = {}
        self.falla = False

    def save(self, sc, clave, d):
        if self.falla:
            raise RuntimeError('memoria caida')
        self.datos[(sc, clave)] = d

    def search(self, sc, q, n):
        return [{'data': v} for (s, _c), v in self.datos.items() if s == sc]


def nuevo(const=CONST_OK, snapshot=None, set_changed=False):
    tmp = Path(tempfile.mkdtemp())
    ruta = tmp / 'CONSTITUCION-YAIWES.json'
    if const is not None:
        ruta.write_text(const if isinstance(const, str) else json.dumps(const), encoding='utf-8')
    mem = MemStub()
    llamadas = {'resolver': 0}
    ns = {'json': json, 're': re, 'time': time, 'Path': Path, '__file__': str(tmp / 'plugin.py'), 'DUENO': 'chat-ui'}
    ns['_memoria'] = lambda: (mem, lambda dueno, clave: dueno + '|' + clave)
    ns['_archivo_memoria'] = lambda sesion, nombre: ''

    def resolver(sesion, anclados, task_id, pregunta=''):
        llamadas['resolver'] += 1
        r = {'texto': 'x', 'snapshot': snapshot if snapshot is not None else [{'tipo': 'archivo', 'id': 'a.txt', 'estado': 'OK', 'sha256': 'abc', 'procedencia': 'p'}],
             'pedidos': [str(a) for a in anclados]}
        if set_changed:
            r['source_set_changed'] = True
        return r
    ns['resolver_anclados'] = resolver
    exec(BLOQUE, ns)
    ns['_CONST_RUTA'] = ruta
    ns['_CONST_DIR'] = tmp
    return ns, mem, ruta, llamadas


def payload(**kw):
    p = {'task_id': 'T1', 'sesion': 's', 'anclados': ['archivo:a.txt'], 'aprobado': False}
    p.update(kw)
    return p


def test_hash_estable_4_llamadas():
    ns, _m, _r, _l = nuevo()
    hs = {ns['gov_prepare'](payload())['constitution_hash'] for _ in range(4)}
    assert len(hs) == 1 and len(next(iter(hs))) == 64
    otro, _m2, _r2, _l2 = nuevo()
    assert otro['gov_prepare'](payload())['constitution_hash'] == next(iter(hs))  # mismo contenido -> mismo hash entre procesos
    r = ns['gov_prepare'](payload())
    assert r['constitution_id'] == 'CONSTITUCION-YAIWES' and r['approved'] is False and r['source_snapshot_id']


def test_overlay_cambia_hash_solo_si_viene():
    ns, _m, _r, _l = nuevo()
    base = ns['gov_prepare'](payload(task_id='A'))['constitution_hash']
    con = ns['gov_prepare'](payload(task_id='B', constitucion={'texto': 'regla extra'}))['constitution_hash']
    assert base != con


def test_cambio_constitucion_da_gap():
    ns, _m, ruta, _l = nuevo()
    assert 'error' not in ns['gov_prepare'](payload())
    ruta.write_text(json.dumps(dict(CONST_OK, reglas=['cambiada'])), encoding='utf-8')
    assert ns['gov_prepare'](payload())['error'] == 'CONSTITUTION_CHANGED_DURING_TASK'
    assert ns['gov_prepare'](payload(aprobado=True))['error'] == 'CONSTITUTION_CHANGED_BEFORE_APPROVAL'
    # hash_esperado distinto
    ns2, _m2, _r2, _l2 = nuevo()
    assert ns2['gov_prepare'](payload(task_id='Z', hash_esperado='0' * 64, aprobado=True))['error'] == 'CONSTITUTION_CHANGED_BEFORE_APPROVAL'
    # sheriff: gov_ctx con hash viejo tras cambiar la Constitucion
    ns3, _m3, ruta3, _l3 = nuevo()
    ctx = ns3['gov_prepare'](payload())
    gov = {'gov_ctx': ctx, 'anclados': ['archivo:a.txt'], 'sesion': 's', 'task_id': 'T1'}
    chk = ns3['sheriff_pre'](gov, 'hola')
    assert chk['ok'] and chk['hash'] == ctx['constitution_hash']
    ruta3.write_text(json.dumps(dict(CONST_OK, reglas=['x'])), encoding='utf-8')
    chk = ns3['sheriff_pre'](gov, 'hola')
    assert not chk['ok'] and chk['codigo'] == 'CONSTITUTION_CHANGED_DURING_TASK'
    p = {'gov_ctx': ctx, 'anclados': ['archivo:a.txt'], 'task_id': 'T1'}
    info, err = ns3['_gov_pre_chat'](p, 's', 'q', p['anclados'])
    assert info is None and err['error'] == 'GAP CONSTITUTION_CHANGED_DURING_TASK'


def test_source_set_changed_antes_del_modelo():
    ns, _m, _r, _l = nuevo()
    ctx = ns['gov_prepare'](payload())
    ns['resolver_anclados'] = lambda *a, **k: {'texto': 'x', 'snapshot': [], 'pedidos': [], 'source_set_changed': True}
    p = {'gov_ctx': ctx, 'anclados': ['archivo:a.txt'], 'task_id': 'T1', 'sesion': 's'}
    info, err = ns['_gov_pre_chat'](p, 's', 'q', p['anclados'])
    assert info is None and err['error'] == 'GAP SOURCE_SET_CHANGED'
    # ancla no leible -> GAP antes del modelo
    ns['resolver_anclados'] = lambda *a, **k: {'texto': 'x', 'snapshot': [{'id': 'a.txt', 'estado': 'NO_LEIBLE'}], 'pedidos': []}
    info, err = ns['_gov_pre_chat'](p, 's', 'q', p['anclados'])
    assert err['error'] == 'GAP FUENTE_ANCLADA_NO_LEIBLE'
    # orden textual en _chat: el pre-chequeo gobernado va antes de cualquier llamada al modelo / tools
    i = SRC.index('def _chat(p):')
    cuerpo = SRC[i:SRC.index('def _estado', i)]
    assert cuerpo.index('_gov_pre_chat(') < cuerpo.index('_especial(') < cuerpo.index('_bucle(')
    assert cuerpo.index('_gov_pre_chat(') < cuerpo.index('_llamar_api(')


def test_gobernanza_apagada_explicita():
    ns, _m, _r, ll = nuevo()
    r = ns['gov_prepare'](payload(gobernanza_activa=False))
    assert r['apagada_por_director'] is True and 'error' not in r
    info, err = ns['_gov_pre_chat']({'gobernanza_activa': False, 'gov_ctx': {'x': 1}}, 's', 'q', [])
    assert err is None and info['apagada_por_director'] is True and info['id'] == 'CONSTITUCION-YAIWES'
    assert ll['resolver'] == 0
    # sin orden explicita nunca se apaga; chat normal intacto
    assert ns['_gov_pre_chat']({}, 's', 'q', []) == (None, None)
    info, err = ns['_gov_pre_chat']({'gov_ctx': {'constitution_hash': 'x'}, 'gobernanza_activa': None}, 's', 'q', [])
    assert err is not None


def test_constitucion_invalida_y_persistencia():
    for malo in (None, '{no es json', {'id': 'X', 'version': '1', 'modo': 'ABIERTO'}, {'version': '1', 'modo': 'FAIL_CLOSED'}):
        ns, _m, _r, _l = nuevo(const=malo)
        assert ns['gov_prepare'](payload())['error'].startswith('CONSTITUTION_INVALID')
        p = {'gov_ctx': {'constitution_hash': 'x'}, 'task_id': 'T'}
        info, err = ns['_gov_pre_chat'](p, 's', 'q', [])
        assert info is None and err['error'] == 'GAP CONSTITUTION_INVALID'
    ns, mem, _r, _l = nuevo()
    mem.falla = True
    assert ns['gov_prepare'](payload())['error'] == 'GOVERNANCE_NO_PERSISTIDO'
    # gobernada sin gov_prepare previo
    ns, _m, _r, _l = nuevo()
    info, err = ns['_gov_pre_chat']({'gobernanza': {'enabled': True}}, 's', 'q', [])
    assert err['error'] == 'GAP GOVERNANCE_PREPARE_NO_DISPONIBLE'


def test_pass_y_ancla_constitucion():
    ns, _m, _r, _l = nuevo()
    ctx = ns['gov_prepare'](payload())
    p = {'gov_ctx': ctx, 'anclados': ['archivo:a.txt'], 'task_id': 'T1', 'sesion': 's'}
    info, err = ns['_gov_pre_chat'](p, 's', 'q', p['anclados'])
    assert err is None and info['sheriff'] == 'PASS' and info['judge'] == 'PENDIENTE' and info['hash'] == ctx['constitution_hash']
    # ancla constitucion:<nombre> por referencia directa, nunca por similitud
    ns['_CONST_DIR'].joinpath('extra.md').write_text('overlay', encoding='utf-8')
    t, _pr = ns['_gov_ancla_leer']('s', 'extra')
    assert t == 'overlay'
    assert ns['_gov_ancla_leer']('s', '../x')[0] is None and ns['_gov_ancla_leer']('s', 'inexistente')[0] is None
    h1 = ns['gov_prepare'](payload(task_id='C', anclados=['constitucion:extra']))['constitution_hash']
    assert h1 != ctx['constitution_hash']
    assert ns['gov_prepare'](payload(task_id='D', anclados=['constitucion:no-existe']))['error'].startswith('FUENTE_ANCLADA_NO_LEIBLE')
    assert "nom.startswith('constitucion:')" in SRC


if __name__ == '__main__':
    n = 0
    for k, f in sorted(globals().items()):
        if k.startswith('test_') and callable(f):
            f()
            n += 1
            print('OK', k)
    print('TOTAL', n, 'tests OK')
