# RECOVERY PATCH — ROUTER INTELIGENTE UNIVERSAL

Contrato: `tel.workflow/v3` · modo `FAIL_CLOSED_LOOP`.

## Estado válido
- Plan limitado a 3 pasos.
- Paso 1: componentes centralizados; owner público HF 0; privados/endpoints FLAG no bloqueante.
- Paso 2 ACTIVE: Gate/conectores/registry + validator/schema/RedUniversal recuperados y verificados.
- C15 `red/enchufe_gate.py` preserva firma pública v1.5 y delega fichas v2 a `domain/schemas/enchufe_v2.py` + `enchufe/validator_v2.py`; HF Job `6aa16ff732d5d0c22c5b0912` = `5 passed in 0.09s`.
- Filtro de comportamiento LLM continúa fail-closed por ausencia de policy standalone explícita.
- R-004: StrategyDelta materialmente distinto localizó `Documentos proyectos router inteligente universal/lote 1 documentos proyecto/respaldo.py.pdf`, blob `2ee8d937493d1923b2c1e5d6cc294a1513df3c91`, tamaño 27576 bytes. La ausencia total de fuente queda refutada; el estado correcto es `SOURCE_PDF_FOUND / EXTRACTION_PENDING`.
- La lectura UTF-8 del blob PDF falla por binario y la ruta raw/web no pudo materializarse en esta ejecución; no se reclama contenido/ownership ni REUSE.
- C03 auditado con donor local `pydantic-settings`: README blob `84c893ab07d3282555622f69cee358686ba4ea99`, pyproject blob `21c3e4780e6da923cccf8435498930f4d9e1bece`, licencia MIT.
- Decisión C03: `ADAPT_CANDIDATE`, no integrado; campos/env/defaults/perfiles sin contrato recuperado.
- Paso 3 pendiente.

## Boot de recuperación
1. Leer STATE/CHECKPOINT/PLAN/BITACORA/README arquitectura/Handoff.
2. Verificar HEAD/blobs y último delta cerrado.
3. R-004: recuperar el binario PDF por vía autorizada y extraer/verificar código+ownership.
4. Solo si coincide con C19/R-004: REUSE exacto a `infrastructure/backup/respaldo.py` → read-back/blob → test fijo → persistir.
5. Si extracción no es posible: mantener `GAP-R004-EXTRACTION-001` y pasar solo a una tarea P02 independiente segura.
6. C03 solo ADAPT cuando exista contrato de campos/env; filtro LLM solo con policy standalone explícita.

## GAP-HF-CATALOG-001
No inventar modelos. Reintentar privados/endpoints solo con nueva evidencia consumible.

## GAP-BEHAVIOR-CONTRACT-001
Schema/validator/perfiles no equivalen a una policy standalone allow/deny.

## GAP-R004-EXTRACTION-001
PDF canónico localizado, pero contenido/ownership ejecutable aún no extraído ni verificado. Presencia PDF ≠ REUSE.

## GAP-C03-CONTRACT-001
Donor válido ≠ contrato del Router. No inventar nombres de secretos/endpoints/timeouts/defaults/perfiles.

## Refutaciones
1. `respaldo.py.pdf` presente ≠ `respaldo.py` recuperado.
2. Blob PDF demostrado ≠ código/ownership verificados.
3. Auditoría forense R-004 PASS ≠ R-004 runtime PASS ≠ Paso 2 cerrado ≠ E2E Paso 3.
