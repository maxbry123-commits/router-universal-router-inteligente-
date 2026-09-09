# RECOVERY PATCH — ROUTER INTELIGENTE UNIVERSAL

Contrato: `tel.workflow/v3` · modo `FAIL_CLOSED_LOOP`.

## Estado válido
- Plan limitado a 3 pasos.
- Paso 1: componentes centralizados; owner público HF 0; privados/endpoints FLAG no bloqueante.
- RIU-0030 verificó Hugging Face Jobs como cómputo real: Job `6aa1c5fd21047bf1b0370d4d`, flavor `cpu-upgrade` (8 vCPU/32 GB según documentación oficial), resultado `success`, clonando/auditando el repo Router.
- Auditoría RIU-0030: `router inteligente universal/integration/huggingface/RIU-0030-HF-JOBS-COMPUTE-AUDIT.md`, commit `0acb4f31a0ff784bae7037b62bac36074e15850f`.
- Paso 2 ACTIVE: Gate/conectores/registry + validator/schema/RedUniversal recuperados y verificados; C10 verificado; C11/C12/C13 AUDIT_ONLY.
- Filtro de comportamiento LLM continúa fail-closed por ausencia de policy standalone explícita.
- Paso 3 pendiente.

## Boot de recuperación
1. Leer STATE/CHECKPOINT/PLAN/BITACORA/README arquitectura/Handoff y mantener `tel.workflow/v3`.
2. Verificar último delta cerrado: RIU-0030 / HF Jobs compute real.
3. Mantener `GAP-HF-CATALOG-001`: Job success no confirma ningún `model_id` privado.
4. Continuar una tarea P02 independiente solo si source/contrato son suficientes; `REUSE > PATCH > ADAPT > GENERATE`.
5. Después de cualquier delta: read-back/blob + test/log cuando corresponda + persistencia.
6. No iniciar Paso 3 por el solo hecho de que HF Jobs ejecute cómputo real.

## GAPs activos
- `GAP-HF-CATALOG-001`: no inventar modelos.
- `GAP-BEHAVIOR-CONTRACT-001`: policy standalone ausente.
- `GAP-R004-EXTRACTION-001`: fuente Python exacta no recuperada.
- `GAP-C03-CONTRACT-001`: donor válido ≠ contrato del Router.
- `GAP-C01-API-CONTRACT-001`: FastAPI disponible ≠ contrato Paneles 1–5.
- `GAP-C11-SEMANTIC-CACHE-CONTRACT-001`: donors presentes ≠ contrato semantic-cache.
- `GAP-C12-COST-POLICY-CONTRACT-001`: LiteLLM/cost metadata ≠ budget policy del Router.
- `GAP-C13-SANDBOX-CONTRACT-001`: docker-py disponible ≠ contrato de aislamiento/ejecución/paridad del Router.

## RIU-0030 verification
Council12 PASS. Refutaciones: (1) Job success ≠ catálogo/model_id; (2) repo audit en Jobs ≠ E2E API/agentes; (3) compute disponible ≠ autorización para inventar FastAPI/behavior policy. Cross-check PASS. CODA `PASS_HF_JOBS_REAL_COMPUTE_DELTA`. `verify_final=PASS_HF_JOBS_COMPUTE_REAL_NO_CATALOG_CLAIM`.
