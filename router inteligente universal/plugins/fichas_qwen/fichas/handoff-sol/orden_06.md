# 10 ÓRDENES DE CORRECCIÓN — QWEN / YAIWES

**Repositorio:** `maxbry123-commits/router-universal-router-inteligente-` · **Rama:** `feat/modos-router`  
**Alcance:** `plugins/puente_chat/`, `plugins/fichas_qwen/`. No modificar el Router principal, Vercel ni HF Jobs. No añadir agentes.  
**Regla:** aplicar por orden → prueba real → conservar aprobación y receipts → registrar PASS/FAIL → no fusionar si falla.

## ORDEN 06 — No contabilizar respuestas `GAP` como herramientas exitosas

**Archivo:** `router inteligente universal/plugins/puente_chat/plugin.py`.

Sustituir la constante existente por:

```python
_FALLO = ('ERROR', 'HTTP 4', 'HTTP 5', 'HTTP 0', 'GAP', 'TIMEOUT')


def _tool_exito(res) -> bool:
    return not str(res or '').strip().upper().startswith(_FALLO)
```

En `_bucle`, sustituir todas las verificaciones:

```python
not str(res).startswith(_FALLO)
```

por:

```python
_tool_exito(res)
```

Y sustituir:

```python
ok_ = not res.startswith(_FALLO)
```

por:

```python
ok_ = _tool_exito(res)
```

No emitir receipt `DONE`, no guardar `hechas[sello]` y no producir `mutacion_real=True` cuando `_tool_exito(res)` sea falso. Mantener receipt `PREPARED` para reconciliación segura.

**PASS:** `GAP_RECEIPT_NO_PERSISTIDO`, `GAP_TOOL_RESULT_INDETERMINADO`, `ERROR` y `HTTP 429` → `ok=False`, no `DONE`; resultado real exitoso → `ok=True`.