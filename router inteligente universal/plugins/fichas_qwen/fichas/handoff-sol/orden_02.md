# 10 ÓRDENES DE CORRECCIÓN — QWEN / YAIWES

**Repositorio:** `maxbry123-commits/router-universal-router-inteligente-` · **Rama:** `feat/modos-router`  
**Alcance:** `plugins/puente_chat/`, `plugins/fichas_qwen/`. No modificar el Router principal, Vercel ni HF Jobs. No añadir agentes.  
**Regla:** aplicar por orden → prueba real → conservar aprobación y receipts → registrar PASS/FAIL → no fusionar si falla.

## ORDEN 02 — Qwen: impedir `required` y conservar thinking OFF en reintentos de tool

**Archivo:** `router inteligente universal/plugins/puente_chat/plugin.py`.

En `_llamar_api`, sustituir el bloque completo `if tools and _FORCE_TOOL.get():` situado antes de `cuerpo.update(ex)` por:

```python
if tools and _FORCE_TOOL.get():
    ex.pop('reasoning_effort', None)
    ex.pop('thinking_budget', None)
    cuerpo.pop('reasoning_effort', None)
    cuerpo.pop('thinking_budget', None)

    if modelo.startswith('qwen'):
        cuerpo['tool_choice'] = 'auto'
        if '-preview' in modelo or modelo in _SOLO_THINKING:
            ex.pop('enable_thinking', None)
        else:
            ex['enable_thinking'] = False

    elif modelo.startswith('deepseek'):
        ex['enable_thinking'] = False

    else:
        ex.pop('enable_thinking', None)
```

Para forzar una **función conocida** en Qwen, usar el formato oficial específico, no `required`:

```python
def _tool_especifica_qwen(cuerpo: dict, tools: list, nombre: str) -> None:
    validas = {
        x['function']['name']
        for x in tools
        if x.get('type') == 'function' and isinstance(x.get('function'), dict)
    }
    if nombre not in validas:
        raise ValueError('GAP_TOOL_NO_DISPONIBLE:' + nombre)
    cuerpo['tool_choice'] = {
        'type': 'function', 'function': {'name': nombre}
    }
    cuerpo['enable_thinking'] = False
    cuerpo.pop('reasoning_effort', None)
    cuerpo.pop('thinking_budget', None)
```

**No invocar `_tool_especifica_qwen` cuando el DAG no haya elegido una función exacta.**

**PASS:** reintento de `qwen3.8-max` registra `tool_choice=auto`, `enable_thinking=False`; no devuelve 400; tool real ejecutada o GAP explícito si decide no ejecutarla.