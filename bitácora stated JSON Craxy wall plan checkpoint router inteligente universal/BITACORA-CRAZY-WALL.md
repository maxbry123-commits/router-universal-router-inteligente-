# BITÁCORA CRAZY WALL — ROUTER INTELIGENTE UNIVERSAL

**Contrato:** `tel.workflow/v3`
**Modo:** `FAIL_CLOSED_LOOP`

## RIU-0001..0029 — TRAZABILIDAD PREVIA
Baseline, componentes, Handoff, plan 3 pasos, HF, Gate/conectores v6/registry/validator/schema/RedUniversal, C10 y auditorías C11/C12/C13 quedan preservados por STATE/CHECKPOINT/commits anteriores.

## RIU-0030 — P01 HUGGING FACE JOBS COMO CÓMPUTO REAL
INPUT literal: resolver primero HF; investigar documentación oficial; usar Jobs como cómputo real y CPU Upgrade/32 GB cuando corresponda; Router→HF Job→resultado→GitHub.

Investigación oficial previa: https://huggingface.co/docs/hub/en/jobs ; https://huggingface.co/docs/huggingface_hub/guides/jobs ; https://huggingface.co/docs/hub/en/jobs-configuration ; https://huggingface.co/docs/hub/jobs-pricing . La documentación confirma `cpu-upgrade` = 8 vCPU/32 GB.

Primer intento fue rechazado por sintaxis shell del wrapper. StrategyDelta materialmente distinto: argv literal sin shell implícito, imagen `python:3.12`, flavor `cpu-upgrade`, clonando el repo GitHub y auditando STATE + árbol de `router inteligente universal/` dentro del Job.

HF Job `6aa1c5fd21047bf1b0370d4d` → `success`; URL https://huggingface.co/jobs/COMAND-CENTER-1/6aa1c5fd21047bf1b0370d4d . Auditoría persistida en `router inteligente universal/integration/huggingface/RIU-0030-HF-JOBS-COMPUTE-AUDIT.md`, commit `0acb4f31a0ff784bae7037b62bac36074e15850f`.

Decisión: HF Jobs queda verificado como cómputo real del proyecto; `GAP-HF-CATALOG-001` permanece OPEN porque éxito de Jobs no confirma `model_id` privados/endpoints.

Council12 PASS. 3 refutaciones: Job success ≠ catálogo/model_id; auditoría repo en Jobs ≠ E2E API/agentes; compute disponible ≠ autorización para inventar contratos FastAPI/behavior policy. Cross-check PASS. CODA `PASS_HF_JOBS_REAL_COMPUTE_DELTA`. `verify_final=PASS_HF_JOBS_COMPUTE_REAL_NO_CATALOG_CLAIM`.

## NEXT
Paso 2 continúa ACTIVE. Cola 1×1: siguiente componente P02 independiente con source/contrato suficiente; mantener todos los GAPs fail-closed. Paso 3 sigue PENDING.
