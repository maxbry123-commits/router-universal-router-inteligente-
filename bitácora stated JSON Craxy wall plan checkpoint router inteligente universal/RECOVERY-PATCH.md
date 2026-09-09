# RECOVERY PATCH — ROUTER INTELIGENTE UNIVERSAL

Contrato: `tel.workflow/v3` · modo `FAIL_CLOSED_LOOP`.

## Estado válido
- Plan limitado a 3 pasos.
- Paso 1: componentes centralizados; owner público HF 0; privados/endpoints FLAG no bloqueante.
- Paso 2 ACTIVE: Gate/conectores/registry + validator/schema/RedUniversal recuperados y verificados.
- C15 `red/enchufe_gate.py` preserva firma pública v1.5 y delega fichas v2 a `domain/schemas/enchufe_v2.py` + `enchufe/validator_v2.py`; HF Job `6aa16ff732d5d0c22c5b0912` = `5 passed in 0.09s`.
- Filtro de comportamiento LLM continúa fail-closed por ausencia de policy standalone explícita.
- R-004 continúa fail-closed: Handoff lo declara existente, pero source/ownership físico no fue recuperado.
- C03 auditado con donor local `pydantic-settings`: README blob `84c893ab07d3282555622f69cee358686ba4ea99`, pyproject blob `21c3e4780e6da923cccf8435498930f4d9e1bece`, licencia MIT, upstream declarado `https://github.com/pydantic/pydantic-settings`.
- Decisión C03: `ADAPT_CANDIDATE`, no integrado; la evidencia disponible no define nombres de env/campos, requeridos, defaults ni perfiles del Router.
- Se abre `GAP-C03-CONTRACT-001`; auditoría física en commit `fa787fe101858ecd2ddf02e1f9ff25238a2148ef`.
- Paso 3 pendiente.

## Boot de recuperación
1. Leer STATE/CHECKPOINT/PLAN/BITACORA/README arquitectura/Handoff.
2. Verificar HEAD/blobs y último delta cerrado.
3. C03: recuperar contrato de campos/env desde evidencia del proyecto antes de escribir producción.
4. Si aparece contrato C03: ADAPT mínimo sobre donor local → read-back/blob → test fijo → persistir.
5. Si no aparece: mantener GAP y pasar solo a una tarea P02 independiente segura respaldada por arquitectura.
6. R-004 solo REUSE con source+ownership canónico; filtro LLM solo con policy standalone explícita.

## GAP-HF-CATALOG-001
No inventar modelos. Reintentar privados/endpoints solo con nueva evidencia consumible.

## GAP-BEHAVIOR-CONTRACT-001
Schema/validator/perfiles no equivalen a una policy standalone allow/deny.

## GAP-R004-SOURCE-001
Fuente/ownership no demostrados; no REUSE ni GENERATE por inferencia.

## GAP-C03-CONTRACT-001
Donor válido ≠ contrato del Router. No inventar nombres de secretos/endpoints/timeouts/defaults/perfiles.

## Refutaciones
1. `pydantic-settings` presente y apto ≠ C03 integrado.
2. `env única fuente` ≠ contrato suficiente para inventar campos.
3. Auditoría C03 cerrada ≠ código C03 verificado ≠ Paso 2 cerrado ≠ E2E Paso 3.
