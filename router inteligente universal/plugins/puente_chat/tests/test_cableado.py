"""Pruebas deterministas del cableado: politicas por modelo, bucle de herramientas, Sentinela de 5 vueltas,
aprobacion de plan, N7 sin ocultar GAP, max_parallel. No llaman a ningun modelo ni a la red."""
import copy
import importlib.util
import json
import sys
import threading
import time
from pathlib import Path

PLUG = Path(__file__).resolve().parents[2]


def _cargar(nombre, ruta):
    spec = importlib.util.spec_from_file_location(nombre, str(ruta))
    m = importlib.util.module_from_spec(spec)
    sys.modules[nombre] = m
    spec.loader.exec_module(m)
    return m


pc = _cargar('puente_chat_test', PLUG / 'puente_chat' / 'plugin.py')
se = _cargar('sentinela_test', PLUG / 'puente_chat' / 'fichas' / 'sentinela.py')
fq = _cargar('fichas_qwen_test', PLUG / 'fichas_qwen' / 'plugin.py')


def _tool(nombre, req):
    return {'type': 'function', 'function': {'name': nombre, 'description': 'd', 'parameters': {'type': 'object', 'properties': {r: {'type': 'string'} for r in req}, 'required': req}}}


TOOLS = [_tool('github_leer', ['repo', 'ruta']), _tool('github_escribir', ['repo', 'ruta', 'contenido']),
         _tool('github_api', ['metodo', 'ruta']), _tool('hf_almacenamiento', ['accion'])]


class Herr:
    SISTEMA = 'x'

    def __init__(self):
        self.TOOLS = TOOLS
        self.llamadas = []

    def ejecutar(self, nom, args):
        self.llamadas.append(nom)
        return 'OK ' + nom


def resp(content='', calls=None, reasoning=None):
    m = {'role': 'assistant', 'content': content}
    if calls:
        m['tool_calls'] = [{'id': 'c%d' % i, 'type': 'function', 'function': {'name': n, 'arguments': json.dumps(a)}} for i, (n, a) in enumerate(calls)]
    if reasoning:
        m['reasoning_content'] = reasoning
    return 200, {'choices': [{'message': m}]}


def bucle(respuestas, herr, pol=None, req=False, vistos=None, solo_lectura=False):
    pc._herr = lambda: herr
    pc._DEADLINE.set(time.monotonic() + 30)
    pc._REQ_TOOLS.set(req)
    pc._SOLO_LECTURA.set(solo_lectura)
    pc._VISTOS.set(vistos if vistos is not None else {})
    it = iter(respuestas)
    vistos_msgs = []

    def llamar(ms, tl):
        pc._POL.set(pol or {})
        vistos_msgs.append([dict(m) for m in ms])
        return next(it)
    d, usadas = pc._bucle(llamar, [{'role': 'user', 'content': 'hola'}])
    return d, usadas, vistos_msgs


LEER = {'repo': 'r', 'ruta': 'x'}
ESCR = {'repo': 'r', 'ruta': 'x', 'contenido': 'c'}


# ---------- Sentinela: 5 vueltas por tarea ----------
def _paso(fallos, err='MODELO_NO_RESPONDE', det='HTTP 503 x'):
    est = {'n': 0}

    def paso(ms):
        est['n'] += 1
        if est['n'] <= fallos:
            return {'error': err, 'detalle': det}, []
        return {'choices': [{'message': {'content': 'ok'}}]}, []
    return paso, est


def test_01_pass_primera_vuelta():
    p, e = _paso(0)
    cl = se.ejecutar([('t', p)], [])
    assert cl['completada'] and cl['estado'] == 'PASS' and e['n'] == 1


def test_02_fail_luego_pass_vuelta_2():
    p, e = _paso(1)
    cl = se.ejecutar([('t', p)], [])
    assert cl['completada'] and e['n'] == 2


