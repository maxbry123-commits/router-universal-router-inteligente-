# RECOVERY PATCH — ROUTER INTELIGENTE UNIVERSAL

Contrato: `tel.workflow/v3` · modo `FAIL_CLOSED_LOOP`.

## Estado válido
- Plan limitado a 3 pasos.
- Paso 1: componentes centralizados; owner público HF 0; privados/endpoints FLAG no bloqueante.
- Paso 2 ACTIVE: Gate/conectores reutilizados desde fuente canónica.
- `ConectorHuggingFace`, `ConectorDB`, `ConectorGitLab`, `ConectorMCPApp` y `ConectorVPS` permanecen contractualmente verificados.
- `ConectorMemoria` ya existía en `router inteligente universal/red/conectores.py`; REUSE sin adapter duplicado y WIRE único en registry.
- Registry Memoria commit `3987856e107e848e111d96317e3a9c92c40a6cbb`, blob `878d0fb69fce49b62fc9e2d934b3d8896c5cc4c9`.
- Test Memoria commit `de82bd75e630f13141df7b2b2b74131163e52200`, blob `0263e511694b7a45b3b8ffaec0f3d0e7b9e2d582`.
- Verify remoto: HF Job `6aa1318d32d5d0c22c5afe2c`; `FETCHED_EXACT_MAIN 5`; `3 passed in 0.04s`.
- Paso 3 pendiente.

## Boot de recuperación
1. Leer STATE/CHECKPOINT/PLAN/BITACORA/README arquitectura.
2. Verificar HEAD y SHAs.
3. Continuar P02 cola 1×1 con siguiente conector v6 respaldado por arquitectura; conservar registry y baselines.

## GAP-HF-CATALOG-001
No inventar modelos. Reintentar privados/endpoints solo con nueva evidencia consumible; continuar tareas P02 independientes.

## Refutaciones
1. ConectorMemoria contractual PASS != State Engine real integrado de extremo a extremo.
2. Registry con Memoria != catálogo v6 completo.
3. PASS contractual != Paso 2 ni Paso 3 completos.
