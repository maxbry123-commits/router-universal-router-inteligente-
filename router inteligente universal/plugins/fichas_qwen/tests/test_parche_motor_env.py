"""PARCHE_MOTOR_ENV offline: el modelo no fija PATH/LD_PRELOAD/tokens del motor; el Harness inyecta el token; el motor ve variables propias.
Desde 'router inteligente universal/':  PYTHONPATH=. python3 plugins/fichas_qwen/tests/test_parche_motor_env.py"""
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import plugins.puente_chat.plugin as pcm  # noqa: E402

BASE = str(pcm._CONFIG_DIR / 'motores_descarga')


class _R:
    returncode = 0; stdout = 'ok'; stderr = ''


def _corre(env_modelo):
    vistos = {}
    class _Sub:
        @staticmethod
        def run(cmd, env=None, **k):
            vistos.update(env or {}); vistos['__cmd'] = cmd[-1]; return _R()
    o = (pcm._embed_rank, pcm._paso_llm, pcm._sub, pcm._herr)
    pcm._embed_rank = lambda q, items: 0
    pcm._paso_llm = lambda *a, **k: json.dumps({'env': env_modelo, 'explicacion': 'x'}) if 'JSON' in str(a[2][-1]['content']) else 'resumen'
    pcm._sub = _Sub
    class _H:
        @staticmethod
        def _token_gh(repo='', escritura=False): return 'tok-del-harness' if escritura else ''
    pcm._herr = lambda: _H
    try:
        pcm._motor_descarga('a -> b')
    finally:
        pcm._embed_rank, pcm._paso_llm, pcm._sub, pcm._herr = o
    return vistos


def test_el_modelo_no_inyecta_variables_peligrosas_ni_tokens():
    v = _corre({'LD_PRELOAD': '/tmp/x.so', 'PATH': '/tmp/evil', 'GITHUB_TOKEN': 'robado', 'HF_TOKEN': 'x', 'PYTHONPATH': '/tmp/m', 'DEST_REPO': 'maxbry123-commits/frontend', 'PUBLISH': '1'})
    assert v.get('LD_PRELOAD') != '/tmp/x.so' and v.get('PATH') != '/tmp/evil' and v.get('PYTHONPATH') != '/tmp/m'
    assert v.get('GITHUB_TOKEN') == 'tok-del-harness' and v.get('HF_TOKEN') != 'x'
    assert v.get('DEST_REPO') == 'maxbry123-commits/frontend' and v.get('PUBLISH') == '1'


def test_helper_solo_variables_que_el_motor_lee():
    e = pcm._env_motor(BASE, {'ARCHIVE_INPUT': 'a.zip', 'DEST_DIR': 'd', 'INVENTADA': 'x'})
    assert e.get('ARCHIVE_INPUT') == 'a.zip' and e.get('DEST_DIR') == 'd' and 'INVENTADA' not in e


if __name__ == '__main__':
    n = 0
    for k, f in list(globals().items()):
        if k.startswith('test_'):
            f(); n += 1; print('PASS', k)
    print('MOTOR_ENV: %d/%d PASS' % (n, n))