def test_03_fail_cuatro_veces_pass_vuelta_5():
    p, e = _paso(4)
    cl = se.ejecutar([('t', p)], [])
    assert cl['completada'] and e['n'] == 5 and se.MAX_VUELTAS == 5


def test_04_fail_cinco_veces_gap_final():
    p, e = _paso(99)
    cl = se.ejecutar([('t', p)], [])
    assert (not cl['completada']) and cl['estado'] == 'GAP_FINAL' and e['n'] == 5
    assert cl['items'][-1]['estado'] == 'GAP_FINAL'


def test_05_error_definitivo_no_gasta_vueltas():
    p, e = _paso(99, det='HTTP 401 sin acceso')
    cl = se.ejecutar([('t', p)], [])
    assert (not cl['completada']) and e['n'] == 1 and cl['estado'] == 'GAP_FINAL'


# ---------- Harness: escrituras, solo lectura, evidencia ----------
def test_06_escritura_ya_hecha_no_se_repite():
    h = Herr()
    comun = {}
    d1, u1, _ = bucle([resp(calls=[('github_escribir', ESCR)]), resp('listo')], h, vistos=comun)
    d2, u2, m2 = bucle([resp(calls=[('github_escribir', ESCR)]), resp('listo')], h, vistos=comun)
    assert h.llamadas.count('github_escribir') == 1
    assert any('OPERACION_YA_COMPLETADA' in str(m.get('content')) for m in m2[1])
    assert u1[0]['mutacion_real'] is True and u2[0]['mutacion_real'] is False


def test_07_solo_lectura_y_mutacion_real():
    pc._SOLO_LECTURA.set(True)
    try:
        assert pc._bloqueo('hf_almacenamiento', {'accion': 'listar'}) == ''
        assert pc._bloqueo('hf_almacenamiento', {'accion': 'leer'}) == ''
        assert 'HERRAMIENTA_BLOQUEADA' in pc._bloqueo('hf_almacenamiento', {'accion': 'escribir'})
        assert pc._bloqueo('github_api', {'metodo': 'GET'}) == ''
        assert 'HERRAMIENTA_BLOQUEADA' in pc._bloqueo('github_api', {'metodo': 'PATCH'})
        assert 'HERRAMIENTA_BLOQUEADA' in pc._bloqueo('github_escribir', ESCR)
        assert pc._bloqueo('github_leer', LEER) == ''
    finally:
        pc._SOLO_LECTURA.set(False)
    assert not pc._es_mutacion('hf_almacenamiento', {'accion': 'listar'}) and pc._es_mutacion('hf_almacenamiento', {'accion': 'escribir'})
    assert not pc._es_mutacion('github_api', {'metodo': 'GET'}) and pc._es_mutacion('github_api', {'metodo': 'PUT'})


def test_08_400_con_tools_es_gap_si_la_tarea_las_exige():
    h = Herr()
    d, _, _ = bucle([(400, {'error': 'tools no soportadas'})], h, req=True)
    assert d['error'] == 'GAP MODELO_SIN_TOOLS'
    d2, _, _ = bucle([(400, {'error': 'tools no soportadas'}), resp('texto')], h, req=False)
    assert 'choices' in d2  # conversacion normal: puede responder texto


def test_09_campos_requeridos_y_reparacion():
    h = Herr()
    d, _, _ = bucle([resp(calls=[('github_escribir', {})]), resp(calls=[('github_escribir', {})])], h)
    assert d['error'] == 'GAP TOOL_ARGUMENTS_INCOMPLETOS' and h.llamadas == []
    h2 = Herr()
    d2, _, _ = bucle([resp(calls=[('github_escribir', {})]), resp(calls=[('github_escribir', ESCR)]), resp('fin')], h2)
    assert 'choices' in d2 and h2.llamadas == ['github_escribir']


