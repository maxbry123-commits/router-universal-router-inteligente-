# RECOVERY PATCH — ROUTER INTELIGENTE UNIVERSAL

Contrato: `tel.workflow/v3` · modo `FAIL_CLOSED_LOOP`.

## Estado válido
- Plan limitado a 3 pasos.
- Paso 1: componentes centralizados; owner público HF 0; privados/endpoints FLAG no bloqueante.
- Paso 2 ACTIVE: Gate/conectores/registry + validator/schema/RedUniversal recuperados y verificados.
- C10 `engine/resilience.py` materializado desde contrato explícito y verificado; HF Job `6aa1ae8221047bf1b03707ff` = `5 passed in 0.10s`.
- RIU-0027 auditó C11 Semantic Cache sin generar producción; `GAP-C11-SEMANTIC-CACHE-CONTRACT-001` OPEN.
- RIU-0028 auditó C12 Cost Optimizer sin generar producción. LiteLLM local (`litellm` 1.100.0, MIT, upstream `https://github.com/BerriAI/litellm`) es donor candidato, pero el Router no define scopes de presupuesto, hard/soft limits, intervalos, normalización monetaria, autoridad de precios, fallback/rollover, ownership agente/tarea ni boundary Enchufe.
- C12 queda `ADAPT_CANDIDATE / AUDIT_ONLY`; `GAP-C12-COST-POLICY-CONTRACT-001` OPEN.
- Filtro de comportamiento LLM continúa fail-closed por ausencia de policy standalone explícita.
- R-004 permanece bloqueado: fuente Python exacta no materializada.
- C03 Config permanece bloqueado por contrato incompleto.
- C01 API permanece bloqueado por contrato Paneles 1–5 incompleto.
- Paso 3 pendiente.

## Boot de recuperación
1. Leer STATE/CHECKPOINT/PLAN/BITACORA/README arquitectura/Handoff y mantener `tel.workflow/v3`.
2. Verificar último delta cerrado: RIU-0028 / C12 audit-only, commit `d34b0ff83e81537d0d1da9ad26db327a0ea552d8`.
3. Mantener todos los GAP fail-closed hasta nueva evidencia contractual/materializable.
4. Continuar una tarea P02 independiente solo si source/contrato son suficientes; `REUSE > PATCH > ADAPT > GENERATE`.
5. Después de cualquier delta: read-back/blob + test/log cuando corresponda + persistencia.
6. No generar C11 ni C12 desde capacidad genérica de donors.

## GAPs activos
- `GAP-HF-CATALOG-001`: no inventar modelos.
- `GAP-BEHAVIOR-CONTRACT-001`: policy standalone ausente.
- `GAP-R004-EXTRACTION-001`: fuente Python exacta no recuperada.
- `GAP-C03-CONTRACT-001`: donor válido ≠ contrato del Router.
- `GAP-C01-API-CONTRACT-001`: FastAPI disponible ≠ contrato Paneles 1–5.
- `GAP-C11-SEMANTIC-CACHE-CONTRACT-001`: donors presentes ≠ contrato semantic-cache.
- `GAP-C12-COST-POLICY-CONTRACT-001`: LiteLLM/cost metadata ≠ budget policy del Router.

## Council12 / 3 refutaciones / cross-check / CODA RIU-0028
Council12 PASS para auditoría; runtime test N/A porque no hubo código de producción. Refutaciones: LiteLLM presente ≠ C12 integrado; cost metadata ≠ budget policy Router; inferir límites/intervalos/autoridad de precios violaría FAIL_CLOSED_LOOP. Cross-check PASS. CODA `PASS_SAFE_AUDIT_DELTA`. `verify_final=PASS_C12_AUDIT_ONLY_CONTRACT_GAP_RECORDED`.
