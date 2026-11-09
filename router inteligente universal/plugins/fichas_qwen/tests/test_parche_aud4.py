"""PARCHE_AUD4 offline: G1 recibos de la tarea, G2 huella con recibos nuevos, G3 temperatura por modo, G4 espejo completo, G5 truncado = continuar.
Desde 'router inteligente universal/':  PYTHONPATH=. python3 plugins/fichas_qwen/tests/test_parche_aud4.py"""
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import plugins.fichas_qwen.plugin as fq  # noqa: E402
from plugins.fichas_qwen.modos import motor_objetivo as mo  # noqa: E402

mo._recibos_falsos = lambda ids: []  # la existencia real la prueba test_parche_t1; aqui se prueba la pertenencia a la tarea
OBJ = {'objetivo': 'x', 'tareas': ['hacer algo'], 'modo_por_defecto': 'code',
       'limites': {'pausa_entre_vueltas_s': 0, 'max_vueltas': 6, 'max_continuaciones_por_tarea': 8}}


def _j(estado, ids=None, nota='n', res='r'):
    return json.dumps({'tarea': 'T1', 'estado': estado, 'resultado': res, 'evidencia': 'e', 'nuevas_tareas': [],
                       'nota_siguiente': nota, 'receipt_ids': ids or []})


def _corre(guion, obj=None):
    pasos = list(guion); prompts = []
    def llamar(modo, prompt):
        prompts.append(prompt)
        return dict(pasos[min(len(prompts) - 1, len(pasos) - 1)])
    res = mo.correr_objetivo(dict(obj or OBJ), llamar, lambda st: None, lambda t: None)
    return res, prompts


def test_g1_recibo_ajeno_no_cierra():
    res, _ = _corre([{'texto': _j('hecho', ['receipt-otra-T9-deadbeef']), 'mutaciones_ok': 1, 'herramientas_ok': 1,
                      'receipt_ids': ['receipt-esta-T1-aaaaaaaa']}])
    assert all(t['estado'] != 'hecho' for t in res['tareas']), res['tareas']


def test_g1_recibo_propio_cierra():
    res, _ = _corre([{'texto': _j('hecho', ['receipt-esta-T1-aaaaaaaa']), 'mutaciones_ok': 1, 'herramientas_ok': 1,
                      'receipt_ids': ['receipt-esta-T1-aaaaaaaa']}])
    assert res['tareas'][0]['estado'] == 'hecho', res['tareas']


def test_g1_code_hecho_con_mutacion_sin_recibo_cierra():  # github_escribir ('OK commit <sha>') no emite 'receipt-': no se exige recibo
    res, _ = _corre([{'texto': _j('hecho', []), 'mutaciones_ok': 1, 'herramientas_ok': 1, 'receipt_ids': []}])
    assert res['tareas'][0]['estado'] == 'hecho', res['tareas']


def test_g1_code_hecho_sin_mutacion_no_cierra():
    res, _ = _corre([{'texto': _j('hecho', []), 'mutaciones_ok': 0, 'herramientas_ok': 0, 'receipt_ids': []}])
    assert all(t['estado'] != 'hecho' for t in res['tareas']), res['tareas']


def test_g2_reformular_sin_recibo_no_es_avance():
    pasos = [{'texto': _j('sigue', [], nota='nota %d' % k), 'mutaciones_ok': 0, 'herramientas_ok': 0, 'receipt_ids': []} for k in range(6)]
    res, _ = _corre(pasos)
    assert int(res['tareas'][0].get('continuaciones') or 0) == 0, res['tareas']


def test_g2_recibo_nuevo_si_es_avance():
    pasos = [{'texto': _j('sigue', [], nota='nota %d' % k), 'mutaciones_ok': 0, 'herramientas_ok': 1,
              'receipt_ids': ['receipt-esta-T1-%08d' % k]} for k in range(6)]
    res, _ = _corre(pasos)
    assert int(res['tareas'][0].get('continuaciones') or 0) >= 1, res['tareas']


def test_g3_temperatura_por_modo():
    assert mo._temp_modo('planificador') == 0.2 and mo._temp_modo('auditor') == 0.0 and mo._temp_modo('code') == 0.2
    assert mo._temp_modo('rapido') is None
    pol = mo._politica_temp_txt()
    assert 'no forzar' in pol.lower(), pol
    assert mo._temp_modo('code', pol, pensando=True) is None  # la politica manda: no forzar en thinking
    assert mo._temp_modo('code', pol, pensando=False) == 0.2


def test_g4_espejo_completo_y_respaldo():
    st = {'tareas': [{'id': 'T1', 'texto': 'x' * 5000}], 'vuelta': 3, 'resumen': ['r']}
    s = fq._motor_espejo(st)
    assert len(s) > 2000 and json.loads(s)['vuelta'] == 3
    orig = fq._ck_cargar
    try:
        fq._ck_cargar = lambda pid: {'out': {'__motor__': s}}
        assert fq._motor_estado_respaldo('p1')['vuelta'] == 3
        fq._ck_cargar = lambda pid: {'out': {}}
        assert fq._motor_estado_respaldo('p1') is None
    finally:
        fq._ck_cargar = orig


def test_g5_truncado_no_cuenta_intento_y_avisa():
    ok = {'texto': _j('hecho', ['receipt-esta-T1-aaaaaaaa']), 'mutaciones_ok': 1, 'herramientas_ok': 1, 'receipt_ids': ['receipt-esta-T1-aaaaaaaa']}
    res, prompts = _corre([{'texto': 'GAP_OUTPUT_TRUNCATED (continuar)', 'truncado': True}, {'texto': 'xx', 'truncado': True}, ok])
    t = res['tareas'][0]
    assert t['estado'] == 'hecho' and int(t.get('intentos') or 0) == 0, t
    assert 'AVISO' in prompts[1] and 'AVISO' in prompts[2] and 'AVISO' not in prompts[0]


def test_g5_tres_truncados_bloquean_con_motivo():
    res, _ = _corre([{'texto': 'GAP_OUTPUT_TRUNCATED (continuar)', 'truncado': True}])
    t = res['tareas'][0]
    assert t['estado'] == 'bloqueada' and 'TRUNCATED' in str(t.get('falta')), t


if __name__ == '__main__':
    n = 0
    for k, f in list(globals().items()):
        if k.startswith('test_'):
            f(); n += 1; print('PASS', k)
    print('AUD4: %d/%d PASS' % (n, n))
