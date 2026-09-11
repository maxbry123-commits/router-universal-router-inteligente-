# PARCHE DE RECUPERACIÓN — ROUTER INTELIGENTE UNIVERSAL

Contrato: `tel.workflow/v3` · `FAIL_CLOSED_LOOP`.

## Core preservado
RIU-0062=`VERIFIED_CLOSED`.
P01/P02/P03 cerrados; API Key Manager 100 slots + E2E verificados; `MODEL_CERTIFICATION_20_OF_20_ACCOUNTED`; regresión global final PASS.

## RIU-0063 — Conectividad centralizada multi-repo
Nueva tarea autorizada: toda conectividad de proyectos debe pasar por Router Inteligente Universal y quedar centralizada en:
`conectividad con Router inteligente universal/`.

Artefactos centrales:
- `MAPA-MENTAL-CONECTIVIDAD-RIU.md`
- `REGISTRY-CONECTIVIDAD-RIU.json`
- `PUENTE-RIU-router-universal-router-inteligente-.yaml`

Cada repo propiedad de `maxbry123-commits` tiene un único archivo puente `PUENTE-RIU-<repo>.yaml` dentro de la misma raíz lógica. Estado material: `19/19 BRIDGE_DECLARED`, fallos de persistencia=0.

## Conexiones recuperadas
- Claude Managed Agents ↔ GitHub: `github_repository` + `https://api.githubcopilot.com/mcp/` + auth vault/runtime; fuente histórica `TAREA-1/skills/claude-api/`.
- Claude memoria persistente: `memory_store` en recursos de sesión; fuente `TAREA-1/skills/claude-api/shared/managed-agents-memory.md`.
- Hugging Face: cuenta observada `COMAND-CENTER-1`, Jobs CPU/GPU y workflow histórico `TAREA-1/.github/workflows/yaiwes-hf-static-publish.yml`.
- Memoria/estado propios: `MEMORIA`, `BIBLIOTECA`, `BITACORA-MAXBRY`, `Cerebro` registrados como targets.

## Estado del nuevo gate
- `ALL_REPOS_BRIDGED=PASS(19/19)`
- `ROUTER_REGISTRY_COMPLETE=PASS`
- `GITHUB_ACCESS_VERIFIED=PENDING`
- `HF_ACCESS_VERIFIED=PENDING`
- `MCP_BOUNDARY_VERIFIED=PENDING`
- `MEMORY_BOUNDARY_VERIFIED=PENDING`
- `CONNECTIVITY_GLOBAL_E2E_PASS=PENDING`

## Seguridad
No almacenar tokens, PAT, OAuth ni claves API en Git. Toda autenticación vive en almacén runtime externo/vault/Codespaces/Actions/HF según corresponda. Router registra referencias/capacidades y falla cerrado si falta autenticación o evidencia.

## Evidencia actual RIU-0063
Mapa=`a8331c4f866d0f90d5d0936e2dc7469021562e27`; Registry=`0a6289861460c9bce4e091c7e39d3cb02724075a`; TAREA-1 bridge enriquecido=`295c380ebee82ccf49a7623bd3bb7320e847fad0`; README arquitectura=`7a475f55849692b461379de44d69e1e2f038f183`; Handoff=`2b5b63ffd9fe0bb0cd74fbcc6de0ef8972f2647d`; STATE=`c32184ad9840f33030fa3601628eebb5dff38ea3`; Crazy Wall=`c2428802f42df5275b867b8624425e79c93b4c5e`; CHECKPOINT=`b38651c5b400a887ecf5c080b0c598efe5380f3b`; PLAN=`509e44be501bc556b4f8e372b6178c6876fac586`; RECOVERY=`4c2508e4add7884b797bd8aecd76a69dc0c2a8bc`.

## Regla de recuperación
No repetir core ni certificación ya cerrada salvo evidencia contradictoria. Retomar RIU-0063 en `GITHUB_RUNTIME_CREDENTIAL_VALIDATION` cuando el Director confirme credenciales runtime. Seguir GitHub → Hugging Face → MCP → memory → E2E global → cierre documental. Nunca promover un fallo a PASS.
