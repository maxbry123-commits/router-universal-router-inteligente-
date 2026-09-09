# BITÁCORA CRAZY WALL — ROUTER INTELIGENTE UNIVERSAL

**Contrato:** `tel.workflow/v3`
**Modo:** `FAIL_CLOSED_LOOP`

## RIU-0001..0030 — TRAZABILIDAD PREVIA
Baseline, componentes, Handoff, plan 3 pasos, HF, Gate/conectores v6/registry/validator/schema/RedUniversal, C10, auditorías C11/C12/C13 y HF Jobs compute real quedan preservados por STATE/CHECKPOINT/commits anteriores.

## RIU-0031 — HF CATALOG/TOKEN BOUNDARY
INPUT literal: resolver primero Hugging Face; investigar oficial/comunidad; Jobs como cómputo real; auditar LLM reales sin inventar model_id; cola 1×1.

Investigación oficial: https://huggingface.co/docs/hub/en/jobs ; https://huggingface.co/docs/hub/en/jobs-configuration ; https://huggingface.co/docs/huggingface_hub/en/guides/jobs . Jobs documenta `JOB_ID/ACCELERATOR/CPU_CORES/MEMORY` como built-ins y los secretos, incluido `HF_TOKEN`, como entrada explícita.

Identidad conectada: `COMAND-CENTER-1`, OAuth autenticado con scopes `jobs/openid/profile/read-mcp/read-repos`.

Attempt A: Job `6aa1d3125527934177ebe373` inició clone del repo grande; quedó consumiendo cómputo sin producir la evidencia objetivo y fue cancelado. No PASS.

StrategyDelta B materialmente distinto: eliminar clone y ejecutar sólo enumeración pública + boundary de token. Job `6aa1d38621047bf1b0370f3f` → COMPLETED, `cpu-basic`, 2 CPU/16.0G observados, `public_model_count=0`, `public_model_ids=[]`, `hf_token_present=false`. URL https://huggingface.co/jobs/COMAND-CENTER-1/6aa1d38621047bf1b0370f3f .

Decisión: `GAP-HF-CATALOG-001` sigue OPEN y queda refinado a boundary de credencial privada. Público 0 no demuestra privado 0. No se creó ningún mapping `model_id→especialidad→adapter→FastAPI` sin modelo confirmado.

Auditoría: `router inteligente universal/integration/huggingface/RIU-0031-HF-CATALOG-TOKEN-AUDIT.md`, commit `505d54c23120f96cec42dde5c26cd001c20092b9`.

Council12 PASS. Refutaciones: público 0 ≠ privado 0; OAuth conectado ≠ token automático en Job; Job success ≠ permiso para inventar FastAPI/adapter. Cross-check PASS. CODA `PASS_HF_CATALOG_BOUNDARY_AUDIT_GAP_REFINED`. `verify_final=PASS_AUDIT_ONLY_NO_MODEL_CLAIM`.

## NEXT
Paso 2 sigue ACTIVE. Cola 1×1: componente P02 independiente con contrato suficiente. Reintentar catálogo privado sólo con ruta segura explícita de credencial/evidencia. Paso 3 sigue PENDING.
