# RECOVERY PATCH — ROUTER INTELIGENTE UNIVERSAL

Contrato: `tel.workflow/v3` · modo `FAIL_CLOSED_LOOP`.

## Estado válido
- Plan limitado a 3 pasos.
- Paso 1: componentes centralizados; owner público HF 0; privados/endpoints FLAG no bloqueante.
- Paso 2 ACTIVE: Gate/conectores reutilizados desde fuente canónica.
- `ConectorHuggingFace`, `ConectorDB`, `ConectorGitLab`, `ConectorMCPApp`, `ConectorVPS`, `ConectorMemoria`, `ConectorInterno` y `ConectorWebhook` permanecen contractualmente verificados.
- `connector_registry.py` registra HTTP/MCP/MCP App/GitHub/HuggingFace/DB/GitLab/VPS/Memoria/Interno/Webhook.
- `enchufe/validator_v2.py` fue recuperado desde FABLES Enchufe Universal v2, source blob `1f2de5b0578391164e6f6f7331507299130e8579`; HF Job `6aa15fea900620b5c77e6fa1`: `6 passed in 0.02s`.
- C05 `router inteligente universal/domain/schemas/enchufe_v2.py` fue materializado desde el JSON Schema explícito FABLES + DOC-A02; commit `14d86fb07caa02e552a2c5a7788c197084a8d11f`, blob `faf0b8a2f1474c044143728bf7fdfd41d1a751fa`.
- Test C05 `router inteligente universal/tests/test_enchufe_v2_schema.py` commit `96448365568950d9bbd7405f58e001f7eb419f1c`, blob `53d4ee813b51000609532817ca1b5d02a71459f8`; HF Job `6aa165be32d5d0c22c5b07df` COMPLETED success: `4 passed in 0.09s`.
- Primera prueba HF con `python:3.12-slim` fue refutada porque la imagen no incluía `git`; StrategyDelta descargó los blobs exactos de `main` vía raw GitHub y ejecutó pytest sin depender de git.
- Schema/validator/perfiles no autorizan inventar una policy standalone del filtro de comportamiento LLM.
- Paso 3 pendiente.

## Boot de recuperación
1. Leer STATE/CHECKPOINT/PLAN/BITACORA/README arquitectura.
2. Verificar HEAD, blobs y evidencia HF de validator v2 + C05 schema.
3. Continuar P02 cola 1×1 buscando en fuentes de verdad un contrato explícito del behavior filter.
4. Solo si aparece policy explícita, materializarla detrás de guard/plugin y fijar test; si no aparece, continuar únicamente tarea P02 independiente segura con donor audit previo.

## GAP-HF-CATALOG-001
No inventar modelos. Reintentar privados/endpoints solo con nueva evidencia consumible; continuar tareas P02 independientes.

## GAP-BEHAVIOR-CONTRACT-001
`validator_v2`, C05 Pydantic, `perfiles` y `repeticion` son contratos estructurales/invariantes; todavía no existe evidencia de policy standalone allow/deny del comportamiento LLM.

## Refutaciones
1. `EnchufeV2` Pydantic PASS != behavior filter implementado.
2. Donor `guardrails` disponible != policy del proyecto autorizada.
3. Tests C05 PASS != Paso 2 cerrado ni E2E del Paso 3.
