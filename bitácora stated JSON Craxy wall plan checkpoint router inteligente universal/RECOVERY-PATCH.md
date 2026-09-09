# RECOVERY PATCH — ROUTER INTELIGENTE UNIVERSAL

Contrato: `tel.workflow/v3` · modo `FAIL_CLOSED_LOOP`.

## Estado válido
- Plan limitado a 3 pasos.
- Paso 1: componentes centralizados; owner público HF 0; privados/endpoints FLAG no bloqueante.
- Paso 2 ACTIVE: Gate/conectores/registry + validator/schema/RedUniversal recuperados y verificados.
- C10 `engine/resilience.py` materializado desde contrato explícito y verificado; HF Job `6aa1ae8221047bf1b03707ff` = `5 passed in 0.10s`.
- RIU-0027 auditó C11 Semantic Cache sin generar producción: `redis-py` está disponible bajo donor root, pero el contrato Router-owned no define keying, embedding/model version, metric/threshold, TTL/invalidation, namespace/privacy, serialization ni boundary Enchufe exacto.
- C11 queda `ADAPT_CANDIDATE / AUDIT_ONLY`; `GAP-C11-SEMANTIC-CACHE-CONTRACT-001` OPEN.
- Filtro de comportamiento LLM continúa fail-closed por ausencia de policy standalone explícita.
- R-004 permanece bloqueado: fuente Python exacta no materializada.
- C03 Config permanece bloqueado por contrato incompleto.
- C01 API permanece bloqueado por contrato Paneles 1–5 incompleto.
- Paso 3 pendiente.

## Boot de recuperación
1. Leer STATE/CHECKPOINT/PLAN/BITACORA/README arquitectura/Handoff y mantener `tel.workflow/v3`.
2. Verificar último delta cerrado: RIU-0027 / C11 audit-only, commit `e03782dcc413efab22399f2df3dc30c6a60a053e`.
3. Mantener todos los GAP fail-closed hasta nueva evidencia contractual/materializable.
4. Continuar una tarea P02 independiente solo si source/contrato son suficientes; `REUSE > PATCH > ADAPT > GENERATE`.
5. Después de cualquier delta: read-back/blob + test/log cuando corresponda + persistencia.
6. No generar C11 desde capacidad genérica de Redis/vector similarity.

## GAPs activos
- `GAP-HF-CATALOG-001`: no inventar modelos.
- `GAP-BEHAVIOR-CONTRACT-001`: policy standalone ausente.
- `GAP-R004-EXTRACTION-001`: fuente Python exacta no recuperada.
- `GAP-C03-CONTRACT-001`: donor válido ≠ contrato del Router.
- `GAP-C01-API-CONTRACT-001`: FastAPI disponible ≠ contrato Paneles 1–5.
- `GAP-C11-SEMANTIC-CACHE-CONTRACT-001`: donors presentes ≠ contrato semantic-cache.

## Council12 / 3 refutaciones / cross-check / CODA RIU-0027
Council12 PASS para auditoría; runtime test N/A porque no hubo código de producción. Refutaciones: donor presente ≠ integrado; Redis/vector capability ≠ policy Router; inferir threshold/TTL/embedding violaría FAIL_CLOSED_LOOP. Cross-check PASS. CODA `PASS_SAFE_AUDIT_DELTA`. `verify_final=PASS_C11_AUDIT_ONLY_CONTRACT_GAP_RECORDED`.
