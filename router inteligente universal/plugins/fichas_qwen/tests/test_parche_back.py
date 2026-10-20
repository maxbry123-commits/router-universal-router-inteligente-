"""PARCHE_BACK offline (handoff 18 GAPs, backend): G03 G05 G06 G07 G10 G11 G12 G15 G16. Sin red; memoria falsa en RAM.
Desde 'router inteligente universal/':  PYTHONPATH=. python3 -I plugins/fichas_qwen/tests/test_parche_back.py"""
import hashlib
import json
import sys
import time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import plugins.puente_chat.plugin as pc  # noqa: E402
import plugins.fichas_qwen.plugin as fq  # noqa: E402


class Mem:
    def __init__(self):
        self.d = {}
        self.rota = False

    def save(self, scope, key, data):
        if self.rota:
            raise OSError('memoria caida')
        self.d.setdefault((scope, key), []).insert(0, {'data': dict(data)})

    def load(self, scope, key):
        if self.rota:
            raise OSError('memoria caida')
        return list(self.d.get((scope, key), []))

    def search(self, scope, q, k=5):
        return [r for (s, _), rows in self.d.items() if s == scope for r in rows][:k]


MEM = Mem()
pc._memoria = lambda: (MEM, lambda dueno, nombre: '%s|%s' % (dueno, nombre))
sha = lambda t: hashlib.sha256(t.encode('utf-8')).hexdigest()  # noqa: E731


# ---------------- G03 ----------------
def test_g03_resolver_positivo_un_solo_control():
    r = pc.thinking_mode_resolver('qwen3.8-flash', 'on')
    assert r == {'ok': True, 'extra': {'reasoning_effort': 'medium'}}
    assert pc.thinking_mode_resolver('qwen3.8-flash', {'mode': 'on', 'effort': 'high'})['extra'] == {'reasoning_effort': 'high'}
    assert pc.thinking_mode_resolver('qwen3.8-flash', 'off')['extra'] == {'enable_thinking': False}
    assert pc.thinking_mode_resolver('deepseek-v4-flash', True)['extra'] == {'enable_thinking': True}
    assert pc.thinking_mode_resolver('qwen3.8-flash', 'auto') == {'ok': True, 'extra': None}
    assert pc.thinking_mode_resolver('qwen3.8-flash', None) == {'ok': True, 'extra': None}
    for m in ('qwen3.8-flash', 'deepseek-v4-flash', 'glm-5.2'):
        for v in ('on', 'off', True, False):
            ex = pc.thinking_mode_resolver(m, v, False).get('extra') or {}
            assert not ({'enable_thinking', 'reasoning_effort'} <= set(ex)), (m, v, ex)


def test_g03_resolver_negativo_unsupported_e_invalido():
    assert pc.thinking_mode_resolver('qwen3.8-flash', 'on', True)['error'] == 'GAP_THINKING_UNSUPPORTED'  # con tools sin prueba: no falso ON
    assert pc.thinking_mode_resolver('nvidia/nemotron-3-super-120b-a12b', 'on')['error'] == 'GAP_THINKING_UNSUPPORTED'
    assert pc.thinking_mode_resolver('llama-3.3-70b', 'off')['error'] == 'GAP_THINKING_UNSUPPORTED'
    assert pc.thinking_mode_resolver('llama-3.3-70b', 'on')['error'] == 'GAP_THINKING_UNSUPPORTED'
    for malo in ('quizas', 3, {'mode': 'on', 'effort': 'ultra'}, {'mode': 'off', 'effort': 'low'}, {'x': 1}, []):
        assert pc.thinking_mode_resolver('qwen3.8-flash', malo)['error'] == 'GAP_THINKING_INVALID', malo


