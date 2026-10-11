# Test determinista (sin red, sin LLM, con stubs) de gov_prepare / sheriff_pre / _gov_pre_chat.
# Extrae el bloque ==GOV-BEGIN==..==GOV-END== de plugin.py y lo ejecuta con exec. Uso: python test_gov_prepare.py
import ast
import hashlib
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


REAL = PLUGIN.parent / 'constitucion' / 'CONSTITUCION-YAIWES.json'


def _fn(*nombres):
    tree = ast.parse(SRC)
    return chr(10).join(ast.get_source_segment(SRC, n) for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in nombres)


def test_system_prompt_contiene_constitucion_real():
    ns, _m, _r, _l = nuevo()
    ns['_CONST_RUTA'] = REAL
    ns['_CONST_DIR'] = REAL.parent
    real = json.loads(REAL.read_text(encoding='utf-8'))
    ctx = ns['gov_prepare'](payload())
    p = {'gov_ctx': ctx, 'anclados': ['archivo:a.txt'], 'task_id': 'T1', 'sesion': 's'}
    info, err = ns['_gov_pre_chat'](p, 's', 'q', p['anclados'])
    assert err is None
    b = info['_bloque']
    assert b.startswith('[CONSTITUCION YAIWES]') and b.endswith('[FIN CONSTITUCION]')
    assert 'ID: ' + real['id'] in b and 'VERSION: ' + real['version'] in b
    assert all(json.dumps(k, ensure_ascii=False) in b for k in real)  # todas las secciones reales de la Constitucion
    i = SRC.index('def _chat(p):')
    cuerpo = SRC[i:SRC.index('def _estado', i)]
    a = cuerpo.index("sistema += ' ' + gov_bloque")
    assert a < cuerpo.index('Contexto guardado de esta conversacion') and a < cuerpo.index('Anclados por el usuario')
    assert cuerpo.index('_gov_pre_chat(') < cuerpo.index('_contexto(')


def test_hash_del_bloque_igual_a_gov_ctx():
    ns, _m, _r, _l = nuevo()
    ns['_CONST_RUTA'] = REAL
    ns['_CONST_DIR'] = REAL.parent
    ctx = ns['gov_prepare'](payload())
    p = {'gov_ctx': ctx, 'anclados': ['archivo:a.txt'], 'task_id': 'T1', 'sesion': 's'}
    b = ns['_gov_pre_chat'](p, 's', 'q', p['anclados'])[0]['_bloque']
    lineas = b.split(chr(10))
    assert lineas[3] == 'HASH: ' + ctx['constitution_hash']
    assert hashlib.sha256(lineas[4].encode('utf-8')).hexdigest() == ctx['constitution_hash']  # el contenido del bloque produce ese hash
    # con overlay constitucion:<nombre> validado
    ns2, _m2, _r2, _l2 = nuevo()
    ns2['_CONST_DIR'].joinpath('extra.md').write_text('regla extra', encoding='utf-8')
    an = ['archivo:a.txt', 'constitucion:extra']
    ctx2 = ns2['gov_prepare'](payload(task_id='O', anclados=an))
    p2 = {'gov_ctx': ctx2, 'anclados': an, 'task_id': 'O', 'sesion': 's'}
    b2 = ns2['_gov_pre_chat'](p2, 's', 'q', an)[0]['_bloque']
    assert '[OVERLAY constitucion:extra' in b2 and 'regla extra' in b2 and ('HASH: ' + ctx2['constitution_hash']) in b2
    assert hashlib.sha256(b2.split(chr(10))[4].encode('utf-8')).hexdigest() == ctx2['constitution_hash']


def _ns_raiz(paths):
    mem = MemStub()
    cuenta = {'lista': 0, 'leer': 0}
    ns = {'json': json, 're': re, 'time': time, 'Path': Path, '__file__': 'x', 'DUENO': 'chat-ui', '_SNAP_ANC': {},
          '_ANC_TOPE_DOC': 3000, '_ANC_TOPE_TOTAL': 24000, '_ANC_RAIZ_MAX': 6}
    ns['_memoria'] = lambda: (mem, lambda d, c: d + '|' + c)
    ns['_anc_sha'] = lambda t: hashlib.sha256(str(t).encode('utf-8')).hexdigest()
    ns['_anc_raiz_parse'] = lambda r: ('o', 'r', '', 'integration')

    def lista(*a, **k):
        cuenta['lista'] += 1
        return list(paths), False

    def leer(o, r, rama, rp):
        cuenta['leer'] += 1
        return 'contenido de ' + rp, 'gh:' + rp
    ns['_anc_raiz_lista'] = lista
    ns['_anc_gh_leer'] = leer
    exec(_fn('_snap_scope', '_snap_guardar', '_snap_cargar', 'resolver_anclados', '_anc_raiz_elegir'), ns)
    return ns, cuenta


PATHS = ['README.md', 'integration/chat_mvp/memory_runtime.py', 'integration/chat_mvp/router.py', 'integration/otro/zeta.py', 'assets/logo.png']


def _ids_archivos(r):
    return [s['id'] for s in r['snapshot'] if s['tipo'] == 'archivo_raiz']


def test_raiz_pregunta_memory_runtime_selecciona_archivo_relevante():
    ns, _c = _ns_raiz(PATHS)
    r = ns['resolver_anclados']('s', ['raiz:o/r/integration'], 'T6', 'memory_runtime')
    ids = _ids_archivos(r)
    assert 'integration/chat_mvp/memory_runtime.py' in ids and 'assets/logo.png' not in ids
    # control: otra pregunta en otra tarea NO selecciona memory_runtime (la seleccion depende de la pregunta)
    r2 = ns['resolver_anclados']('s', ['raiz:o/r/integration'], 'T6b', 'zzzz qqqq')
    assert 'integration/chat_mvp/memory_runtime.py' not in _ids_archivos(r2)


def test_raiz_congelada_misma_seleccion_en_llamadas_posteriores():
    ns, cuenta = _ns_raiz(PATHS)
    r1 = ns['resolver_anclados']('s', ['raiz:o/r/integration'], 'T7', 'memory_runtime')
    ids1 = _ids_archivos(r1)
    lecturas = cuenta['leer']
    for q in ('pregunta distinta zzzz', '', 'router zeta'):
        r = ns['resolver_anclados']('s', ['raiz:o/r/integration'], 'T7', q)
        assert _ids_archivos(r) == ids1 and r['texto'] == r1['texto'] and not r.get('source_set_changed')
    assert cuenta['lista'] == 1 and cuenta['leer'] == lecturas  # el snapshot se crea una sola vez, no se recalcula
    # tras perder la cache en proceso se rehidrata desde la memoria con la misma seleccion
    ns['_SNAP_ANC'].clear()
    r = ns['resolver_anclados']('s', ['raiz:o/r/integration'], 'T7', 'otra cosa')
    assert _ids_archivos(r) == ids1 and cuenta['lista'] == 1
    # prepare le pasa la pregunta del payload a resolver_anclados
    assert "str(p.get('pregunta') or '')" in SRC

if __name__ == '__main__':
    n = 0
    for k, f in sorted(globals().items()):
        if k.startswith('test_') and callable(f):
            f()
            n += 1
            print('OK', k)
    print('TOTAL', n, 'tests OK')