# ---------- Politicas por modelo ----------
def test_10_deepseek_conserva_reasoning_content():
    h = Herr()
    pol = {'conservar_reasoning_content_con_tools': True}
    _, _, ms = bucle([resp(calls=[('github_leer', LEER)], reasoning='pienso'), resp('fin')], h, pol=pol)
    asis = [m for m in ms[1] if m.get('role') == 'assistant' and m.get('tool_calls')]
    assert asis and asis[0].get('reasoning_content') == 'pienso'
    _, _, ms2 = bucle([resp(calls=[('github_leer', LEER)], reasoning='pienso'), resp('fin')], Herr(), pol={})
    assert 'reasoning_content' not in [m for m in ms2[1] if m.get('tool_calls')][0]
    d, _, _ = bucle([(400, {'error': {'message': 'reasoning_content must be passed back'}})], Herr())
    assert d['error'] == 'GAP HISTORIAL_DEEPSEEK_INCOMPLETO'


def test_11_parser_de_llamadas_en_texto():
    inv = '<invoke name="github_leer"><parameter name="repo">r</parameter><parameter name="ruta">x</parameter></invoke>'
    assert pc._calls_texto(inv) == [('github_leer', LEER)]
    js = json.dumps({'name': 'github_leer', 'arguments': LEER})
    assert pc._calls_texto(js, {'github_leer'}) == [('github_leer', LEER)]
    assert pc._calls_texto(json.dumps({'name': 'otra', 'arguments': {}}), {'github_leer'}) == []
    assert pc._calls_texto(json.dumps({'a': 1}), {'github_leer'}) == []
    assert pc._calls_texto('<tool_call>' + js + '</tool_call>') == [('github_leer', LEER)]
    h = Herr()
    pol = {'buscar_tool_calls_en': ['tool_calls', 'content', 'reasoning_content']}
    bucle([resp('', reasoning='<tool_call>' + js + '</tool_call>'), resp('fin')], h, pol=pol)
    assert h.llamadas == ['github_leer']  # Qwen 3.6: llamada dentro del razonamiento
    h2 = Herr()
    bucle([resp('', reasoning='<tool_call>' + js + '</tool_call>'), resp('fin')], h2, pol={})
    assert h2.llamadas == []


def test_12_anti_loop_qwen36():
    h = Herr()
    c = resp(calls=[('github_leer', LEER)])
    _, _, ms = bucle([c, c, c, resp('fin')], h, pol={'anti_loop': {'x': 1}})
    assert h.llamadas == ['github_leer']
    assert any('REPETICION_TOOL_DETECTADA' in str(m.get('content')) for m in ms[3])


def test_13_politica_llega_a_la_peticion_http():
    capt = []

    def http(met, url, token, cuerpo, espera):
        capt.append(copy.deepcopy(cuerpo))
        return 200, {'choices': [{'message': {'content': 'ok'}}]}
    pc._qwen_conf = lambda: ('k', 'http://base')
    pc._http = http
    pc._POL_CACHE.clear()
    msg = [{'role': 'user', 'content': 'x'}]
    pc._llamar_api('qwencloud', 'glm-5.2', msg, 100, 30, TOOLS)
    assert capt[-1].get('tool_stream') is True and capt[-1].get('clear_thinking') is True and 'top_p' not in capt[-1]
    pc._llamar_api('qwencloud', 'deepseek-v4-pro', msg, 100, 30, TOOLS)
    assert capt[-1].get('top_p') == 0.95 and 'tool_stream' not in capt[-1]
    pc._llamar_api('qwencloud', 'deepseek-v4-flash-0731', msg, 100, 30, TOOLS)
    assert capt[-1].get('top_p') == 0.95
    pc._llamar_api('qwencloud', 'qwen3.8-flash', msg, 100, 30, TOOLS)
    assert capt[-1].get('preserve_thinking') is True and capt[-1].get('reasoning_effort') == 'medium' and 'enable_thinking' not in capt[-1]
    pc._llamar_api('qwencloud', 'qwen3.6-flash', msg, 100, 30, TOOLS)
    assert not ({'tool_stream', 'top_p', 'preserve_thinking', 'clear_thinking'} & set(capt[-1]))
    pc._llamar_api('qwencloud', 'qwen3.7-max', msg, 100, 30, TOOLS)
    assert not ({'tool_stream', 'top_p', 'preserve_thinking', 'clear_thinking'} & set(capt[-1]))
    # si el endpoint rechaza un extra: mismo modelo y misma clave, sin extras
    capt.clear()

    def http400(met, url, token, cuerpo, espera):
        capt.append(copy.deepcopy(cuerpo))
        if 'tool_stream' in cuerpo:
            return 400, {'error': 'parametro desconocido'}
        return 200, {'choices': [{'message': {'content': 'ok'}}]}
    pc._http = http400
    s, d = pc._llamar_api('qwencloud', 'glm-5.2', msg, 100, 30, TOOLS)
    assert s == 200 and len(capt) == 2 and capt[0]['model'] == capt[1]['model'] == 'glm-5.2' and 'tool_stream' not in capt[1]


