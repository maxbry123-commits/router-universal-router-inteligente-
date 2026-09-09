# RECOVERY PATCH — ROUTER INTELIGENTE UNIVERSAL

Contrato: `tel.workflow/v3` · modo `FAIL_CLOSED_LOOP`.

## Estado válido
- Plan limitado a 3 pasos.
- Paso 1: componentes centralizados; owner público HF 0; privados/endpoints FLAG no bloqueante.
- Paso 2 ACTIVE: Gate/conectores reutilizados desde fuente canónica.
- `ConectorHuggingFace`, `ConectorDB`, `ConectorGitLab`, `ConectorMCPApp`, `ConectorVPS`, `ConectorMemoria`, `ConectorInterno` y `ConectorWebhook` permanecen contractualmente verificados.
- `ConectorInterno` y `ConectorWebhook` ya existían en `router inteligente universal/red/conectores.py`; REUSE sin adapters duplicados y registry existente reconciliado.
- Registry blob `4beb5b96e5abb6ff7263cdf2297628058a98e790` contiene `interno` y `webhook`.
- Test `router inteligente universal/tests/test_conector_interno_webhook_v6.py` blob `b7dc3343b7515ad9a1f57ccee983ace65bb03a6b` verifica resolución de ambos, comportamiento Interno y fail-closed Webhook sin env.
- Verify remoto: HF Job `6aa13ab432d5d0c22c5b008f`; `FETCHED_EXACT_MAIN 5`; `3 passed in 0.11s`.
- Paso 3 pendiente.

## Boot de recuperación
1. Leer STATE/CHECKPOINT/PLAN/BITACORA/README arquitectura.
2. Verificar HEAD y SHAs.
3. Continuar P02 cola 1×1 con siguiente delta respaldado por arquitectura; conservar registry y baselines.

## GAP-HF-CATALOG-001
No inventar modelos. Reintentar privados/endpoints solo con nueva evidencia consumible; continuar tareas P02 independientes.

## Refutaciones
1. ConectorWebhook contractual PASS != entrega real a Telegram/Discord/n8n/Zapier.
2. Registry con catálogo actual != backend C01-C23 completo.
3. PASS contractual != Paso 2 ni Paso 3 completos.
