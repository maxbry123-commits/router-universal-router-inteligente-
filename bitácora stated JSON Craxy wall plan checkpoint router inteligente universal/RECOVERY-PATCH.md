# RECOVERY PATCH — ROUTER INTELIGENTE UNIVERSAL
Contrato: `tel.workflow/v3` · `FAIL_CLOSED_LOOP`.

## Estado preservado
Core P01-P03=`VERIFIED_CLOSED`; `MODEL_CERTIFICATION_20_OF_20_ACCOUNTED`; regresión global core=`PASS`.

## RIU-0063/0064 — Connectivity Fabric
Objetivo: toda conectividad de proyectos pasa por Router Inteligente Universal bajo `conectividad con Router inteligente universal/`.

### Estado material verificado
- 19/19 repositorios con exactamente un `PUENTE-RIU-<repo>.yaml` en `riu.connectivity.bridge/v2` y read-back.
- registry central v2 sincronizado; blob `aa27dc728af98af73741ad287cdcd6bdee6addeb`.
- runtime `router inteligente universal/integration/connectivity_runtime.py`; blob `0a26e4133efba1e5343685eff9fe17a88a7ea3a3`.
- Router bridge v2/runtime-tested; blob `469ee974ea6c0f3edfb38443b96ef19b83f6df81`.
- frontend v2 incluye GitHub, HF `COMAND-CENTER-1`, HF Jobs CPU/GPU, models/datasets/spaces/jobs, Claude `github_repository` + GitHub MCP y memoria.
- TAREA-2 v2 commit `0848a33e21a8e48d62597d05ca363caac40f64f8`, blob `dab6ebdc7b7a973314df7ce2126a432cc0388658`.
- runtime tests ejecutados en HF Job `6aa490c35527934177ecacb3`: `COMPLETED`, `3 passed in 0.02s`.

### Secret boundary
Store autorizado: `https://github.com/settings/codespaces`.
HF refs: `RIU_HF_TOKEN`, `HF_TOKEN`, `HUGGINGFACE_TOKEN`.
GitHub/MCP refs: `RIU_GITHUB_PAT`, `GITHUB_TOKEN`, `GH_TOKEN`.
Valores crudos prohibidos en Git, logs, README, STATE, registry y respuestas.

### Gate actual
PASS: `BRIDGES_V2_19_OF_19`, `ROUTER_RUNTIME_TESTED`, `SECRET_RESOLUTION_FAIL_CLOSED_UNIT_TEST`.
PENDING runtime credential: `GITHUB_ACCESS_VERIFIED`, `HF_ACCESS_VERIFIED`, `MCP_BOUNDARY_VERIFIED`, `MEMORY_BOUNDARY_VERIFIED`, `CONNECTIVITY_GLOBAL_E2E_PASS`.

### Recuperación
Retomar en `GITHUB_RUNTIME_CREDENTIAL_VALIDATION`. Ejecutar sólo si el runtime donde corre Router ve una de las refs autorizadas; nunca intentar leer valores desde GitHub Secrets API. Después: GitHub probe -> HF probe -> MCP boundary -> memory read-back -> global E2E -> sync final. Cualquier ausencia de secret o scope queda FLAG/PENDING, nunca PASS falso.

### Evidencia documental RIU-0064
STATE commit `9db5cec9574c1e3c70f1509347612ea24876087c`; CHECKPOINT `605dc13491c523e26b1b8d5178771b98f29c8f2b`; PLAN `64c0aeda36d06db8cbea8e40d0b9a8adfbf1c812`; Crazy Wall `00cd6cf1d196bc20007d51f0decb7611f51d3946`.
