# RECOVERY PATCH — ROUTER INTELIGENTE UNIVERSAL

Contrato: `tel.workflow/v3` · modo `FAIL_CLOSED_LOOP`.

## Estado válido
- Plan limitado a 3 pasos.
- Paso 1: componentes centralizados; owner público HF verificado en 0 modelos; registry persistido no contiene `model_id` HF; privados/endpoints quedan FLAG no bloqueante.
- Paso 2 ACTIVE: `red/enchufe_gate.py` y `red/conectores.py` reutilizados desde la fuente canónica y probados antes de PATCH.
- Evidencia Gate: commit `4007983f2cabecdf78198a1a7ae23aff5fcfa8ce`; test `7328d377726dbf435cbc877d6909a5f74a9bcbb3`; `PASS_ENCHUFE_GATE_V15_REUSE`.
- Evidencia conectores: commit `8dc43490cc14f21c6d09d9e3d824606868679766`; test `94ad8b8879c8c03b2f084ac62059bd346da6a610`; `3 passed in 0.11s` / `PASS_CONECTORES_CANONICAL_REUSE_BASELINE`.
- Paso 3 pendiente.

## Boot de recuperación
1. Leer STATE/CHECKPOINT/PLAN/BITACORA/README arquitectura.
2. Verificar HEAD y SHAs.
3. Continuar P02 cola 1×1: PATCH/ADAPT `red/conectores.py` con capacidades v6 demostradas por arquitectura y donors locales; conservar `ConectorHTTP` y `ConectorMCP` existentes.

## GAP-HF-CATALOG-001
No inventar modelos. Reintentar privados/endpoints solo cuando exista nueva credencial/evidencia consumible; mientras tanto continuar tareas P02 independientes.

## Refutaciones
1. COUNT 0 público != ausencia de privados/endpoints.
2. REUSE de conectores + test baseline != catálogo v6 completo.
3. PASS unitario Gate/conectores != Paso 2 completo.
