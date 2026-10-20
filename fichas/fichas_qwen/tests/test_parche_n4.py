"""PARCHE_N4 (offline, sin red): el escritor aprobado recibe CAP_WRITE + motor; nadie mas.
Ejecutar desde la raiz del repo:  PYTHONPATH=. python3 fichas/fichas_qwen/tests/test_parche_n4.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import fichas.fichas_qwen.plugin as fq  # noqa: E402
from plugins.puente_chat import capacidad as cap  # noqa: E402
import plugins.puente_chat.plugin as pcm  # noqa: E402

CAPT = []


class _FakePC:
    FICHAS = {'qw-qwen-3-8-max': ('x', 'x', 'Qwen 3.8 Max', 60)}

    @staticmethod
    def _chat(p):
        CAPT.append(p)
        return {'choices': [{'message': {'content': 'ok'}}], 'constitucion': None}


fq._pc = lambda: _FakePC
FICHA = dict(fq.FICHAS['ficha2-dag-codigo'])


def _llamar(nodo, **o):
    CAPT.clear()
    opts = {'fid': 'ficha2-dag-codigo', 'cap_in': 'none', 'sesion': 't', 'tarea_id': 'T1'}
    opts.update(o)
    try:
        fq._llamar_harness_1('ficha-qwen38max', 'hola', FICHA, nodo, opts)
    except RuntimeError as e:  # el fake no ejecuta tools: EJECUCION_SIN_EVIDENCIA es lo correcto para el escritor
        assert 'SIN_EVIDENCIA' in str(e), e
    return CAPT[-1]


def test_n4_aprobado_escribe_con_motor():
    p = _llamar({'id': 'N4', 'timeout_s': 30}, aprobado=True, muta=True, cap_in='write')
    assert p['cap_tools'] == 'write' and p['solo_lectura'] is False
    assert p['motor'] is True and p['requiere_tools'] is True and p['tools_habilitadas'] is True


def test_n4_sin_aprobacion_no_escribe():
    p = _llamar({'id': 'N4', 'timeout_s': 30}, aprobado=False, muta=True, cap_in='write')
    assert p['cap_tools'] == 'read' and p['solo_lectura'] is True and p['motor'] is False


def test_revisor_nunca_escribe_aunque_este_aprobado():
    for nid in ('N1', 'N6', 'N7', 'N8', 'V1'):
        p = _llamar({'id': nid, 'timeout_s': 30, 'escribe': False}, aprobado=True, muta=True, cap_in='write')
        assert p['cap_tools'] != 'write' and p['solo_lectura'] is True and p['motor'] is False, nid


def test_p3_cadena_escritor_aprobado():
    p = _llamar({'id': 'P3', 'timeout_s': 30, 'escribe': True, 'requiere_tools': True}, aprobado=True, muta=True, cap_in='write')
    assert p['cap_tools'] == 'write' and p['motor'] is True


def test_fast_lane_nunca_escribe():
    p = _llamar({'id': 'N4', 'timeout_s': 30}, aprobado=True, muta=True, cap_in='write', fast_lane=True)
    assert p['cap_tools'] != 'write' and p['motor'] is False


def test_catalogo_write_trae_github_escribir_y_read_no():
    from plugins.puente_chat.herramientas import TOOLS
    nw = {t['function']['name'] for t in cap.catalogo_para('write', TOOLS)}
    nr = {t['function']['name'] for t in cap.catalogo_para('read', TOOLS)}
    assert 'github_escribir' in nw and 'github_escribir' not in nr


def test_motor_mutante_y_fallo():
    assert pcm._es_mutacion('motor_copiar', {}) and pcm._es_mutacion('motor_mover', {}) and pcm._es_mutacion('motor_descargar', {})
    assert not pcm._es_mutacion('motor_verificar', {}) and not pcm._es_mutacion('motor_extraer', {})
    assert 'MOTOR_ERROR: x'.startswith(pcm._FALLO)


def test_motor_bloqueado_en_solo_lectura():
    tok = pcm._SOLO_LECTURA.set(True)
    try:
        assert pcm._bloqueo('motor_copiar', {'origen': 'a', 'destino': 'b'}).startswith('ERROR: GAP_MUTACION_NO_AUTORIZADA')
    finally:
        pcm._SOLO_LECTURA.reset(tok)


def test_capacidad_verbos_de_copia_y_extraccion():
    w = ['Busca el zip en GitHub, extráelo y copia los archivos al repo',
         'Copia la carpeta X del repo a la rama main', 'Descarga el zip de GitHub y descomprímelo en la rama',
         'Integra estos archivos en el repositorio', 'Añade el archivo al repo', 'Edita el archivo del repo']
    for t in w:
        assert cap.capacidad_de(t) == 'write', t
    assert cap.capacidad_de('Extrae información del repo') == 'read'
    assert cap.capacidad_de('No copies nada, solo revisa el repo') == 'read'
    assert cap.capacidad_de('Copia este texto') == 'none'


def test_cadena_por_id():
    cid, c = fq._cadena_por_id('construir_feature')
    assert cid == 'construir_feature' and any(p.get('tools') == 'escritura' for p in c['pasos'])
    assert fq._cadena_por_id('no_existe') == (None, None)


if __name__ == '__main__':
    n = 0
    for k, f in list(globals().items()):
        if k.startswith('test_'):
            f()
            n += 1
            print('PASS', k)
    print('PARCHE_N4: %d/%d PASS' % (n, n))