def _harness(thinking_mode, requiere_tools=False, modelo='ficha-qwen38flash'):
    vistos = []
    orig = pc._chat
    pc._chat = lambda payload: (vistos.append(payload), {'choices': [{'message': {'content': 'ok'}}]})[1]
    try:
        ficha = fq.FICHAS['ficha1-modelos']
        n = {'id': 'N1', 'timeout_s': 10, 'max_output_tokens': 500, 'requiere_tools': requiere_tools}
        opts = {'thinking_mode': thinking_mode, 'fid': 'ficha1-modelos', 'herr': {}, 'cap_in': 'read' if requiere_tools else 'none', 'sesion': 's'}
        try:
            return fq._llamar_harness_1(modelo, 'hola', ficha, n, opts), vistos, None
        except RuntimeError as x:
            return None, vistos, str(x)
    finally:
        pc._chat = orig


def test_g03_payload_backend_on_off_y_unsupported():
    _, v, e = _harness('off')
    assert e is None and v[0]['extra_llm'] == {'enable_thinking': False}, (e, v)
    _, v, e = _harness('on')
    assert e is None and v[0]['extra_llm'] == {'reasoning_effort': 'medium'}, (e, v)
    _, v, e = _harness('on', requiere_tools=True)  # con tools: GAP, nunca se manda un ON que el backend no respeta
    assert e and e.startswith('GAP_THINKING_UNSUPPORTED') and not v, (e, v)
    r = fq._chat({'ficha_qwen': 'ficha1-modelos', 'message': 'hola', 'thinking_mode': 'quizas'})
    assert r.get('error') == 'GAP_THINKING_INVALID'


# ---------------- G05 ----------------
def test_g05_entrada_larga_80k_unicode_sha_readback_reensamblado():
    t = ('Ñandú 日本語 😀  espacios\t\n' * 4000)[:80001] + ' fin'
    assert len(t) > 80000
    r = fq._fuente_integra_guardar('sesA', t, 40000)
    assert r['ok'] and r['sha256'] == sha(t) == r['readback_sha'] and r['segmentos'] == 3 and r['chars'] == len(t)
    assert ''.join(fq._segmentar_integro(t, 40000)) == t
    fila = MEM.load('chat-ui|fuente:sesA', 'fuente:' + r['sha256'])[0]['data']
    assert fila['texto'] == t  # literal, sin trim ni ventana
    assert len(fq._hist_txt(t)) == 12000  # el historial abreviado sigue siendo otra cosa
    assert fq._hist_txt(t) != t


def test_g05_readback_distinto_es_gap_no_silencio():
    MEM.rota = True
    try:
        assert fq._fuente_integra_guardar('sesB', 'x' * 100)['error'] == 'GAP_FUENTE_NO_VERIFICADA'
    finally:
        MEM.rota = False


# ---------------- G06 ----------------
def test_g06_presupuesto_min_de_nodo_proveedor_tarea():
    assert fq._presupuesto_salida(1500, None, None, 0) == {'max_tokens': 1500, 'limitado_por': 'nodo'}
    assert fq._presupuesto_salida(1500, 1000, None, 0)['limitado_por'] == 'proveedor'
    assert fq._presupuesto_salida(1500, 8000, 4000, 3200) == {'max_tokens': 800, 'limitado_por': 'presupuesto_tarea'}
    assert fq._presupuesto_salida(500, None, 99999, 0)['max_tokens'] == 500  # fast_lane ya aplicado al nodo: el presupuesto no lo sube
    assert fq._presupuesto_salida(1500, None, 4000, 4000)['error'] == 'GAP_TASK_TOKEN_BUDGET_AGOTADO'
    assert fq._presupuesto_salida('x', None, None, 0)['error'] == 'GAP_TOKENS_INVALIDOS'


