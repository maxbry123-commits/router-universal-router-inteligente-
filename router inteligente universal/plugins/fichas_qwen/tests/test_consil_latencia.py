"""consil-latencia: Ask consil (Ficha 2/3) con archivo anclado.
Input trivial (<=160 chars, no habla de lo anclado) -> FAST_QA (1 llamada, anclas siguen como contexto).
Input que se refiere a lo anclado -> HEAVY (DAG). Sin red: el Harness se simula; se cuentan llamadas."""
import importlib.util, json, os, time

_D = os.path.dirname(os.path.abspath(__file__))
_P = os.path.join(_D, '..', 'plugin.py')
_F = os.path.join(_D, '..', 'fichas')
ANCLA = ['archivo:informe.md']

TRIVIALES = ['hola', 'Di solo: hola', '¿Cómo estás?', 'gracias', 'buenos días', 'ok, perfecto', '¿Qué modelo eres?', '¿Cuánto es 2+2?']
REFIEREN = ['resume el documento anclado', 'Resúmelo', 'explícalo', 'analízalo por favor', '¿qué dice el texto?', 'lee esto',
            '¿de qué trata?', 'revisa informe.md', 'según lo adjunto, ¿qué opinas?', '¿dónde está la función main?',
            'busca errores en las líneas 10-20', 'basado en eso, dame 3 ideas', 'summarize this file', 'review the attached doc',
            'compara las dos secciones', 'hola ' + 'x' * 160]


def _mod():
    sp = importlib.util.spec_from_file_location('fichas_qwen_consil_t', _P)
    m = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(m)
    for k in ('_prog', '_meta', '_ck_guardar'):
        setattr(m, k, lambda *a, **k_: None)
    m._tarea_visor = lambda *a: ''
    m._ck_cargar = lambda *a: None
    return m


def _ficha(n):
    nombre = {2: 'ficha2-dag-codigo.json', 3: 'ficha3-frontend.json'}[n]
    return json.load(open(os.path.join(_F, nombre), encoding='utf-8'))


def _opts(anclados=ANCLA, **kw):
    o = {'aprobado': False, 'muta': False, 'sesion': 's', 'cap_in': 'none', 'fast_reply': False, 'task_type': '', 'historial': '', 'tarea_id': 'T', 'caller_id': '', 'anclados': list(anclados)}
    o.update(kw)
    return o


def _nodos(f):
    return {n['id']: n for n in f.get('nodos', [])}


# 1) compuerta: trivial con anclas -> FAST en Ficha 2 y 3
def test_trivial_con_ancla_va_fast_f2_f3():
    m = _mod()
    for n in (2, 3):
        f = _ficha(n)
        for t in TRIVIALES:
            assert m._fast_multi_qa_ok(f, t, _opts(), _nodos(f)), (n, t)


# 2) compuerta: input que se refiere a lo anclado -> NO FAST (DAG)
def test_refiere_ancla_no_fast():
    m = _mod()
    for n in (2, 3):
        f = _ficha(n)
        for t in REFIEREN:
            assert not m._fast_multi_qa_ok(f, t, _opts(), _nodos(f)), (n, t)


# 3) las demas compuertas siguen mandando: cap, muta, perfil code, task_type pesado, Ficha 1 con anclas
def test_compuertas_intactas():
    m = _mod()
    f = _ficha(2)
    nd = _nodos(f)
    assert not m._fast_multi_qa_ok(f, 'hola', _opts(cap_in='read'), nd)
    assert not m._fast_multi_qa_ok(f, 'hola', _opts(muta=True), nd)
    assert not m._fast_multi_qa_ok(f, 'hola', _opts(perfil='code'), nd)
    assert not m._fast_multi_qa_ok(f, 'hola', _opts(task_type='code'), nd)
    assert not m._fast_multi_qa_ok(f, 'crea un archivo nuevo', _opts(), nd)
    assert m._fast_multi_qa_ok(f, 'hola', _opts(anclados=[]), nd)  # sin anclas: igual que antes
    f1 = {'ficha': 'ficha1-modelos', 'fast_lane': {'enabled': True}}
    assert not m._fast_multi_qa_ok(f1, 'hola', _opts(), {'N4': {}})
    assert not m._fast_chat_ok(f1, 'hola', _opts(), {'N4': {}})  # Ficha 1 con anclas: sin cambios
    assert 'ANCHORED_FILES' not in m._fast_reject_reasons(f, 'hola', _opts())
    assert 'ANCHORED_FILES' in m._fast_reject_reasons(f, 'resume el documento', _opts())


def _sim(m, f, msg, lat_s=0.0):
    llamadas = []

    def lh(modelo, prompt, ficha, n, o):
        llamadas.append({'nodo': n.get('id'), 'anclados': list(o.get('anclados') or []), 'fast': bool(o.get('fast_lane'))})
        time.sleep(lat_s)
        return 'ok'
    m._llamar_harness = lh
    m._anexo = lambda *a, **k: 'GAP SIM_HEAVY'  # el camino HEAVY se corta en el anexo de entrada (antes del DAG)
    o = _opts()
    t0 = time.perf_counter()
    r, tr = m._correr(f, msg, '', '', o)
    return r, tr, o, llamadas, time.perf_counter() - t0


# 4) simulacion _correr real: trivial -> FAST_QA, 1 llamada, con anclas como contexto
def test_sim_trivial_fast_una_llamada_con_anclas():
    m = _mod()
    for n in (2, 3):
        r, tr, o, ll, _ = _sim(m, _ficha(n), 'Di solo: hola')
        assert o.get('fast_lane') is True and o.get('fast_source') == 'AUTO'
        assert len(ll) == 1 and ll[0]['nodo'] == 'FAST' and ll[0]['fast'] is True
        assert ll[0]['anclados'] == ANCLA  # las anclas no se descartan
        assert r == 'ok' and tr[0]['nodo'] == 'FAST'


# 5) simulacion _correr real: refiere ancla -> HEAVY (no hay llamada FAST)
def test_sim_refiere_ancla_heavy():
    m = _mod()
    for n in (2, 3):
        r, tr, o, ll, _ = _sim(m, _ficha(n), 'resume el documento anclado')
        assert not o.get('fast_lane') and o.get('fast_source') == 'NONE'
        assert 'ANCHORED_FILES' in o.get('fast_reject_reasons', [])
        assert not any(x['nodo'] == 'FAST' for x in ll) and r == 'GAP SIM_HEAVY'


# 6) FAST que falla cae a HEAVY una sola vez (sin segundo FAST)
def test_sim_fast_gap_cae_a_heavy():
    m = _mod()
    m._fast_qa = lambda *a, **k: ('GAP FAST (x): timeout', [])
    m._anexo = lambda *a, **k: 'GAP SIM_HEAVY'
    o = _opts()
    r, _ = m._correr(_ficha(2), 'hola', '', '', o)
    assert o.get('fast_fallback') is True and r == 'GAP SIM_HEAVY'
