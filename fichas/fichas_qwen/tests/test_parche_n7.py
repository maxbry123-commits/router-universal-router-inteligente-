"""PARCHE_N7 offline: verificadores/analistas con tools opcionales; el escritor aprobado las exige; el motor devuelve su error real.
Desde la raiz del repo:  PYTHONPATH=. python3 fichas/fichas_qwen/tests/test_parche_n7.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import fichas.fichas_qwen.plugin as fq  # noqa: E402
import plugins.puente_chat.plugin as pcm  # noqa: E402

CAPT = []


class _FakePC:
    FICHAS = {'qw-qwen-3-8-max': ('x', 'x', 'Qwen 3.8 Max', 60)}

    @staticmethod
    def _chat(p):
        CAPT.append(p)
        return {'choices': [{'message': {'content': 'VEREDICTO: PASS'}}], 'constitucion': None}


fq._pc = lambda: _FakePC
FICHA = dict(fq.FICHAS['ficha2-dag-codigo'])


def _llamar(nodo, **o):
    CAPT.clear()
    opts = {'fid': 'ficha2-dag-codigo', 'cap_in': 'write', 'sesion': 't', 'tarea_id': 'T7', 'aprobado': True, 'muta': True}
    opts.update(o)
    try:
        fq._llamar_harness_1('ficha-qwen38max', 'hola', FICHA, nodo, opts)
    except RuntimeError as e:  # el fake no ejecuta tools
        assert 'SIN_EVIDENCIA' in str(e), e
    return CAPT[-1]


def test_verificadores_y_analistas_no_exigen_tools():
    for nid in ('N1', 'N2', 'N3', 'N3B', 'N5', 'N6', 'N7', 'N8', 'V1'):
        p = _llamar({'id': nid, 'timeout_s': 30, 'escribe': False})
        assert p['requiere_tools'] is False, nid
        assert p['cap_tools'] == 'read' and p['solo_lectura'] is True and p['motor'] is False, nid


def test_escritor_aprobado_si_exige_tools_y_escribe():
    p = _llamar({'id': 'N4', 'timeout_s': 30})
    assert p['requiere_tools'] is True and p['cap_tools'] == 'write' and p['motor'] is True


def test_nodo_que_declara_requiere_tools_se_respeta():
    p = _llamar({'id': 'N7', 'timeout_s': 30, 'escribe': False, 'requiere_tools': True})
    assert p['requiere_tools'] is True and p['cap_tools'] == 'read'


def test_motor_error_llega_al_modelo():
    pcm._MOTOR_HAB.set(True)
    orig = pcm._motor_descarga
    pcm._motor_descarga = lambda q: ('MOTOR_ERROR: motor_1_extract_only.py codigo=2\nTraceback: zip corrupto', ['motor:x'])
    try:
        out = pcm._motor_ejecutar('motor_descargar', {'origen': 'a', 'destino': 'b'})
    finally:
        pcm._motor_descarga = orig
        pcm._MOTOR_HAB.set(False)
    assert out.startswith('MOTOR_ERROR') and 'zip corrupto' in out and out.startswith(pcm._FALLO)


if __name__ == '__main__':
    n = 0
    for k, f in list(globals().items()):
        if k.startswith('test_'):
            f()
            n += 1
            print('PASS', k)
    print('PARCHE_N7: %d/%d PASS' % (n, n))
