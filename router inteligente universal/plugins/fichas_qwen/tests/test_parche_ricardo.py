"""PARCHE_RICARDO offline: A nota de reanudacion, B verificar_recibos, C done_when, E estado invalido, G objetivo corto con sha.
Desde 'router inteligente universal/':  PYTHONPATH=. python3 -I plugins/fichas_qwen/tests/test_parche_ricardo.py"""
import json
import os
import sys
import tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from plugins.fichas_qwen.modos import motor_objetivo as mo  # noqa: E402
import plugins.puente_chat.plugin as pcm  # noqa: E402

mo._recibos_falsos = lambda ids: []
OBJ = {'objetivo': 'x', 'tareas': ['hacer algo'], 'modo_por_defecto': 'code',
       'limites': {'pausa_entre_vueltas_s': 0, 'max_vueltas': 6, 'max_continuaciones_por_tarea': 8}}


def _j(estado, nota='n', res='r'):
    return json.dumps({'tarea': 'T1', 'estado': estado, 'resultado': res, 'evidencia': 'e', 'nuevas_tareas': [],
                       'nota_siguiente': nota, 'receipt_ids': []})


def _corre(guion, obj=None):
    pasos = list(guion); prompts = []
    def llamar(modo, prompt):
        prompts.append(prompt)
        return dict(pasos[min(len(prompts) - 1, len(pasos) - 1)])
    res = mo.correr_objetivo(dict(obj or OBJ), llamar, lambda st: None, lambda t: None)
    return res, prompts


def test_a_nota_llega_a_la_vuelta_siguiente():
    res, pr = _corre([{'texto': _j('sigue', nota='seguir en linea 42 de a.py'), 'mutaciones_ok': 1, 'herramientas_ok': 1},
                      {'texto': _j('hecho'), 'mutaciones_ok': 1, 'herramientas_ok': 1}])
    assert 'PUNTO DE REANUDACIÓN: seguir en linea 42 de a.py' in pr[1], pr[1]
    assert 'PUNTO DE REANUDACIÓN' not in pr[0]


def test_a_resumen_lleva_nota_y_recibos():
    res, pr = _corre([{'texto': _j('sigue', nota='NOTA_X'), 'mutaciones_ok': 1, 'herramientas_ok': 1, 'receipt_ids': ['receipt-a-T1-11111111']},
                      {'texto': _j('hecho'), 'mutaciones_ok': 1, 'herramientas_ok': 1}])
    assert 'nota: NOTA_X' in pr[1] and 'receipt-a-T1-11111111' in pr[1], pr[1]


def test_c_criterio_false_no_cierra_y_reencola():
    obj = dict(OBJ, done_when=['existe a.txt', 'tests pasan'])
    v = {'texto': json.dumps({'cumplido': True, 'criterios': [{'c': 'existe a.txt', 'ok': True, 'evidencia': 'x'},
                                                            {'c': 'tests pasan', 'ok': False, 'evidencia': 'fallan'}]}), 'herramientas_ok': 1}
    n = {'i': 0}; prompts = []
    def llamar(modo, prompt):
        prompts.append((modo, prompt))
        if modo == 'auditor':
            return v
        return {'texto': _j('hecho'), 'mutaciones_ok': 1, 'herramientas_ok': 1}
    res = mo.correr_objetivo(obj, llamar, lambda st: None, lambda t: None)
    assert res['estado'] != 'CUMPLIDO', res
    assert any('tests pasan' in t['texto'] for t in res['tareas'][1:]), res['tareas']
    assert 'done_when' in [p for m, p in prompts if m == 'auditor'][0]


def test_c_todos_ok_cierra_y_sin_done_when_compatible():
    obj = dict(OBJ, done_when=['a'])
    ok = {'texto': json.dumps({'cumplido': True, 'criterios': [{'c': 'a', 'ok': True, 'evidencia': 'x'}]}), 'herramientas_ok': 1}
    pasos = {'code': {'texto': _j('hecho'), 'mutaciones_ok': 1, 'herramientas_ok': 1}, 'auditor': ok}
    assert mo.correr_objetivo(obj, lambda m, p: dict(pasos[m]), lambda s: None, lambda t: None)['estado'] == 'CUMPLIDO'
    ok2 = {'texto': json.dumps({'cumplido': True, 'evidencia': 'e'}), 'herramientas_ok': 1}
    pasos['auditor'] = ok2
    assert mo.correr_objetivo(dict(OBJ), lambda m, p: dict(pasos[m]), lambda s: None, lambda t: None)['estado'] == 'CUMPLIDO'
    assert 'done_when' not in mo._prompt_verif(OBJ, [])


def test_e_estado_invalido_es_fallo():
    res, _ = _corre([{'texto': _j('terminado'), 'mutaciones_ok': 1, 'herramientas_ok': 1}])
    t = res['tareas'][0]
    assert t['estado'] != 'hecho' and t['intentos'] >= 1, t


def test_g_objetivo_grande_prompt_corto_con_sha():
    obj = dict(OBJ, objetivo=('linea de objetivo largo\n' * 700))
    obj.pop('tareas')
    assert len(obj['objetivo']) > 8500
    res, pr = _corre([{'texto': _j('hecho'), 'mutaciones_ok': 1, 'herramientas_ok': 1}], obj)
    import hashlib
    sha = hashlib.sha256(obj['objetivo'].encode('utf-8')).hexdigest()[:12]
    assert sha in pr[0] and 'objetivo_sha256="%s"' % sha in pr[0]
    assert pr[0].count('linea de objetivo largo') < 700 and len(pr[0]) < len(obj['objetivo']) + 3000
    t = {'id': 'T1', 'texto': 'x', 'input_bloque': 'bloque', 'sha_input': 'a' * 64, 'sha_objetivo': 'b' * 64}
    assert len(mo._prompt_vuelta(obj, t, '')) < 2500


def test_b_verificar_recibos_lectura_real_e_inventado():
    os.environ['RIU_MOTOR_WS'] = tempfile.mkdtemp()
    plan = json.dumps({"meta": {"name": "ric-t"}, "ops": [
        {"id": "T1", "op": "create_directory", "path": "d"},
        {"id": "T2", "op": "write_text", "path": "d/p.txt", "text": "hola\n", "depends_on": ["T1"]},
        {"id": "T3", "op": "finish", "depends_on": ["T2"]}]})
    pcm._MOTOR_HAB.set(True); pcm._MOTOR_SES.set('ses-ric')
    try:
        assert 'verificar_recibos' in {t['function']['name'] for t in pcm._MOTOR_TOOLS}
        assert not pcm._es_mutacion('verificar_recibos', {'receipt_id': 'x'})
        rep = json.loads(pcm._motor_ejecutar('ejecutar_plan_json', {'plan': plan}).split(' ', 1)[1])
        rid = next(r['receipt_id'] for r in rep['receipts'] if r.get('receipt_id'))
        assert json.loads(pcm._motor_ejecutar('verificar_recibos', {'receipt_id': rid}))['existe'] is True
        assert json.loads(pcm._motor_ejecutar('verificar_recibos', {'receipt_id': 'receipt-inventado-T9-deadbeef'}))['existe'] is False
    finally:
        pcm._MOTOR_HAB.set(False)


if __name__ == '__main__':
    n = 0
    for k, f in list(globals().items()):
        if k.startswith('test_'):
            f(); n += 1; print('PASS', k)
    print('RICARDO: %d/%d PASS' % (n, n))
