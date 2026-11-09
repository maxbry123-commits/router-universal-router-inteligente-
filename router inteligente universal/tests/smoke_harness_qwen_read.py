import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

from plugins.puente_chat import plugin as pc  # noqa: E402

modelo = next(
    (ident for ident, ficha in pc.FICHAS.items()
     if ficha[1] == 'qwencloud' and ficha[2] == 'qwen3.8-max'),
    None,
)
assert modelo, 'FAIL: Qwen 3.8 Max ausente del catálogo'

r = pc._chat({
    'model': modelo,
    'sesion': 'smoke-qwen-read',
    'messages': [{
        'role': 'user',
        'content': (
            'Usa github_leer para leer el archivo '
            'router inteligente universal/plugins/puente_chat/plugin.py '
            'del repositorio maxbry123-commits/router-universal-router-inteligente- '
            'en la rama feat/modos-router. No escribas ni modifiques nada.'
        ),
    }],
    'max_tokens': 2000,
    'presupuesto_s': 180,
    'solo_lectura': True,
    'requiere_tools': True,
    'tools_habilitadas': True,
    'cap_tools': 'read',
    'perfil': 'code',
    'tarea_id': 'SMOKE-READ-01',
    'task_id': 'SMOKE-READ-01',
})
assert isinstance(r, dict), 'FAIL: salida no estructurada'
assert not r.get('error'), f'FAIL: {r.get("error")}: {r.get("detalle", "")}'
uso = r.get('evidencia_tools') or r.get('herramientas') or []
assert any(x.get('ok') and x.get('tool') == 'github_leer' for x in uso), (
    f'FAIL: github_leer no ejecutado: {uso!r}'
)
assert not any(x.get('mutacion_real') for x in uso), 'FAIL: mutación en READ'
print('PASS: Qwen → Harness → github_leer real → evidencia READ')
