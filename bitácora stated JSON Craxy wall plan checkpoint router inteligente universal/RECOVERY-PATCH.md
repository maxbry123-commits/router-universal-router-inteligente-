# RECOVERY PATCH — ROUTER INTELIGENTE UNIVERSAL

Contrato: `tel.workflow/v3` · modo `FAIL_CLOSED_LOOP`.

## Estado válido
- Plan limitado a 3 pasos.
- Paso 1: componentes centralizados; owner público HF 0; privados/endpoints FLAG no bloqueante.
- Paso 2 ACTIVE: Gate/conectores reutilizados desde fuente canónica.
- `ConectorHuggingFace` y `ConectorDB` v6 permanecen contractualmente verificados.
- Nuevo `ConectorGitLab` separado en `router inteligente universal/red/conector_gitlab.py`.
- Código GitLab commit `122e5baeec061e89be2fe32411d0b3d5ee70f6aa`, blob `d0e1de92a0cb3ab1577e29c2c83adf020806f4c1`.
- Registry explícito `red/connector_registry.py` commit `0c13109de1f2e120b9c3eea7990026b4c80f8639`.
- Test GitLab/registry commit `0e5dbf8d4efa34df83397fea6631a74bb7896c12`.
- Verify remoto: HF Job `6aa11334900620b5c77e5ca7` status `success` ejecutando pytest del contrato GitLab.
- Paso 3 pendiente.

## Boot de recuperación
1. Leer STATE/CHECKPOINT/PLAN/BITACORA/README arquitectura.
2. Verificar HEAD y SHAs.
3. Continuar P02 cola 1×1 con siguiente conector v6 respaldado por arquitectura; conservar registry y baselines.

## GAP-HF-CATALOG-001
No inventar modelos. Reintentar privados/endpoints solo con nueva evidencia consumible; continuar tareas P02 independientes.

## Refutaciones
1. Adapter GitLab probado contractualmente != GitLab remoto autenticado del Paso 3.
2. Registry con GitLab != catálogo v6 completo.
3. PASS contractual != Paso 2 ni Paso 3 completos.
