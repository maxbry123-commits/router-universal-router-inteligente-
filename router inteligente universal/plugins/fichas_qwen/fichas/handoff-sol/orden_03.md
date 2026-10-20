# 10 ÓRDENES DE CORRECCIÓN — QWEN / YAIWES

**Repositorio:** `maxbry123-commits/router-universal-router-inteligente-` · **Rama:** `feat/modos-router`  
**Alcance:** `plugins/puente_chat/`, `plugins/fichas_qwen/`. No modificar el Router principal, Vercel ni HF Jobs. No añadir agentes.  
**Regla:** aplicar por orden → prueba real → conservar aprobación y receipts → registrar PASS/FAIL → no fusionar si falla.

## ORDEN 03 — Qwen CODE: separar planificación, ejecución y auditoría

**Archivo:** `router inteligente universal/plugins/puente_chat/plugin.py`.

Sustituir `_qwen_razonamiento_compatible(modelo_api, ex, tools)` por:

```python
def _qwen_razonamiento_compatible(modelo_api, ex, tools):
    modelo = str(modelo_api or '')
    if not modelo.startswith('qwen'):
        return ex

    ex = dict(ex)
    if not tools:
        ex.pop('thinking_budget', None)
        return ex

    thinking_tools = (
        os.environ.get('RIU_QWEN_TOOLS_THINKING_TESTED') == '1'
        and str((_IDS_CTX.get() or {}).get('ficha_id') or '')
            in ('ficha2-dag-codigo', 'ficha3-frontend')
        and str(_PERFIL.get() or '') in ('code', 'auditoria')
        and not _FORCE_TOOL.get()
        and modelo in ('qwen3.8-max', 'qwen3.8-flash')
    )

    if '-preview' in modelo or modelo in _SOLO_THINKING:
        ex.pop('enable_thinking', None)
        return ex

    if thinking_tools:
        ex['enable_thinking'] = True
        ex['reasoning_effort'] = (
            'medium' if modelo == 'qwen3.8-max' else 'low'
        )
        ex['preserve_thinking'] = True
    else:
        ex['enable_thinking'] = False
        ex.pop('reasoning_effort', None)
        ex.pop('preserve_thinking', None)
    ex.pop('thinking_budget', None)
    return ex
```

**Instrucciones:** mantener `RIU_QWEN_TOOLS_THINKING_TESTED=0` por defecto; ejecutar pruebas del orden 09 con tools sin pensamiento; activar `=1` exclusivamente en `code`/`auditoria` después de confirmar compatibilidad real. No introducir parámetro API inventado `mode=agent` o `mode=code`.

**PASS:** planificador razona; llamada simple a tool usa thinking OFF; code complejo usa thinking ON únicamente tras activación; sin incompatibilidad de `reasoning_effort`/`thinking_budget`.