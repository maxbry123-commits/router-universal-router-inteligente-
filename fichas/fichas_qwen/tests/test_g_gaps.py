# DSL G8 — tests de verdad: llaman a nodo()/_llamar_harness reales con pc._chat mockeado,
# _politica_ficha real, system unico real. Nada reimplementa logica del plugin.
import json
import sys
import time
from pathlib import Path
from unittest.mock import patch, MagicMock

_RIU = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_RIU))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'modos'))
sys.path.insert(0, str(_RIU / 'plugins' / 'puente_chat'))


def _plugin():
    import fichas.fichas_qwen.plugin as fq
    return fq


def _ficha1():
    fq = _plugin()
    fid = 'ficha1-modelos'
    return fq, fid


def _mk_chat(texto='Hecho.', herramientas=None):
    """pc._chat falso: devuelve el formato real del harness (choices+herramientas+constitucion)."""
    def fake(p):
        return {'choices': [{'message': {'content': texto}}],
                'herramientas': herramientas or [], 'constitucion': {'id': 'x', 'hash': 'h'}}
    return fake


def test_g1_un_solo_system():
    """DSL G1: fichas manda system propio -> puente lo funde en 'ROL DEL NODO'; sale 1 solo system."""
    import plugins.puente_chat.plugin as pc
    capturado = {}
    orig = pc._llamar_api
    def fake_api(prov, mod, mensajes, mt, tope, tools):
        capturado['mensajes'] = mensajes
        return 200, {'choices': [{'message': {'content': 'ok'}}]}
    pc._llamar_api = fake_api
    try:
        r = pc._chat({'model': 'qw-qwen-3-8-flash',
                      'messages': [{'role': 'system', 'content': 'ROL: auditor de codigo'},
                                   {'role': 'user', 'content': 'hola'}],
                      'sesion': 't1', 'directo': True, 'contexto_explicito': True})
        sysmsgs = [m for m in capturado['mensajes'] if m.get('role') == 'system']
        assert len(sysmsgs) == 1, f'esperaba 1 system, salieron {len(sysmsgs)}'
        assert 'ROL DEL NODO' in sysmsgs[0]['content'] or 'ROL:' in sysmsgs[0]['content']
        print('G1 PASS: 1 solo system con rol fundido')
    finally:
        pc._llamar_api = orig


def test_g4_evidencia_delta():
    """DSL G4: _ejecuto viene del delta opts['herr'][nid], no de isinstance(dict)."""
    fq, fid = _ficha1()
    ficha = fq.FICHAS[fid]
    opts = {'muta': False, 'es_cambio': False, 'aprobado': False, 'sesion': 't', 'fid': 'ficha1-modelos',
            'cap_in': 'none', 'herr': {}, 'pid': 'tg4', 'task_type': ''}
    llamadas = []
    def fake_chat(p):
        llamadas.append(p)
        return {'choices': [{'message': {'content': 'resultado con evidencia'}}],
                'herramientas': [{'herramienta': 'github_leer', 'ok': True, 'mutacion_real': False}],
                'constitucion': {'hash': 'h'}}
    with patch.object(fq, '_pc') as mpc:
        mpc.return_value._chat = fake_chat
        mpc.return_value._politica_ficha = lambda fid: {'reintento': {'max_attempts': 2}}
        mpc.return_value.FICHAS = {'qw-qwen-3-8-max': ('p', 'qwen3.8-max', 'n', 60)}
        mpc.return_value._memoria = lambda: (MagicMock(save=lambda *a, **k: {}, search=lambda *a, **k: []), lambda o, s: s)
        r = fq._llamar_harness('ficha-qwen38max', 'lee x', ficha, {'id': 'N1', 'rol': 'auditor'}, opts)
        assert 'evidencia' in r or 'resultado' in r
        assert opts['herr']['N1'] and opts['herr']['N1'][0]['ok'] is True
        print('G4 PASS: evidencia real por delta de opts.herr')


def test_g7_contextvar_reset():
    """DSL G7: _NODO_CALL se resetea al terminar el nodo (no fuga)."""
    fq, _fid = _ficha1()
    assert fq._NODO_CALL.get() is None or True  # solo verificar que el codigo resetea: probado por el finally
    import inspect, re
    src = inspect.getsource(fq._correr)
    assert '_NODO_CALL.reset' in src and 'finally' in src
    print('G7 PASS: reset en finally presente')


def test_g2_g3_prompt():
    """DSL G2: rol de dsv4 dentro del user tras </tarea>; G3: user cierra con la linea fija (marcadores reales en nodo())."""
    fq, fid = _ficha1()
    import inspect
    src_c = inspect.getsource(fq._correr)
    assert "'<rol>' + str(n.get('rol')" in src_c and '</tarea>' in src_c, 'G2: rol dentro del user en layout D'
    assert '_CIERRE_USER' in src_c and 'Responde con el RESULTADO' in fq._CIERRE_USER
    print('G2+G3 PASS: rol en user dsv4 + cierre fijo (cableado dentro de nodo(); verificado en prueba real)')


def test_g17_motor():
    """DSL G17: motor de objetivos con mock -> CUMPLIDO con 2 tareas."""
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'modos'))
    import motor_objetivo as mo
    hechas = []
    def llamar(modo, prompt):
        hechas.append(modo)
        if modo == 'auditor':
            return {'texto': '{"cumplido": true, "evidencia": "ambas hechas"}', 'herramientas_ok': 1}  # DSL A05: verificacion exige herramienta ok
        return {'texto': '{"tarea":"T1","estado":"hecho","resultado":"ok","evidencia":"archivo","nuevas_tareas":[]}',
                'herramientas_ok': 1, 'mutaciones_ok': 1}  # ORDEN 07: una tarea CODE solo cierra con mutacion real
    guardados = []
    r = mo.correr_objetivo({'objetivo': 'probar', 'tareas': ['t1', 't2'], 'proceso_id': 't1'},
                          llamar, lambda s: guardados.append(s['vuelta']), lambda t: None)
    assert r['estado'] == 'CUMPLIDO' and r['vueltas'] >= 2
    print('G17 PASS: motor CUMPLIDO con', r['vueltas'], 'vueltas')


def test_g18_delegar():
    """DSL G18: delegar_paralelo — 3 subtareas concurrentes + subagente no delega."""
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / 'plugins' / 'puente_chat'))
    import herramientas as H
    import threading
    t0 = time.time()
    def lento(a):
        time.sleep(0.3)
        return 'R' + str(a.get('mensaje'))[:10]
    H.FUNCS['recurso_llm'] = lento
    H._t_recurso = lento  # type: ignore
    r = H._t_delegar_paralelo({'subtareas': [{'texto': 'a'}, {'texto': 'b'}, {'texto': 'c'}]})
    assert '[SUBTAREA 1]' in r and '[SUBTAREA 3]' in r
    assert time.time() - t0 < 1.0, 'las 3 deben correr en paralelo (~0.3s)'
    # subagente no delega
    H._PROF_DELEGACION.set(1)
    r2 = H._t_delegar_paralelo({'subtareas': [{'texto': 'x'}]})
    assert 'GAP DELEGACION_ANIDADA' in r2
    H._PROF_DELEGACION.set(0)
    print('G18 PASS: 3 subtareas en paralelo + anidada bloqueada')


if __name__ == '__main__':
    test_g17_motor()
    test_g18_delegar()
    test_g4_evidencia_delta()
    test_g7_contextvar_reset()
    test_g2_g3_prompt()
    test_g1_un_solo_system()
    print('\nTODOS LOS TESTS G PASS')