def test_g06_tres_segmentos_con_hashes_y_cero_pass_prematuro():
    fq._ck_guardar = lambda *a, **k: None
    guion = ['tool p1\nCONTINUAR_PARTE', 'tool p2\nCONTINUAR_PARTE', 'tool p3\nTAREA_COMPLETA']
    ll = []

    def fake(modelo, pedido, ficha, n, opts):
        a = guion[len(ll)]
        ll.append(1)
        opts['herr'].setdefault('N4', []).append({'herramienta': 'github_escribir', 'ok': True, 'mutacion_real': True})
        opts['tokens_usados'] = opts.get('tokens_usados', 0) + 100
        return a.replace('tool ', '')
    fq._llamar_harness_3 = fake
    opts = {'herr': {'N4': []}, 'out': {}, 'pid': 'p', 'fid': 'f', 'aprobado': True, 'muta': True, 'cap_in': 'write'}
    r = fq._llamar_con_partes('m', 'haz X', {'loop': {}}, {'id': 'N4'}, opts)
    ens = opts['loop_ensamblado']['N4']
    assert ens['segmentos'] == 3 and len(ens['sha_piezas']) == 3 and ens['sha'] == sha(r) and ens['tokens_usados'] == 300
    # negativo: terminar sin TAREA_COMPLETA nunca devuelve resultado
    ll.clear()
    guion[:] = ['tool a\nCONTINUAR_PARTE'] * 5
    opts2 = {'herr': {'N4': []}, 'out': {}, 'pid': 'p', 'fid': 'f', 'aprobado': True, 'muta': True, 'cap_in': 'write'}
    try:
        fq._llamar_con_partes('m', 'haz X', {'loop': {'max_partes_codigo': 2}}, {'id': 'N4'}, opts2)
        raise AssertionError('PASS prematuro')
    except RuntimeError as x:
        assert str(x).startswith('GAP_LOOP_MAX_PARTES')


# ---------------- G07 ----------------
def _sse(chunks, termina):
    class R:
        status = 200

        def __iter__(self):
            for c in chunks:
                yield c.encode()
            if termina:
                yield b'data: [DONE]\n'
        def __enter__(self): return self
        def __exit__(self, *a): return False
        def read(self, *a): return b''
    return R()


def test_g07_stream_cortado_guarda_parcial_y_loop_lo_trata_como_corte():
    fq._ck_guardar = lambda *a, **k: None
    vistos = []
    orig = pc._chat
    n_llam = []

    def chat(payload):
        n_llam.append(1)
        if len(n_llam) == 1:
            return {'error': 'GAP_STREAM_INTERRUPTED', 'parcial': '{"ops":[{"id":"T1","op":"wri'}
        return {'choices': [{'message': {'content': 'listo\nTAREA_COMPLETA'}}],
                'herramientas': [{'herramienta': 'github_escribir', 'tool': 'github_escribir', 'ok': True, 'mutacion_real': True, 'receipt_id': 'tr-1', 'status': 'OK'}]}
    pc._chat = chat
    try:
        fq._llamar_harness_3 = lambda m, p, f, n, o: fq._llamar_harness_1(m, p, f, n, o)
        opts = {'herr': {'N4': []}, 'out': {}, 'pid': 'p', 'fid': 'ficha1-modelos', 'aprobado': True, 'muta': True, 'cap_in': 'write', 'sesion': 's'}
        n = {'id': 'N4', 'timeout_s': 10, 'max_output_tokens': 500, 'requiere_tools': True, 'escribe': True}
        r = fq._llamar_con_partes('ficha-qwen38flash', 'haz X', dict(fq.FICHAS['ficha1-modelos'], loop={}), n, opts)
    finally:
        pc._chat = orig
    assert len(n_llam) == 2 and 'listo' in r and 'wri' not in r
    assert opts['herr']['N4'][0]['receipt_id'] == 'tr-1' and opts['herr']['N4'][0]['status'] == 'OK'


