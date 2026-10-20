import importlib.util, os

_P = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'plugin.py')


def _mod():
    sp = importlib.util.spec_from_file_location('fichas_qwen_plugin_t', _P)
    m = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(m)
    m.FICHAS = {'f': {'ficha': 'f', 'verificacion_cruzada': {'modelos': ['a', 'b', 'c']}, 'gobernanza': {'enabled': True}}}
    m._prog = lambda *a: None
    m._meta = lambda *a: None
    m._tarea_visor = lambda *a: ''
    m._verif_cerrar = lambda *a: None
    return m


def _run(m, prep=None):
    calls, preps = [], []

    def gp(f, o, ap, es=''):
        preps.append(dict(o, _esperado=es))
        return {'constitution_hash': 'H1', 'task_id': o.get('tarea_id')}

    def lh(mod, prompt, ficha, nodo, o):
        calls.append((nodo['escribe'], o['gov_ctx'].get('constitution_hash'), prompt))
        return 'ok' + chr(10) + 'VEREDICTO: PASS'
    m._gov_prepare = prep or gp
    m._llamar_harness = lh
    r = m._verificar('f', 's', {'input': 'corrige memory_runtime', 'salida': 'x', 'tarea_id': 'T1', 'constitucion_hash': 'H1'}, 'p', 0.0)
    return r, calls, preps


def test_verificar_sin_nameerror_y_prepara_una_vez():
    r, calls, preps = _run(_mod())
    assert r['estado_tarea'] == 'VERIFICACION_CRUZADA'
    assert len(preps) == 1 and len(calls) == 3


def test_v1_v3_mismo_hash():
    _, calls, _ = _run(_mod())
    assert {c[1] for c in calls} == {'H1'}


def test_v1_v3_solo_lectura():
    _, calls, _ = _run(_mod())
    assert all(c[0] is False for c in calls)
    assert all('SOLO LECTURA' in c[2] and 'CORRECCION_N4' in c[2] for c in calls)


def test_verificar_reanuda_con_entrada_congelada_y_pregunta():
    _, _, preps = _run(_mod())
    assert preps[0]['reanudar'] is True
    assert preps[0]['_esperado'] == 'H1'
    assert preps[0]['pregunta'] == 'corrige memory_runtime'


def test_gov_prepare_envia_reanudar_al_harness():
    m = _mod()
    got = {}

    class PC:
        @staticmethod
        def gov_prepare(p):
            got.update(p)
            return {'constitution_hash': 'H1'}
    m._pc = lambda: PC
    m._gov_prepare = m.__dict__['_gov_prepare']
    m._gov_prepare({'ficha': 'f'}, {'gobernanza': {'enabled': True}, 'reanudar': True, 'pregunta': 'q', 'tarea_id': 'T'}, True, 'H1')
    assert got['reanudar'] is True and got['pregunta'] == 'q' and got['hash_esperado'] == 'H1'


def test_sin_registro_es_gap_nunca_constitucion_nueva():
    m = _mod()
    r, calls, _ = _run(m, prep=lambda f, o, ap, es='': {'error': 'GOVERNANCE_CONTEXT_NO_RECUPERABLE'})
    assert r['reply'] == 'GAP GOVERNANCE_CONTEXT_NO_RECUPERABLE' and calls == []
