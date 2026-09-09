# RECOVERY PATCH — ROUTER INTELIGENTE UNIVERSAL

Contrato: `tel.workflow/v3` · modo `FAIL_CLOSED_LOOP`.

## Estado válido
- Plan limitado a 3 pasos.
- Paso 1: componentes centralizados; owner público HF 0; privados/endpoints FLAG no bloqueante.
- Paso 2 ACTIVE: Gate/conectores reutilizados desde fuente canónica.
- `ConectorHuggingFace`, `ConectorDB`, `ConectorGitLab`, `ConectorMCPApp`, `ConectorVPS`, `ConectorMemoria`, `ConectorInterno` y `ConectorWebhook` permanecen contractualmente verificados.
- `connector_registry.py` registra HTTP/MCP/MCP App/GitHub/HuggingFace/DB/GitLab/VPS/Memoria/Interno/Webhook.
- StrategyDelta recuperó el contrato real `validator_v2.py` desde FABLES Enchufe Universal v2, source blob `1f2de5b0578391164e6f6f7331507299130e8579`.
- `router inteligente universal/enchufe/validator_v2.py` existe ahora en `main`, commit `2e20488e384ad658675d1ccaf6726fa1edd02034`, blob `418f230e705d18525aae63d6930311ccb7b9297b`.
- Test contractual final commit `de9326ff0167a04024a09fc60617c8bf6b75ae28`, blob `4aa5d4a878f582b82f254cd5ff1fda8d9161fe14`; HF Job `6aa15fea900620b5c77e6fa1` COMPLETED: `6 passed in 0.02s`.
- Recuperar el validador no autoriza inventar una policy standalone del filtro de comportamiento LLM.
- Paso 3 pendiente.

## Boot de recuperación
1. Leer STATE/CHECKPOINT/PLAN/BITACORA/README arquitectura.
2. Verificar HEAD, blobs y evidencia HF del validator v2.
3. Continuar P02 cola 1×1 buscando en fuentes de verdad un contrato explícito del behavior filter.
4. Solo si aparece policy explícita, materializarla detrás de guard/plugin y fijar test; si no aparece, continuar únicamente tarea P02 independiente segura.

## GAP-HF-CATALOG-001
No inventar modelos. Reintentar privados/endpoints solo con nueva evidencia consumible; continuar tareas P02 independientes.

## GAP-BEHAVIOR-CONTRACT-001
Estado refinado: `validator_v2` fue recuperado y probado, pero no se recuperó todavía una policy standalone allow/deny del comportamiento LLM. `perfiles`/`repeticion` del Enchufe v2 son invariantes contractuales, no permiso para inferir semántica adicional.

## Refutaciones
1. `validator_v2` PASS != behavior filter implementado.
2. Donor `guardrails` disponible != policy del proyecto autorizada.
3. Seis tests contractuales PASS != Paso 2 cerrado ni E2E del Paso 3.
