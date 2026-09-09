# RECOVERY PATCH — ROUTER INTELIGENTE UNIVERSAL

Contrato: `tel.workflow/v3` · modo `FAIL_CLOSED_LOOP`.

## Estado válido
- Plan limitado a 3 pasos.
- Paso 1: componentes centralizados; owner público HF 0; privados/endpoints FLAG no bloqueante.
- Paso 2 ACTIVE: Gate/conectores/registry + validator/schema/RedUniversal recuperados y verificados.
- C10 `engine/resilience.py` materializado desde contrato explícito y verificado; HF Job `6aa1ae8221047bf1b03707ff` = `5 passed in 0.10s`.
- RIU-0027 C11 y RIU-0028 C12 quedan AUDIT_ONLY por contratos específicos incompletos.
- RIU-0029 auditó C13 CodeSandbox dual sin generar producción. Donor local `router inteligente universal/Componente open soure router inteligente universal/docker-py/`; `pyproject.toml` declara paquete `docker`, licencia Apache-2.0 y upstream `https://github.com/docker/docker-py`; versión dinámica, no inferida.
- C13 queda `ADAPT_CANDIDATE / AUDIT_ONLY`; `GAP-C13-SANDBOX-CONTRACT-001` OPEN porque faltan allowlists, imagen/pinning, límites CPU/mem/PIDs/disco, red/filesystem, timeout/cancel, IO/artefactos, secretos, paridad Docker↔subprocess, schema de resultado y boundary Enchufe.
- Filtro de comportamiento LLM continúa fail-closed por ausencia de policy standalone explícita.
- R-004, C03 y C01 continúan bloqueados por sus GAPs registrados.
- Paso 3 pendiente.

## Boot de recuperación
1. Leer STATE/CHECKPOINT/PLAN/BITACORA/README arquitectura/Handoff y mantener `tel.workflow/v3`.
2. Verificar último delta cerrado: RIU-0029 / C13 audit-only, commit `b761958f1532345e97ec82e747d38cd9b596ec0c`.
3. Mantener todos los GAP fail-closed hasta nueva evidencia contractual/materializable.
4. Continuar una tarea P02 independiente solo si source/contrato son suficientes; `REUSE > PATCH > ADAPT > GENERATE`.
5. Después de cualquier delta: read-back/blob + test/log cuando corresponda + persistencia.
6. No generar C11/C12/C13 desde capacidad genérica de donors.

## GAPs activos
- `GAP-HF-CATALOG-001`: no inventar modelos.
- `GAP-BEHAVIOR-CONTRACT-001`: policy standalone ausente.
- `GAP-R004-EXTRACTION-001`: fuente Python exacta no recuperada.
- `GAP-C03-CONTRACT-001`: donor válido ≠ contrato del Router.
- `GAP-C01-API-CONTRACT-001`: FastAPI disponible ≠ contrato Paneles 1–5.
- `GAP-C11-SEMANTIC-CACHE-CONTRACT-001`: donors presentes ≠ contrato semantic-cache.
- `GAP-C12-COST-POLICY-CONTRACT-001`: LiteLLM/cost metadata ≠ budget policy del Router.
- `GAP-C13-SANDBOX-CONTRACT-001`: docker-py disponible ≠ contrato de aislamiento/ejecución/paridad del Router.

## Council12 / 3 refutaciones / cross-check / CODA RIU-0029
Council12 PASS para auditoría; runtime test N/A porque no hubo código de producción. Refutaciones: docker-py presente ≠ C13 integrado; Docker Engine API ≠ policy de aislamiento/recursos Router; fallback subprocess sin contrato de paridad violaría FAIL_CLOSED_LOOP. Cross-check PASS. CODA `PASS_SAFE_AUDIT_DELTA`. `verify_final=PASS_C13_AUDIT_ONLY_CONTRACT_GAP_RECORDED`.