# ---------- Motor de fichas: /aprobar, N0/N5, N6/N7, GAP, paralelo ----------
LLAM = []
ROL = {}


def _llh(modelo, prompt, ficha, n, opts):
    nid = n['id']
    LLAM.append((opts.get('sesion'), nid, prompt))
    f = ROL.get(nid)
    if callable(f):
        return f(prompt, opts)
    return 'salida ' + nid


fq._llamar_harness = _llh


def _n(ses, nid):
    return [p for s, n, p in LLAM if s == ses and n == nid]


def _chat(ses, msg):
    return fq._chat({'ficha_qwen': '2', 'message': msg, 'sesion': ses, 'modelo': 'ficha-qwen38max'})


def test_14_aprobar_retoma_la_misma_tarea():
    ROL.clear()
    ROL['N4'] = lambda p, o: ('EJECUTADO' if o.get('aprobado') else 'PLAN: editar x' + chr(10) + 'ESPERANDO_APROBACION')
    ROL['N6'] = lambda p, o: 'revisado' + chr(10) + 'VEREDICTO: PASS'
    ROL['N7'] = lambda p, o: _full('ok') + chr(10) + 'VEREDICTO: PASS'
    r = _chat('s14', 'corrige el Router')
    assert 'ESPERANDO_APROBACION' in r['reply'] and r['estado_tarea'] == 'ESPERANDO_APROBACION'
    assert [len(_n('s14', k)) for k in ('N1', 'N2', 'N3', 'N4')] == [1, 1, 1, 1] and not _n('s14', 'N6') and not _n('s14', 'N7')
    r2 = _chat('s14', '/aprobar')
    assert [len(_n('s14', k)) for k in ('N1', 'N2', 'N3')] == [1, 1, 1]  # N1/N2/N3 no se repiten
    assert len(_n('s14', 'N4')) == 2 and 'PLAN APROBADO POR EL DIRECTOR' in _n('s14', 'N4')[1] and 'corrige el Router' in _n('s14', 'N4')[1]
    assert r2['reply'] == _full('ok') and 'VEREDICTO' not in r2['reply']
    assert 'PLAN / RESULTADO ESPERADO' in _n('s14', 'N6')[0] and 'INPUT LITERAL DEL DIRECTOR' in _n('s14', 'N1')[0]
    r3 = _chat('s14', '/aprobar')
    assert r3['reply'].startswith('GAP SIN_PLAN_PENDIENTE')  # la tarea ya se cerro


