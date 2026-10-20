# 10 ÓRDENES DE CORRECCIÓN — QWEN / YAIWES

**Repositorio:** `maxbry123-commits/router-universal-router-inteligente-` · **Rama:** `feat/modos-router`  
**Alcance:** `plugins/puente_chat/`, `plugins/fichas_qwen/`. No modificar el Router principal, Vercel ni HF Jobs. No añadir agentes.  
**Regla:** aplicar por orden → prueba real → conservar aprobación y receipts → registrar PASS/FAIL → no fusionar si falla.

## ORDEN 08 — Qwen: distinguir rate limit, cuota, autenticación y timeout

**Archivo:** `router inteligente universal/plugins/puente_chat/plugin.py`.

Añadir antes de `_llamar_api`:

```python
def _clasificar_error_qwen(status, payload):
    detalle = json.dumps(payload, ensure_ascii=False, default=str).lower()
    if status in (401, 403):
        return 'AUTH'
    if status in (404, 410):
        return 'MODEL_UNAVAILABLE'
    if status == 429:
        if 'insufficient_quota' in detalle or (
            'quota' in detalle and 'rate' not in detalle
        ):
            return 'QUOTA_EXHAUSTED'
        return 'RATE_LIMIT'
    if status in (500, 502, 503, 504):
        return 'TRANSIENT'
    if status == 400:
        return 'INVALID_PARAMETERS'
    if status == 0:
        return 'NETWORK_TIMEOUT'
    return 'OTHER'
```

En `_llamar_api`, sustituir el bloque actual `if ultimo[0] == 429:` por:

```python
if ultimo[0] == 429:
    causa = _clasificar_error_qwen(ultimo[0], ultimo[1])
    if causa == 'QUOTA_EXHAUSTED':
        muertas.add(i)
        continue

    restante = fin - time.monotonic()
    if restante < 65:
        return 429, {
            'error': 'GAP_QWEN_RATE_LIMIT',
            'retry_after_s': 60,
            'detalle': ultimo[1],
        }

    time.sleep(min(60, max(0, restante - 5)))
    continue
```

Mantener el `checkpoint` del DAG antes de cualquier reintento externo; no duplicar operaciones de escritura cuando exista receipt previo.

**PASS:** cuota agotada → detener; rate limit temporal → esperar con presupuesto suficiente o devolver `GAP_QWEN_RATE_LIMIT` con `retry_after_s`; autenticación inválida → no repetir.