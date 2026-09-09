# BITÁCORA CRAZY WALL — ROUTER INTELIGENTE UNIVERSAL

**Contrato:** `tel.workflow/v3`
**Modo:** `FAIL_CLOSED_LOOP`

## RIU-0001 — BASELINE
Método de trabajo replicado desde UI YAIWES sin copiar su arquitectura funcional.

## RIU-0002 — COMPONENTES OPEN SOURCE
Componentes centralizados y movidos a `router inteligente universal/Componente open soure router inteligente universal/`.

## RIU-0003 — ÍNDICE / HANDOFF
Índice + Handoff C01-C23 con regla `presencia != integración`.

## RIU-0004 — PLAN 3 PASOS
1. Componentes + auditoría LLM/HF/FastAPI.
2. Cableado + poda + faltantes + filtro LLM.
3. Test HF + GitHub + API + agentes.

## RIU-0005 — HF REUSE / GAP
Bridge HF auditado; owner público HF COUNT 0; privados/endpoints quedan `GAP-HF-CATALOG-001` no bloqueante; prohibido inventar `model_id`.

## RIU-0006..0020 — P02 CIERRES PREVIOS
Gate/conectores v6/registry/validator/schema/RedUniversal y PATCH C15 v1.5→v2.0 verificados; último HF Job C15 `6aa16ff732d5d0c22c5b0912`: `5 passed in 0.09s`.

## RIU-0021 — P02 AUDIT R-004 BACKUP / RESPALDO
Handoff declara C19/R-004 `EXISTING_COMPLETE → REUSE`, pero la búsqueda inicial no recuperó un `.py` físico; se abrió `GAP-R004-SOURCE-001` y no se generó sustituto.

## RIU-0022 — P02 AUDIT C03 CONFIG DONOR
Handoff declara C03 `Config inmutable` como MISSING y ordena `env única fuente de configuración`. Se inspeccionó primero el donor físico local `router inteligente universal/Componente open soure router inteligente universal/pydantic-settings/`. README blob `84c893ab07d3282555622f69cee358686ba4ea99`; `pyproject.toml` blob `21c3e4780e6da923cccf8435498930f4d9e1bece`; upstream declarado `https://github.com/pydantic/pydantic-settings`; licencia MIT; capacidad `Settings management using Pydantic`, Pydantic v2 y `python-dotenv` demostrados. Se creó evidencia `router inteligente universal/integration/audits/C03-CONFIG-DONOR-AUDIT.md`, commit `fa787fe101858ecd2ddf02e1f9ff25238a2148ef`. Decisión `ADAPT_CANDIDATE`, no integrado: no existe contrato recuperado de nombres env/campos, requeridos, defaults o perfiles, por lo que se abre `GAP-C03-CONTRACT-001` y no se inventa `settings.py`.

## RIU-0023 — STRATEGYDELTA R-004: FUENTE PDF LOCALIZADA
La refutación del GAP R-004 cambió materialmente de estrategia: en vez de buscar únicamente rutas `.py`, se auditó el árbol documental canónico del lote 1. Se encontró `Documentos proyectos router inteligente universal/lote 1 documentos proyecto/respaldo.py.pdf`, blob `2ee8d937493d1923b2c1e5d6cc294a1513df3c91`, tamaño 27576 bytes. Por tanto queda refutada la afirmación anterior `source físico no recuperado`. El runtime intentó leer el blob como UTF-8 y falló con `UnicodeDecodeError`, y la ruta web/raw no pudo materializar el PDF en esta ejecución. Decisión fail-closed: `SOURCE_PDF_FOUND / EXTRACTION_PENDING`; no REUSE, no GENERATE y no producción hasta extraer el código del PDF, comprobar ownership/contenido, comparar con el contrato C19 y ejecutar test fijo. Progreso permanece 93%.

## COUNCIL12 / CROSS-CHECK / CODA / VERIFY_FINAL RIU-0023
PASS de auditoría forense, no de código: Handoff C19/R-004 ↔ árbol del lote 1 ↔ blob PDF coinciden en identidad `respaldo`; la evidencia corrige el GAP sin transformar presencia documental en integración. CODA mantiene `REUSE > PATCH > ADAPT > GENERATE`; verify_final prohíbe marcar C19 PASS hasta extracción/read-back/test.

## 3 REFUTACIONES
1. PDF `respaldo.py.pdf` presente ≠ código `respaldo.py` recuperado.
2. Blob PDF identificado ≠ ownership/contenido ejecutable verificado.
3. StrategyDelta forense PASS ≠ R-004 REUSE PASS ≠ Paso 2 cerrado ≠ E2E Paso 3.

## NEXT
Cola 1×1: recuperar/extractar `respaldo.py.pdf` por una vía binaria autorizada; verificar contenido y ownership, después solo si coincide materializar `infrastructure/backup/respaldo.py` por REUSE exacto → read-back/blob → test → persistir. C03, HF catalog y filtro LLM permanecen fail-closed hasta nueva evidencia.