def test_15_n6_fail_devuelve_control_a_n4():
    ROL.clear()
    cuenta = {'n6': 0}

    def n6(p, o):
        cuenta['n6'] += 1
        return 'VEREDICTO: FAIL: falta X' if cuenta['n6'] == 1 else 'VEREDICTO: PASS'
    ROL['N4'] = lambda p, o: ('EJECUTADO' if o.get('aprobado') else 'PLAN' + chr(10) + 'ESPERANDO_APROBACION')
    ROL['N6'] = n6
    ROL['N7'] = lambda p, o: _full('final') + chr(10) + 'VEREDICTO: PASS'
    _chat('s15', 'corrige el Router')
    r = _chat('s15', '/aprobar')
    assert len(_n('s15', 'N4')) == 3 and len(_n('s15', 'N6')) == 2 and r['reply'] == _full('final')
    assert 'CORRECCION PEDIDA POR EL VERIFICADOR' in _n('s15', 'N4')[2] and 'falta X' in _n('s15', 'N4')[2]
    assert len(_n('s15', 'N1')) == 1


def test_16_n7_fail_no_se_oculta():
    ROL.clear()
    ROL['N4'] = lambda p, o: ('EJECUTADO' if o.get('aprobado') else 'PLAN' + chr(10) + 'ESPERANDO_APROBACION')
    ROL['N6'] = lambda p, o: 'VEREDICTO: PASS'
    ROL['N7'] = lambda p, o: 'defecto grave' + chr(10) + 'VEREDICTO: FAIL: no cumple X'
    _chat('s16', 'corrige el Router')
    r = _chat('s16', '/aprobar')
    assert r['reply'].startswith('GAP FINAL') and 'defecto grave' in r['resultado_parcial']
    ROL['N7'] = lambda p, o: (_ for _ in ()).throw(RuntimeError('boom'))
    ROL['N6'] = lambda p, o: 'verificado bien'
    r2 = _chat('s16b', 'analiza el router')
    assert r2['reply'].startswith('GAP FINAL') and r2['resultado_parcial'] == 'verificado bien'


def test_17_max_parallel_se_obedece():
    ROL.clear()
    est = {'act': 0, 'max': 0}
    lock = threading.Lock()

    def lento(p, o):
        with lock:
            est['act'] += 1
            est['max'] = max(est['max'], est['act'])
        time.sleep(0.05)
        with lock:
            est['act'] -= 1
        return 'ok'
    for k in ('N1', 'N2', 'N3'):
        ROL[k] = lento
    base = fq.FICHAS['ficha2-dag-codigo']
    f1 = copy.deepcopy(base)
    f1['dsl']['parallel']['max_parallel'] = 1
    fq._correr(f1, 'analiza el router', 'ficha-qwen38max', '', {'sesion': 'p1'})
    assert est['max'] == 1
    est['max'] = 0
    fq._correr(copy.deepcopy(base), 'analiza el router', 'ficha-qwen38max', '', {'sesion': 'p2'})
    assert est['max'] == 3


def test_18_dos_tareas_en_paralelo_no_se_pisan():
    ROL.clear()

    def juez(p, o):
        return _full(p.split('(INPUT BLOCK VERBATIM):' + chr(10), 1)[1].split(chr(10), 1)[0])
    ROL['N7'] = juez
    res = {}

    def corre(ses, msg):
        res[ses] = _chat(ses, msg)['reply']
    ts = [threading.Thread(target=corre, args=('pa', 'analiza TAREA-A')), threading.Thread(target=corre, args=('pb', 'analiza TAREA-B'))]
    [t.start() for t in ts]
    [t.join() for t in ts]
    assert res['pa'] == _full('analiza TAREA-A') and res['pb'] == _full('analiza TAREA-B')


def _full(t):
    return chr(10).join(['MICRO RESUMEN ' + t, 'MICRO FLUJO a > b', 'RESULTADO ok', 'CHECKLIST ok', 'EVIDENCIA commit'])


def _plan_o_exec(p, o):
    return 'EJECUTADO' if o.get('aprobado') else 'PLAN' + chr(10) + 'ESPERANDO_APROBACION'


