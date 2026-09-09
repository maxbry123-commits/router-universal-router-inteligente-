# RECOVERY PATCH — ROUTER INTELIGENTE UNIVERSAL

Contrato: `tel.workflow/v3` · modo `FAIL_CLOSED_LOOP`.

## Estado válido
- Plan limitado a 3 pasos.
- Paso 1: componentes centralizados; owner público HF 0; privados/endpoints FLAG no bloqueante.
- Paso 2 ACTIVE: Gate/conectores reutilizados desde fuente canónica.
- `ConectorHuggingFace` v6 verificado por contrato: pytest 3/3 PASS.
- `ConectorDB` v6 integrado en `router inteligente universal/red/conectores.py`; commit `885cf992222e59097e5042b74b5371a3a4aa7d1a`, blob `beca488fdb34ff14ee2f5b4e4ef8c8de45ee9c78`.
- Test `router inteligente universal/tests/test_conector_db_v6.py`; commit `0f6681e17988554a3206d9d3fac7326028ae24dc`.
- Verify remoto fijado al commit: HF Job `6aa1105432d5d0c22c5af971`, `3 passed in 0.10s`.
- Primer intento de verify falló solo por ausencia de pytest en el entorno; StrategyDelta instaló pytest/httpx y repitió contra el mismo commit con PASS.
- Paso 3 pendiente.

## Boot de recuperación
1. Leer STATE/CHECKPOINT/PLAN/BITACORA/README arquitectura.
2. Verificar HEAD y SHAs.
3. Continuar P02 cola 1×1 con el siguiente conector v6 prioritario; preservar HTTP/MCP/GitHub/HF/DB verificados.

## GAP-HF-CATALOG-001
No inventar modelos. Reintentar privados/endpoints solo con nueva evidencia consumible; continuar tareas P02 independientes.

## Refutaciones
1. Adapter DB probado con contrato/injection != DB remoto real del Paso 3.
2. HF/DB adapters PASS != catálogo v6 completo.
3. PASS unitario/contractual != Paso 2 ni Paso 3 completos.
