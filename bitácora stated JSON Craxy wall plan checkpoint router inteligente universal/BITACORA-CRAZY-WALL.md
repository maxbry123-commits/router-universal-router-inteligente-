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
Handoff declara C03 `Config inmutable` como MISSING y ordena `env única fuente de configuración`. Donor local `pydantic-settings` confirmado MIT/Pydantic v2; evidencia `router inteligente universal/integration/audits/C03-CONFIG-DONOR-AUDIT.md`, commit `fa787fe101858ecd2ddf02e1f9ff25238a2148ef`. Decisión `ADAPT_CANDIDATE`, no integrado; `GAP-C03-CONTRACT-001` por campos/env/defaults/perfiles no definidos.

## RIU-0023 — STRATEGYDELTA R-004: FUENTE PDF LOCALIZADA
Se encontró `Documentos proyectos router inteligente universal/lote 1 documentos proyecto/respaldo.py.pdf`, blob `2ee8d937493d1923b2c1e5d6cc294a1513df3c91`, tamaño 27576 bytes. Estado `SOURCE_PDF_FOUND / EXTRACTION_PENDING`; no REUSE, no GENERATE hasta extraer código, comprobar ownership/contenido y ejecutar test fijo.

## RIU-0024 — STRATEGYDELTA R-004: IDENTIDAD/ORIGEN VERIFICADOS, MATERIALIZACIÓN BLOQUEADA
Cola 1×1 ejecutada sobre el mismo R-004 sin escribir producción. Se verificó que el PDF fue añadido por commit `7db4e349ff3ea22be5f1b8c10a1efc46b73418aa`; el historial/arquitectura del commit confirma C19/R-004, `empaquetar()` + `verificar()`, ZIP + manifiesto SHA-256 y tests de round-trip/archivo roto. GitHub `fetch_file` base64 confirmó cabecera PDF; `fetch_blob` UTF-8 falló con `UnicodeDecodeError` (esperado para binario); raw/web no materializó y el runtime local falló DNS. Evidencia persistida en `router inteligente universal/integration/audits/R004-PDF-EXTRACTION-AUDIT.md`, commit `f41db4710a7af645288fe1b1339fa5aba6cc894f`. Decisión: `GAP-R004-EXTRACTION-001` permanece OPEN; contrato de comportamiento no autoriza regenerar la implementación.

## COUNCIL12 / CROSS-CHECK / CODA / VERIFY_FINAL RIU-0024
PASS de auditoría, no de runtime. Council12: objetivo/INPUT/destino/estado/evidencia/arquitectura/concurrencia PASS; reusable `FOUND_PDF/BLOCKED_EXTRACTION`; dependencia binaria BLOCKED; test de runtime `NOT_RUN_BY_DESIGN`; cierre `PASS_FOR_AUDIT_ONLY`. Cross-check Handoff↔PLAN↔CHECKPOINT↔RECOVERY↔historial Git coincide. CODA selecciona fail-closed/no-code. `verify_final = PASS_AUDIT_ONLY`.

## 3 REFUTACIONES RIU-0024
1. Base64/cabecera PDF demostrada ≠ fuente Python exacta recuperada.
2. `empaquetar()/verificar()` + SHA-256 ≠ permiso para GENERATE.
3. Auditoría PASS ≠ R-004 runtime PASS ≠ Paso 2 cerrado ≠ E2E Paso 3.

## NEXT
R-004 queda en retry solo cuando exista vía binaria autorizada materializable. Cola 1×1 pasa a auditar un componente P02 independiente con source/contrato suficiente; `REUSE > PATCH > ADAPT > GENERATE`. C03, HF catalog y filtro LLM permanecen fail-closed hasta nueva evidencia.