def test_19_detector_de_mutacion():
    si = ['corrige el Router', 'modifica la ficha', 'agrega un campo', 'anade validacion', 'añade validación', 'mejora el parser',
          'cablea las politicas', 'haz los cambios', 'implementar el loop', 'integra el modulo', 'refactoriza plugin',
          'elimina ese archivo', 'quita el limite', 'sube el archivo', 'sincroniza los repos', 'Edita ficha2', 'arreglalo ya',
          'construye el modulo', 'programa el parser', 'desarrolla la funcion', 'monta el plugin', 'conecta el harness', 'duplica la ficha',
          'clona el repo', 'habilita tool_stream', 'desactiva el fallback', 'optimiza el contexto', 'ajusta los tiempos', 'repara el bug',
          'soluciona el error', 'reescribe el prompt', 'amplia el limite', 'inserta una linea', 'sustituye el modelo',
          'quiero que modifiques la ficha', 'necesito que corrijas el bug', 'hazlo ahora', 'haz que funcione', 'add a field',
          'remove the limit', 'rename the file']
    no = ['analiza el router', 'explica como funciona el harness', 'revisa el mejor modelo', 'que cambios hizo claude',
          'lista los archivos', 'documentos del proyecto', 'revisa el cableado', 'que modificacion hizo',
          'la ficha activa', 'como se ejecuta N4', 'el router genera salida', 'una copia del archivo', 'quien arma el dag', 'que hace el modulo']
    assert all(fq._muta(x) for x in si), [x for x in si if not fq._muta(x)]
    assert not any(fq._muta(x) for x in no), [x for x in no if fq._muta(x)]


def test_20_perfiles_de_contexto_y_pasos():
    largo = 'x' * 6000
    ms = [{'role': 'system', 'content': 's'}, {'role': 'user', 'content': 'u'},
          {'role': 'assistant', 'content': '', 'tool_calls': [{'id': 'a', 'type': 'function', 'function': {'name': 'github_leer', 'arguments': '{}'}}]},
          {'role': 'tool', 'tool_call_id': 'a', 'content': largo}]
    grande = [{'role': 'system', 'content': 's'}] + [{'role': 'user', 'content': 'y' * 3000} for _ in range(10)]
    try:
        pc._PERFIL.set('normal')
        assert len([m for m in pc._recortar(ms) if m['role'] == 'tool'][0]['content']) < 3200
        n_norm = len(pc._recortar(grande))
        pc._PERFIL.set('code')
        assert len([m for m in pc._recortar(ms) if m['role'] == 'tool'][0]['content']) == 6000
        n_code = len(pc._recortar(grande))
        pc._PERFIL.set('auditoria')
        n_aud = len(pc._recortar(grande))
        assert n_norm < n_code == n_aud == 11, (n_norm, n_code, n_aud)
        for perfil, esperado in (('normal', 6), ('code', 14), ('auditoria', 20)):
            pc._PERFIL.set(perfil)
            h = Herr()
            rs = [resp(calls=[('github_leer', {'repo': 'r', 'ruta': 'f%d' % i})]) for i in range(25)] + [resp('fin')]
            bucle(rs, h)
            assert len(h.llamadas) == esperado, (perfil, len(h.llamadas))
    finally:
        pc._PERFIL.set('normal')


def test_21_aprobar_sin_plan_no_ejecuta_nada():
    ROL.clear()
    r = _chat('s21', '/aprobar corrige el Router')
    assert r['reply'].startswith('GAP SIN_PLAN_PENDIENTE') and not _n('s21', 'N4')


def test_22_validador_de_formato_final():
    ROL.clear()
    c = {'n7': 0}

    def n7(p, o):
        c['n7'] += 1
        return ('MICRO RESUMEN solo' if 'REFORMATEA' not in p else _full('ok')) + chr(10) + 'VEREDICTO: PASS'
    ROL['N4'] = _plan_o_exec
    ROL['N6'] = lambda p, o: 'VEREDICTO: PASS'
    ROL['N7'] = n7
    _chat('s22', 'corrige el Router')
    r = _chat('s22', '/aprobar')
    assert c['n7'] == 2 and r['reply'] == _full('ok')
    ROL['N7'] = lambda p, o: 'MICRO RESUMEN solo' + chr(10) + 'VEREDICTO: PASS'
    _chat('s22b', 'corrige el Router')
    r2 = _chat('s22b', '/aprobar')
    assert r2['reply'].startswith('GAP FORMATO_SALIDA') and 'MICRO RESUMEN solo' in r2['resultado_parcial']


