# 10 ÓRDENES DE CORRECCIÓN — QWEN / YAIWES

**Repositorio:** `maxbry123-commits/router-universal-router-inteligente-` · **Rama:** `feat/modos-router`  
**Alcance:** `plugins/puente_chat/`, `plugins/fichas_qwen/`. No modificar el Router principal, Vercel ni HF Jobs. No añadir agentes.  
**Regla:** aplicar por orden → prueba real → conservar aprobación y receipts → registrar PASS/FAIL → no fusionar si falla.

## ORDEN 10 — Prueba de integración REAL del Harness y DAG N4 → N6/N7

**Crear:** `router inteligente universal/tests/smoke_harness_qwen_read.py`. Test de integración **solo lectura** con el Harness existente; no simular tool calls ni dar permisos de escritura.

```python
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
```

**Ejecutar desde el repositorio con el entorno/credenciales ya configurados:**

```bash
python 'router inteligente universal/tests/smoke_harness_qwen_read.py'
```

**Después, en la Ficha 2, ejecutar una tarea controlada de cambio real aprobada expresamente:**

```text
INPUT → PLAN → ESPERANDO_APROBACION → /aprobar
→ N4 TOOL WRITE REAL → RECEIPT DONE → N6/N7 READ VERIFY
→ EVIDENCIA COMMIT + TEST → CUMPLIDO
```

**Puerta de aceptación:** `N4` con mutación exitosa y receipt durable; `N6/N7` con lecturas/pruebas reales; ninguna respuesta `GAP` como PASS; sin reejecución duplicada después de checkpoint; 10/10 órdenes verificadas. Si alguna falla, detener cierre y conservar el GAP concreto.