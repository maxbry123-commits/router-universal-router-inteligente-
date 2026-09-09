# RECOVERY PATCH — ROUTER INTELIGENTE UNIVERSAL

Contrato: `tel.workflow/v3` · modo `FAIL_CLOSED_LOOP`.

## Estado válido
- Plan limitado a 3 pasos.
- Paso 1: componentes centralizados; owner público HF 0; privados/endpoints FLAG no bloqueante.
- Paso 2 ACTIVE: Gate/conectores/registry + validator/schema/RedUniversal recuperados y verificados.
- C15 `red/enchufe_gate.py` preserva firma pública v1.5 y delega fichas v2 a `domain/schemas/enchufe_v2.py` + `enchufe/validator_v2.py`; HF Job `6aa16ff732d5d0c22c5b0912` = `5 passed in 0.09s`.
- Filtro de comportamiento LLM continúa fail-closed por ausencia de policy standalone explícita.
- R-004 permanece bloqueado: fuente Python exacta no materializada; no regenerar desde PDF/contrato.
- C03 donor `pydantic-settings` permanece `ADAPT_CANDIDATE`; contrato de campos/env/defaults/perfiles ausente.
- C01 donor FastAPI auditado en `router inteligente universal/integration/audits/C01-FASTAPI-DONOR-AUDIT.md`, commit `c8d297ed1046445c74190d6ba51bc1a39307462d`; `pyproject.toml` blob `06c82344a7010eefaf98f567468dea8be5a5ae10`, MIT, upstream `https://github.com/fastapi/fastapi`.
- C01 queda `ADAPT_CANDIDATE`, no integrado: falta contrato exacto Paneles 1–5 para rutas/métodos/schemas/auth/error/WS.
- Paso 3 pendiente.

## Boot de recuperación
1. Leer STATE/CHECKPOINT/PLAN/BITACORA/README arquitectura/Handoff.
2. Verificar HEAD/blobs y último delta cerrado.
3. Mantener todos los GAP fail-closed hasta nueva evidencia contractual/materializable.
4. Continuar una tarea P02 independiente solo si source/contrato son suficientes; aplicar `REUSE > PATCH > ADAPT > GENERATE`.
5. Después de cualquier delta: read-back/blob + test/log cuando corresponda + persistencia.
6. C01 solo generar/adaptar API cuando exista contrato exacto; C03 solo ADAPT con campos/env; filtro LLM solo con policy standalone explícita.

## GAPs activos
- `GAP-HF-CATALOG-001`: no inventar modelos.
- `GAP-BEHAVIOR-CONTRACT-001`: schema/validator/perfiles no equivalen a policy standalone.
- `GAP-R004-EXTRACTION-001`: PDF demostrado ≠ fuente Python exacta recuperada.
- `GAP-C03-CONTRACT-001`: donor válido ≠ contrato del Router.
- `GAP-C01-API-CONTRACT-001`: FastAPI disponible ≠ contrato Paneles 1–5 recuperado.

## Refutaciones último delta
1. FastAPI presente y MIT ≠ C01 integrado.
2. Soporte REST/WS del donor ≠ rutas/schemas/auth/error del Router.
3. Auditoría C01 PASS ≠ C01 runtime PASS ≠ Paso 2 cerrado ≠ E2E Paso 3.
