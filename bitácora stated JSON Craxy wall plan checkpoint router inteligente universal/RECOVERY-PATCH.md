# RECOVERY PATCH — ROUTER INTELIGENTE UNIVERSAL

Contrato: `tel.workflow/v3` · modo `FAIL_CLOSED_LOOP`.

## Estado válido
- Plan limitado a 3 pasos.
- Paso 1: componentes centralizados; owner público HF 0; privados/endpoints FLAG no bloqueante.
- Paso 2 ACTIVE: Gate/conectores reutilizados desde fuente canónica.
- `ConectorHuggingFace`, `ConectorDB`, `ConectorGitLab`, `ConectorMCPApp`, `ConectorVPS`, `ConectorMemoria`, `ConectorInterno` y `ConectorWebhook` permanecen contractualmente verificados.
- `connector_registry.py` registra HTTP/MCP/MCP App/GitHub/HuggingFace/DB/GitLab/VPS/Memoria/Interno/Webhook.
- `enchufe/validator_v2.py` recuperado desde FABLES Enchufe Universal v2; HF Job `6aa15fea900620b5c77e6fa1`: `6 passed in 0.02s`.
- C05 `domain/schemas/enchufe_v2.py` verificado; HF Job `6aa165be32d5d0c22c5b07df`: `4 passed in 0.09s`.
- R-003 `red/red_universal.py` estaba ausente del code root pese a figurar `EXISTING_COMPLETE` en Handoff; se recuperó por REUSE desde `2📌🔌ROUTER_UNIVERSAL_RED_CONEXIONES.md`, source blob `692daca7ace7ac983aeb585dd05ac281e571f2f3`.
- Materialización R-003: commit `189a605fbccf703a81269d05777573c14acb68fb`, blob `66154b60ad53aa797094df8741389c8427f9bec0`.
- Test R-003: commit `b7ed873fa8c8b8f848d46c3fd1217206a51480c3`, blob `2be8bcf56fac0bb1c88b0f18edd0330538364726`.
- HF Job `6aa16b3e32d5d0c22c5b0874` fue refutado porque el harness aplanó las rutas; StrategyDelta distinto preservó directorios y HF Job `6aa16b68900620b5c77e7259` dio `5 passed in 0.05s`.
- Schema/validator/perfiles no autorizan inventar una policy standalone del filtro de comportamiento LLM.
- Paso 3 pendiente.

## Boot de recuperación
1. Leer STATE/CHECKPOINT/PLAN/BITACORA/README arquitectura/Handoff.
2. Verificar HEAD/blobs y evidencia HF del último delta R-003.
3. Continuar P02 cola 1×1 auditando C15 Gate v1.5→v2.0 contra contratos ya recuperados.
4. PATCH C15 solo si el contrato exacto demuestra el cambio; mantener firma pública y Enchufe Universal como único boundary.
5. Filtro LLM solo si aparece policy standalone explícita; en otro caso GAP permanece fail-closed.

## GAP-HF-CATALOG-001
No inventar modelos. Reintentar privados/endpoints solo con nueva evidencia consumible; continuar tareas P02 independientes.

## GAP-BEHAVIOR-CONTRACT-001
`validator_v2`, C05 Pydantic, `perfiles` y `repeticion` son contratos estructurales/invariantes; todavía no existe evidencia de policy standalone allow/deny del comportamiento LLM.

## Refutaciones
1. R-003 presente + 5 tests PASS != C15 v2 cableado.
2. Donor `guardrails` disponible != policy LLM autorizada.
3. Tests contractuales PASS != Paso 2 cerrado ni E2E del Paso 3.
