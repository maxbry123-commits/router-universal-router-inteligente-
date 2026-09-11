# RECOVERY PATCH — ROUTER INTELIGENTE UNIVERSAL
Contrato: `tel.workflow/v3` · `FAIL_CLOSED_LOOP`.

## Estado recuperable preservado
Core RIU-0058=`VERIFIED_CLOSED`; P01/P02/P03 cerrados.
Certificación HF ampliada=`MODEL_CERTIFICATION_20_OF_20_ACCOUNTED`.
Regresión global core=`FINAL_REGRESSION_E2E_PASS`.

## Nueva fase recuperable — RIU-0063 conectividad centralizada
Objetivo: toda conectividad de proyectos pasa por Router Inteligente Universal y queda inventariada bajo `conectividad con Router inteligente universal/`.

### Artefactos canónicos
- `MAPA-MENTAL-CONECTIVIDAD-RIU.md`
- `REGISTRY-CONECTIVIDAD-RIU.json`
- `PUENTE-RIU-router-universal-router-inteligente-.yaml`
- cada repo propietario contiene exactamente un `PUENTE-RIU-<repo>.yaml` dentro de la misma raíz lógica.

### Estado material
- repos esperados: 19
- bridges declarados: 19
- fallos de persistencia: 0
- GitHub runtime credential validation: PENDING
- Hugging Face runtime credential validation: PENDING
- Claude/GitHub MCP boundary validation: PENDING
- Claude memory_store boundary validation: PENDING
- Global connectivity E2E: PENDING

### Conexiones recuperadas
Claude/GitHub MCP: fuente histórica `maxbry123-commits/TAREA-1/skills/claude-api/`; patrón `github_repository` + `https://api.githubcopilot.com/mcp/` + auth externa vault/runtime.
Claude memoria persistente: fuente `maxbry123-commits/TAREA-1/skills/claude-api/shared/managed-agents-memory.md`; recurso `memory_store` persistente entre sesiones; bridge TAREA-1 enriquecido, aún no E2E.
Hugging Face: cuenta observada `COMAND-CENTER-1`; Jobs CPU/GPU usados previamente; workflow histórico `TAREA-1/.github/workflows/yaiwes-hf-static-publish.yml`; toda credencial queda fuera de Git.
Memoria/estado propios: `MEMORIA`, `BIBLIOTECA`, `BITACORA-MAXBRY`, `Cerebro` mapeados como targets pendientes de E2E Router.

## Evidencias RIU-0063 actuales
- mapa central enriquecido `a8331c4f866d0f90d5d0936e2dc7469021562e27`
- registry 19/19 + conexiones `0a6289861460c9bce4e091c7e39d3cb02724075a`
- TAREA-1 bridge enriquecido `295c380ebee82ccf49a7623bd3bb7320e847fad0`
- arquitectura `7a475f55849692b461379de44d69e1e2f038f183`
- handoff `2b5b63ffd9fe0bb0cd74fbcc6de0ef8972f2647d`
- STATE `c32184ad9840f33030fa3601628eebb5dff38ea3`
- Crazy Wall `c2428802f42df5275b867b8624425e79c93b4c5e`
- CHECKPOINT `b38651c5b400a887ecf5c080b0c598efe5380f3b`
- PLAN `509e44be501bc556b4f8e372b6178c6876fac586`

## Reglas de recuperación
1. No repetir P01-P03 ni certificación 20/20 salvo regresión.
2. No exponer ni persistir valores secretos.
3. Retomar en `GITHUB_RUNTIME_CREDENTIAL_VALIDATION` cuando el Director confirme los tokens runtime.
4. Seguir cola 1×1 hasta GitHub PASS → HF PASS → MCP boundary PASS → memory boundary PASS → global E2E PASS → cierre documental.
5. Cualquier fallo queda FLAG/GAP con evidencia, nunca PASS falso.

## Gate actual
`ALL_REPOS_BRIDGED=PASS(19/19)`.
`CONNECTIVITY_LAYER_VERIFIED_CLOSED=PENDING`.
