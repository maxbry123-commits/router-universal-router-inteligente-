# RECOVERY PATCH — ROUTER INTELIGENTE UNIVERSAL

Contrato: `tel.workflow/v3` · modo `FAIL_CLOSED_LOOP`.

## Estado válido
- Plan limitado a 3 pasos.
- Paso 1: componentes centralizados; owner público HF verificado en 0 modelos; registry persistido no contiene `model_id` HF; privados/endpoints quedan FLAG no bloqueante.
- Paso 2 ACTIVE: `router inteligente universal/red/enchufe_gate.py` reutilizado desde la fuente canónica y probado determinísticamente.
- Evidencia gate: commit `4007983f2cabecdf78198a1a7ae23aff5fcfa8ce`; test commit `7328d377726dbf435cbc877d6909a5f74a9bcbb3`; log `PASS_ENCHUFE_GATE_V15_REUSE`.
- Paso 3 pendiente.

## Boot de recuperación
1. Leer STATE/CHECKPOINT/PLAN/BITACORA/README arquitectura.
2. Verificar HEAD y SHAs.
3. Continuar P02 cola 1×1: recuperar `red/conectores.py` de la fuente canónica, materializar sin reescribir y probar antes de PATCH.

## GAP-HF-CATALOG-001
No inventar modelos. Reintentar privados/endpoints solo cuando exista nueva credencial/evidencia consumible; mientras tanto continuar tareas P02 independientes.

## Refutaciones
1. COUNT 0 público != ausencia de privados/endpoints.
2. Código fuente documental != integrado hasta materializar + test.
3. PASS unitario Gate != Paso 2 completo.