def test_g07_length_dos_veces_y_una_sola_ejecucion_por_mutacion():
    class H:
        SISTEMA = 'x'
        TOOLS = [{'type': 'function', 'function': {'name': 'github_escribir', 'description': 'd', 'parameters': {'type': 'object', 'properties': {k: {'type': 'string'} for k in ('repo', 'ruta', 'contenido')}, 'required': ['repo', 'ruta', 'contenido']}}}]
        llamadas = []

        def ejecutar(self, nom, args):
            self.llamadas.append(nom)
            return 'OK ' + nom
    h = H()
    pc._herr = lambda: h
    pc._receipt_cargar = lambda tid, fp: (MEM.load('rc', tid + fp) or [{}])[0].get('data')
    pc._receipt_guardar = lambda tid, fp, d: (MEM.save('rc', tid + fp, d), True)[1]
    pc._tool_verificar = lambda nom, args: None

    def corre(resps):
        it = iter(resps)
        pc._DEADLINE.set(time.monotonic() + 60)
        pc._REQ_TOOLS.set(False)
        pc._SOLO_LECTURA.set(False)
        pc._VISTOS.set({})
        pc._IDS_CTX.set({'task_id': 'T-g07', 'nodo': 'N4', 'sesion': 's'})
        pc._POL.set({})
        return pc._bucle(lambda ms, tl: next(it), [{'role': 'user', 'content': 'hola'}])
    call = {'role': 'assistant', 'content': '', 'tool_calls': [{'id': 'c0', 'type': 'function', 'function': {'name': 'github_escribir', 'arguments': json.dumps({'repo': 'r', 'ruta': 'x', 'contenido': 'c'})}}]}
    L = lambda t: (200, {'choices': [{'message': {'role': 'assistant', 'content': t}, 'finish_reason': 'length'}]})  # noqa: E731
    fin = (200, {'choices': [{'message': {'role': 'assistant', 'content': 'cola final'}, 'finish_reason': 'stop'}]})
    d, u = corre([(200, {'choices': [{'message': call, 'finish_reason': 'tool_calls'}]}), L('parte uno de la respuesta '), L('parte dos de la respuesta '), fin])
    assert 'error' not in d and len(h.llamadas) == 1, (d, h.llamadas)
    txt = d['choices'][0]['message']['content']
    assert 'parte uno' in txt and 'cola final' in txt
    # reanudacion tras corte: la misma mutacion ya esta DONE, no se ejecuta otra vez
    d2, _ = corre([(200, {'choices': [{'message': call, 'finish_reason': 'tool_calls'}]}), fin])
    assert 'error' not in d2 and len(h.llamadas) == 1, h.llamadas


def test_g07_sse_cortado_devuelve_gap_con_parcial():
    class R:
        status = 200
        def __enter__(self): return self
        def __exit__(self, *a): return False
        def __iter__(self):
            yield b'data: {"choices":[{"delta":{"content":"hola "}}]}\n'
    orig = pc._abrir
    pc._abrir = lambda req, espera: R()
    pc._DEADLINE.set(time.monotonic() + 30)
    try:
        s, d = pc._http_stream('http://x', 'tok', {'model': 'm'}, 5, lambda c: None)
    finally:
        pc._abrir = orig
    assert s == 502
    assert d.get('error') == 'GAP_STREAM_INTERRUPTED' and d.get('parcial') == 'hola '


# ---------------- G10 ----------------
def _ficha_loop(**lp):
    return {'loop': {'max_partes_codigo': 2, **lp}}


def _opts():
    return {'herr': {'N4': []}, 'out': {}, 'pid': 'pG10', 'fid': 'f', 'aprobado': True, 'muta': True, 'cap_in': 'write'}


def test_g10_limite_de_request_se_reanuda_hasta_done():
    fq._ck_guardar = lambda *a, **k: None
    k = []

    def fake(m, p, f, n, o):
        k.append(1)
        o['herr'].setdefault('N4', []).append({'herramienta': 'w%d' % len(k), 'ok': True, 'mutacion_real': True})
        return 'parte%d\n%s' % (len(k), 'TAREA_COMPLETA' if len(k) == 5 else 'CONTINUAR_PARTE')
    fq._llamar_harness_3 = fake
    r = fq._llamar_con_partes_reanudable('m', 'haz X', _ficha_loop(), {'id': 'N4'}, _opts())
    assert len(k) == 5 and 'parte5' in r and 'parte1' in r  # 2 partes por request -> 3 ventanas, DONE solo al final


