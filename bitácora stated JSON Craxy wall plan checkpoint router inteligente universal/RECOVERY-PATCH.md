# RECOVERY PATCH — ROUTER INTELIGENTE UNIVERSAL

Contrato: `tel.workflow/v3` · modo `FAIL_CLOSED_LOOP`.

## Estado válido
- Plan limitado a 3 pasos.
- Paso 1: componentes centralizados; HF Jobs compute real verificado; catálogo privado todavía no demostrado.
- RIU-0031: identidad HF conectada `COMAND-CENTER-1`; OAuth con scopes `jobs/openid/profile/read-mcp/read-repos`; Job `6aa1d38621047bf1b0370f3f` completó auditoría mínima y reportó `public_model_count=0`, `hf_token_present=false`.
- Auditoría: `router inteligente universal/integration/huggingface/RIU-0031-HF-CATALOG-TOKEN-AUDIT.md`, commit `505d54c23120f96cec42dde5c26cd001c20092b9`.
- Intento previo `6aa1d3125527934177ebe373` cancelado por clone grande ineficiente; no PASS.
- Paso 2 ACTIVE; filtro LLM fail-closed; Paso 3 PENDING.

## Boot de recuperación
1. Leer STATE/CHECKPOINT/PLAN/BITACORA/README arquitectura/Handoff; mantener `tel.workflow/v3`.
2. Último delta cerrado: RIU-0031 / HF catalog-token boundary audit.
3. Mantener `GAP-HF-CATALOG-001`: público 0 ≠ privado 0; Jobs no recibió `HF_TOKEN` implícito.
4. Reintentar privados solo mediante credencial explícita segura; nunca hardcode/log tokens.
5. Continuar una tarea P02 independiente solo con source/contrato suficiente; `REUSE > PATCH > ADAPT > GENERATE`.
6. Tras cada delta: read-back/blob + test/log + persistencia; no iniciar Paso 3 por un audit PASS.

## GAPs activos
`GAP-HF-CATALOG-001`, `GAP-BEHAVIOR-CONTRACT-001`, `GAP-R004-EXTRACTION-001`, `GAP-C03-CONTRACT-001`, `GAP-C01-API-CONTRACT-001`, `GAP-C11-SEMANTIC-CACHE-CONTRACT-001`, `GAP-C12-COST-POLICY-CONTRACT-001`, `GAP-C13-SANDBOX-CONTRACT-001`.

## RIU-0031 verification
Council12 PASS. Refutaciones: (1) público 0 ≠ privado 0; (2) OAuth conectado ≠ token inyectado en Jobs; (3) Job success ≠ FastAPI/model adapter autorizado. Cross-check PASS. CODA `PASS_HF_CATALOG_BOUNDARY_AUDIT_GAP_REFINED`. `verify_final=PASS_AUDIT_ONLY_NO_MODEL_CLAIM`.
