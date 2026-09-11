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
- Global connectivity E2E: PENDING

### Conexiones recuperadas
Claude/GitHub MCP: fuente histórica `maxbry123-commits/TAREA-1/skills/claude-api/`; patrón `github_repository` + `https://api.githubcopilot.com/mcp/` + auth externa vault/runtime.
Hugging Face: cuenta observada `COMAND-CENTER-1`; Jobs CPU/GPU usados previamente; toda credencial queda fuera de Git.
Memoria/estado: `MEMORIA`, `BIBLIOTECA`, `BITACORA-MAXBRY`, `Cerebro` mapeados como targets pendientes de E2E Router.

## Evidencias RIU-0063
- mapa central `b74d6220b8ddbead8a77af48e04b0970d2ddea60`
- registry inicial `f56d64668448363a62684066d5f1a8685dcd31f7`
- registry 19/19 `87b5f3c61a94e69494450829772a74b0eee552c9`
- arquitectura `be0dc26ab4f6aac525c06decbb56bab20829457a`
- handoff `6a8facc3bfc9ea3616f6d5c93493d2db4c6731e1`
- STATE `cb7a184aac29ee1967ad5b13a5e9917303a0d0fd`
- Crazy Wall `8116f24e147a61697d235f30612184e67e586537`
- CHECKPOINT `4b8cb86bf347248455a1e8a0975c0a3b3c5298d0`
- PLAN `50060a46671c2735ee9af3ea5de9fc5c3a214df1`

## Reglas de recuperación
1. No repetir P01-P03 ni certificación 20/20 salvo regresión.
2. No exponer ni persistir valores secretos.
3. Retomar en `GITHUB_RUNTIME_CREDENTIAL_VALIDATION` cuando el Director confirme los tokens runtime.
4. Seguir cola 1×1 hasta GitHub PASS → HF PASS → MCP boundary PASS → global E2E PASS → cierre documental.
5. Cualquier fallo queda FLAG/GAP con evidencia, nunca PASS falso.

## Gate actual
`ALL_REPOS_BRIDGED=PASS(19/19)`.
`CONNECTIVITY_LAYER_VERIFIED_CLOSED=PENDING`.