def test_g10_watchdog_sin_avance_y_stop():
    fq._ck_guardar = lambda *a, **k: None
    orig = fq._llamar_con_partes
    def sin_avance(*a):
        raise RuntimeError('GAP_LOOP_LIMITE_TIEMPO')  # cada ventana agota el tiempo sin dejar cursor nuevo
    fq._llamar_con_partes = sin_avance
    try:
        fq._llamar_con_partes_reanudable('m', 'haz X', _ficha_loop(), {'id': 'N4'}, _opts())
        raise AssertionError('debia cortar')
    except RuntimeError as x:
        assert str(x).startswith('GAP_LOOP_SIN_AVANCE_ENTRE_VENTANAS'), x
    finally:
        fq._llamar_con_partes = orig
    o = _opts()
    fq._CANCEL.add('pG10')
    try:
        fq._llamar_con_partes_reanudable('m', 'haz X', _ficha_loop(), {'id': 'N4'}, o)
        raise AssertionError('Stop ignorado')
    except RuntimeError as x:
        assert str(x) == 'GAP_LOOP_CANCELADO'
    finally:
        fq._CANCEL.discard('pG10')
    # GAP bloqueante no se reanuda
    fq._llamar_harness_3 = lambda *a: 'CONTINUAR_PARTE'
    try:
        fq._llamar_con_partes_reanudable('m', 'haz X', _ficha_loop(max_partes_codigo=12), {'id': 'N4'}, _opts())
        raise AssertionError('debia bloquear')
    except RuntimeError as x:
        assert str(x).startswith('GAP_LOOP_SIN_PROGRESO'), x  # sin tool OK es bloqueo real, no se reanuda


# ---------------- G11 ----------------
def test_g11_receipt_real_status_y_payload_sanitizado():
    e = pc._evi('github_escribir', {'repo': 'r', 'ruta': 'a', 'token': 'ghp_SECRETO', 'contenido': 'c'}, True, True, 'OK')
    assert e['status'] == 'OK' and e['receipt_id'].startswith('tr-') and e['payload_sanitizado']['token'] == '[REDACTADO]'
    assert 'ghp_SECRETO' not in json.dumps(e)
    assert e['receipt_id'] == pc._evi('github_escribir', {'repo': 'r', 'ruta': 'a', 'token': 'otro', 'contenido': 'c'}, True, True)['receipt_id']
    f = pc._evi('github_leer', {'repo': 'r'}, False, False, 'ERROR 404')
    assert f['status'] == 'FALLO' and f['ok'] is False  # fallo real jamas PASS


def test_g11_el_llm_no_acredita_tools_con_texto():
    class H:
        SISTEMA = 'x'
        TOOLS = []
        def ejecutar(self, n, a): raise AssertionError('no debe ejecutarse')
    pc._herr = lambda: H()
    pc._DEADLINE.set(time.monotonic() + 30)
    pc._REQ_TOOLS.set(True)
    pc._SOLO_LECTURA.set(True)
    pc._VISTOS.set({})
    pc._POL.set({})
    d, usadas = pc._bucle(lambda ms, tl: (200, {'choices': [{'message': {'role': 'assistant', 'content': 'Ya ejecute github_leer y lei el repo.'}}]}), [{'role': 'user', 'content': 'lee'}])
    assert not [u for u in usadas if isinstance(u, dict) and u.get('ok') and u.get('tool')]  # sin receipt real no hay evidencia (el chat devuelve GAP HERRAMIENTA_NO_EJECUTADA)


