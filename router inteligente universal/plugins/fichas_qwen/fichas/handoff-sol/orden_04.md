# 10 ÓRDENES DE CORRECCIÓN — QWEN / YAIWES

**Repositorio:** `maxbry123-commits/router-universal-router-inteligente-` · **Rama:** `feat/modos-router`  
**Alcance:** `plugins/puente_chat/`, `plugins/fichas_qwen/`. No modificar el Router principal, Vercel ni HF Jobs. No añadir agentes.  
**Regla:** aplicar por orden → prueba real → conservar aprobación y receipts → registrar PASS/FAIL → no fusionar si falla.

## ORDEN 04 — Qwen: mantener SSE en TODOS los reintentos

**Archivo:** `router inteligente universal/plugins/puente_chat/plugin.py` · función `_llamar_api`.

Tras calcular `_stream`, declarar la función local y llamarla para el primer intento y las tres reparaciones (`max_completion_tokens`, contexto y extras rechazados):

```python
_stream = proveedor == 'qwencloud' or (proveedor == 'nvidia' and not tools)

def _solicitar_modelo(payload, segundos):
    url = base + '/chat/completions'
    if _stream:
        return _http_stream(
            url, clave, payload, segundos, sf or (lambda _c: None)
        )
    return _http('POST', url, clave, payload, segundos)

ultimo = _solicitar_modelo(cuerpo, resta)
```

Sustituir **cada** reintento local de esta función:

```python
ultimo = _http('POST', base + '/chat/completions', clave, cuerpo, resta)
```

por:

```python
ultimo = _solicitar_modelo(cuerpo, resta)
```

No alterar `_http()` para los otros proveedores. No cambiar el parser SSE existente.

**PASS:** `audit_llm` registra stream verdadero en Qwen durante primera llamada y reparaciones; las llamadas con tools mantienen `tool_calls` íntegros.