def test_23_cinco_correcciones_con_tope_de_tiempo():
    ROL.clear()
    assert fq.FICHAS['ficha2-dag-codigo']['loop']['correcciones'] == 5 and fq.FICHAS['ficha3-frontend']['loop']['correcciones'] == 5
    assert fq.FICHAS['ficha2-dag-codigo']['loop']['max_segundos'] == 600 and fq.FICHAS['ficha3-frontend']['loop']['max_segundos'] == 600
    c = {'n': 0}

    def n6(p, o):
        c['n'] += 1
        return 'VEREDICTO: FAIL: falta X' if c['n'] <= 3 else 'VEREDICTO: PASS'
    ROL['N4'] = _plan_o_exec
    ROL['N6'] = n6
    ROL['N7'] = lambda p, o: _full('ok') + chr(10) + 'VEREDICTO: PASS'
    _chat('s23', 'corrige el Router')
    r = _chat('s23', '/aprobar')
    assert len(_n('s23', 'N4')) == 5 and len(_n('s23', 'N6')) == 4 and r['reply'] == _full('ok')
    ROL['N6'] = lambda p, o: 'VEREDICTO: FAIL: sigue mal'
    _chat('s23b', 'corrige el Router')
    _chat('s23b', '/aprobar')
    assert len(_n('s23b', 'N4')) == 7 and len(_n('s23b', 'N6')) == 6
    f = copy.deepcopy(fq.FICHAS['ficha2-dag-codigo'])
    f['loop']['max_segundos'] = 1e-9
    fq._correr(f, 'corrige x', 'ficha-qwen38max', '', {'sesion': 's23c', 'aprobado': True, 'muta': True})
    assert len(_n('s23c', 'N4')) == 1


def test_24_n6_n7_son_solo_lectura_tambien_en_la_metadata():
    for k in ('ficha2-dag-codigo', 'ficha3-frontend'):
        nd = {n['id']: n for n in fq.FICHAS[k]['nodos']}
        for i in ('N6', 'N7'):
            assert not nd[i].get('write_paths') and not nd[i].get('locks'), (k, i)
        assert nd['N4'].get('write_paths') and nd['N4'].get('locks'), k


def test_25_formato_obligatorio_tambien_en_auditoria_de_solo_lectura():
    ROL.clear()
    ROL['N7'] = lambda p, o: 'respuesta sin formato'
    r = _chat('s25', 'analiza el router')
    assert r['reply'].startswith('GAP FORMATO_SALIDA') and r['resultado_parcial'] == 'respuesta sin formato'
    ROL['N7'] = lambda p, o: _full('auditoria') if 'REFORMATEA' in p else 'respuesta sin formato'
    assert _chat('s25b', 'analiza el router')['reply'] == _full('auditoria')
    for k in ('ficha2-dag-codigo', 'ficha3-frontend'):
        rol7 = [n for n in fq.FICHAS[k]['nodos'] if n['id'] == 'N7'][0]['rol']
        assert 'solo tareas de trabajo o code' not in rol7 and 'auditoria de solo lectura' in rol7


if __name__ == '__main__':
    fallos = 0
    for nombre, f in sorted(globals().items()):
        if nombre.startswith('test_') and callable(f):
            try:
                f()
                print('PASS', nombre)
            except Exception as e:  # noqa: BLE001
                fallos += 1
                import traceback
                print('FAIL', nombre, repr(e)[:300])
                traceback.print_exc(limit=3)
    print('TOTAL FALLOS:', fallos)
    sys.exit(1 if fallos else 0)