# ---------------- G12 ----------------
def test_g12_proyecto_resuelve_local_antes_de_github():
    MEM.save('chat-ui|project:pSin', 'meta', {'nombre': 'Sin repo', 'notas': 'n'})
    MEM.save('chat-ui|project:pCon', 'meta', {'nombre': 'Con repo', 'notas': 'n', 'repo': 'org/r'})
    pc.DUENO = 'chat-ui'
    a, b, c = pc.proyecto_resolver('pSin'), pc.proyecto_resolver('pCon'), pc.proyecto_resolver('pNo')
    assert (a['estado'], b['estado'], c['estado']) == ('LOCAL_SIN_REPO', 'LOCAL_CON_REPO', 'DESCONOCIDO')
    assert b['repo'] == 'org/r' and a['repo'] == ''
    assert 'proyecto no implica repo' in a['regla'] and 'inventes' in a['regla']
    assert 'GAP_PROJECT_NO_RESUELTO' in c['regla']


# ---------------- G15 ----------------
def test_g15_pregunta_respuesta_extensas_byte_a_byte_por_sha_y_cursor():
    q, a = 'Ñ¿?' * 3000, 'ré😀\n' * 6000
    assert pc._guardar('sG15', 'm', q, a) is True
    h = sha(q + '\0' + a)
    corto = [r['data'] for (s, _), rows in MEM.d.items() if s.endswith('chat:sG15') for r in rows][0]
    assert corto['full_sha'] == h and len(corto['respuesta']) == 8000
    partes, cur = [], 0
    while cur is not None:
        r = pc._turno_full_leer('sG15', h, 'respuesta', cur, 7000)
        assert r['ok']
        partes.append(r['texto'])
        cur = r['siguiente']
    assert ''.join(partes) == a and len(partes) > 1
    assert pc._turno_full_leer('sG15', h, 'pregunta', 0, 200000)['texto'] == q
    assert pc._turno_full_leer('otraSesion', h)['error'] == 'GAP_TURNO_FULL_NO_EXISTE'  # sesion correcta
    assert pc._turno_full_leer('sG15', 'f' * 64)['error'] == 'GAP_TURNO_FULL_NO_EXISTE'
    assert pc._guardar('sG15b', 'm', 'corta', 'corta') is True and pc._turno_full_leer('sG15b', sha('corta\0corta'))['error'] == 'GAP_TURNO_FULL_NO_EXISTE'


# ---------------- G16 ----------------
def test_g16_lock_solo_delegaciones_y_tools_chat_directo_sigue():
    pc.DUENO = 'chat-ui'
    assert pc._agent_lock_set('sL', True) == {'ok': True, 'locked': True}
    pc._IDS_CTX.set({})            # camino que no propago la sesion
    pc._MOTOR_SES.set('sL')
    assert pc._deleg_lock() is True  # cae a la sesion segura del backend
    pc._IDS_CTX.set({'sesion': 'sL'})
    assert pc._deleg_lock() is True
    pc._MOTOR_SES.set('sOtra')
    pc._IDS_CTX.set({})
    assert pc._deleg_lock() is False  # cambio de sesion respeta el estado
    r = pc.handle('recurso_probar', {'sesion': 'sL', 'agente': 'a'}) if hasattr(pc, 'handle') else None
    if r is not None:
        assert r.get('error') == 'GAP_AGENT_ACCESS_LOCKED'
    assert pc._agent_lock_set('sL', False) == {'ok': True, 'locked': False}  # OFF restablece
    pc._IDS_CTX.set({'sesion': 'sL'})
    assert pc._deleg_lock() is False
    # chat directo sin tools: el lock no toca la llamada (solo _TOOLS_DELEGAN)
    assert 'groq_agente' in pc._TOOLS_DELEGAN and 'github_leer' not in pc._TOOLS_DELEGAN


if __name__ == '__main__':
    fallos = 0
    for nombre, fn in sorted(globals().items()):
        if nombre.startswith('test_') and callable(fn):
            try:
                fn()
            except Exception as x:  # noqa: BLE001
                fallos += 1
                import traceback
                traceback.print_exc()
                print('FAIL', nombre, repr(x)[:300])
    print('PARCHE_BACK FAIL' if fallos else 'PARCHE_BACK PASS')
    sys.exit(1 if fallos else 0)
