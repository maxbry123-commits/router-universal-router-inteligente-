# RIU-0030 — Hugging Face Jobs compute audit

Contrato: `tel.workflow/v3`
Modo: `FAIL_CLOSED_LOOP`
Nodo: Paso 1 / Hugging Face compute real

## INPUT literal aplicado
Resolver primero Hugging Face revisando estado real, permisos y montaje; investigar documentación oficial antes del delta; usar Jobs como cómputo real del proyecto con CPU Upgrade/32 GB cuando corresponda; devolver resultado al flujo Router→HF Job→storage/resultado→GitHub.

## Investigación previa
- Oficial Jobs: https://huggingface.co/docs/hub/en/jobs
- Guía `huggingface_hub` Jobs: https://huggingface.co/docs/huggingface_hub/guides/jobs
- Configuración/hardware: https://huggingface.co/docs/hub/en/jobs-configuration
- Pricing: https://huggingface.co/docs/hub/jobs-pricing

La documentación oficial confirma `cpu-upgrade` = 8 vCPU / 32 GB y Jobs para workloads AI/data con imagen+comando+hardware.

## Ejecución 1×1
Intento inicial: rechazado por sintaxis shell no permitida por el wrapper; no se tomó como fallo del Router.

StrategyDelta materialmente distinto: comando argv literal, imagen `python:3.12`, flavor `cpu-upgrade`, clonando `https://github.com/maxbry123-commits/router-universal-router-inteligente-.git` y auditando `STATE.json` + árbol `router inteligente universal/` dentro del Job.

Job: https://huggingface.co/jobs/COMAND-CENTER-1/6aa1c5fd21047bf1b0370d4d
Job ID: `6aa1c5fd21047bf1b0370d4d`
Resultado de inspección: `success`.
Hardware solicitado: `cpu-upgrade`.

## Verificación / refutación
PASS: Hugging Face Jobs aceptó y ejecutó cómputo real sobre el repo GitHub del Router, no un test sintético aislado.

Refutaciones:
1. Job `success` no demuestra catálogo privado/model_id de HF.
2. Clonar/auditar el repo en Jobs no equivale a E2E Paso 3 con API/agentes.
3. Resultado de inspección exitoso no autoriza inventar contratos FastAPI ni behavior policy LLM.

## Council12 / cross-check / CODA / verify_final
Council12: PASS para este delta de infraestructura/computación.
Cross-check: STATE/PLAN/RECOVERY mantienen Paso 2 ACTIVE y Paso 3 PENDING.
CODA: `PASS_HF_JOBS_REAL_COMPUTE_DELTA`.
verify_final: `PASS_HF_JOBS_COMPUTE_REAL_NO_CATALOG_CLAIM`.

## Decisión
Hugging Face Jobs queda verificado como cómputo real utilizable del proyecto con `cpu-upgrade`; se mantiene abierto `GAP-HF-CATALOG-001` hasta obtener model_id/endpoints privados reales. No se invocó el skill externo porque este delta no descargó ningún componente externo nuevo.
