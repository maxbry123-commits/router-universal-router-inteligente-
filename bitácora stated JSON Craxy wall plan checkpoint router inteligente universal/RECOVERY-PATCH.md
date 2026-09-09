# RECOVERY PATCH — ROUTER INTELIGENTE UNIVERSAL

Contrato: `tel.workflow/v3` · modo `FAIL_CLOSED_LOOP`.

## Estado válido
- Plan limitado a 3 pasos.
- Paso 1: componentes centralizados; owner público HF 0; privados/endpoints FLAG no bloqueante.
- Paso 2 ACTIVE: Gate/conectores/registry + validator/schema/RedUniversal recuperados y verificados.
- C15 `red/enchufe_gate.py` preserva firma pública v1.5 y delega fichas v2 a `domain/schemas/enchufe_v2.py` + `enchufe/validator_v2.py`; HF Job `6aa16ff732d5d0c22c5b0912` = `5 passed in 0.09s`.
- Filtro de comportamiento LLM continúa fail-closed por ausencia de policy standalone explícita.
- R-004: PDF canónico `Documentos proyectos router inteligente universal/lote 1 documentos proyecto/respaldo.py.pdf`, blob `2ee8d937493d1923b2c1e5d6cc294a1513df3c91`, origen commit `7db4e349ff3ea22be5f1b8c10a1efc46b73418aa`.
- StrategyDelta actual: `router inteligente universal/integration/audits/R004-PDF-EXTRACTION-AUDIT.md`, commit `f41db4710a7af645288fe1b1339fa5aba6cc894f`. Base64 confirma PDF; lectura blob UTF-8 falla correctamente por binario; raw/web no materializa; red del runtime falló DNS. No se reconstruyó fuente Python exacta y no existe R-004 PASS.
- C03 auditado con donor local `pydantic-settings`: README blob `84c893ab07d3282555622f69cee358686ba4ea99`, pyproject blob `21c3e4780e6da923cccf8435498930f4d9e1bece`, licencia MIT. Estado `ADAPT_CANDIDATE`, no integrado.
- Paso 3 pendiente.

## Boot de recuperación
1. Leer STATE/CHECKPOINT/PLAN/BITACORA/README arquitectura/Handoff.
2. Verificar HEAD/blobs y último delta cerrado.
3. Mantener R-004 fail-closed hasta disponer de una vía binaria autorizada que materialice el PDF exacto.
4. Continuar una tarea P02 independiente solo si source/contrato son suficientes; aplicar `REUSE > PATCH > ADAPT > GENERATE`.
5. Después de cualquier delta: read-back/blob + test/log cuando corresponda + persistencia.
6. C03 solo ADAPT cuando exista contrato de campos/env; filtro LLM solo con policy standalone explícita.

## GAP-HF-CATALOG-001
No inventar modelos. Reintentar privados/endpoints solo con nueva evidencia consumible.

## GAP-BEHAVIOR-CONTRACT-001
Schema/validator/perfiles no equivalen a una policy standalone allow/deny.

## GAP-R004-EXTRACTION-001
PDF identity/origin/behavior contract demostrados; fuente Python exacta no materializada. No generar sustituto desde descripciones.

## GAP-C03-CONTRACT-001
Donor válido ≠ contrato del Router. No inventar nombres de secretos/endpoints/timeouts/defaults/perfiles.

## Refutaciones
1. PDF/base64 demostrado ≠ `respaldo.py` exacto recuperado.
2. Contrato `empaquetar/verificar` ≠ permiso para regenerar implementación.
3. Auditoría R-004 PASS ≠ R-004 runtime PASS ≠ Paso 2 cerrado ≠ E2E Paso 3.
