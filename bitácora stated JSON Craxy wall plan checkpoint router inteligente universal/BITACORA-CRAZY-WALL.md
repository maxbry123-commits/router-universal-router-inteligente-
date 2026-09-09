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
Handoff declara C19/R-004 `EXISTING_COMPLETE → REUSE`, pero no se recuperó `.py` exacto; fail-closed.

## RIU-0022 — P02 AUDIT C03 CONFIG DONOR
`pydantic-settings` confirmado MIT/Pydantic v2; `ADAPT_CANDIDATE`, no integrado; `GAP-C03-CONTRACT-001` por campos/env/defaults/perfiles no definidos.

## RIU-0023..0024 — STRATEGYDELTA R-004
PDF canónico localizado y origen/identidad verificados; materialización binaria bloqueada. `GAP-R004-EXTRACTION-001` permanece OPEN; auditoría commit `f41db4710a7af645288fe1b1339fa5aba6cc894f`.

## RIU-0025 — P02 AUDIT C01 FASTAPI DONOR
Cola 1×1 auditó exclusivamente C01 sin escribir producción. Donor local: `router inteligente universal/Componente open soure router inteligente universal/fastapi/`; `pyproject.toml` blob `06c82344a7010eefaf98f567468dea8be5a5ae10`; `LICENSE` blob `3e92463e6bd522a2a21e5f0a80d8089d6c4be20d`; upstream declarado `https://github.com/fastapi/fastapi`; licencia MIT; Python `>=3.10`; dependencias base Starlette + Pydantic v2. Evidencia persistida en `router inteligente universal/integration/audits/C01-FASTAPI-DONOR-AUDIT.md`, commit `c8d297ed1046445c74190d6ba51bc1a39307462d`. Decisión: `ADAPT_CANDIDATE`, no integrado. Se abrió `GAP-C01-API-CONTRACT-001` porque no están definidos los paths/métodos/schemas/auth/error envelope/WS-SSE de Paneles 1–5.

## COUNCIL12 / CROSS-CHECK / CODA / VERIFY_FINAL RIU-0025
`PASS_AUDIT_ONLY`. Source/destination/ownership/license/dependency fit demostrados; implementación runtime bloqueada por contrato API específico ausente. Cross-check Handoff↔README↔STATE↔CHECKPOINT↔PLAN↔RECOVERY consistente. CODA: fail-closed/no-code y continuar solo con tarea P02 independiente segura. `verify_final = PASS_AUDIT_ONLY`.

## 3 REFUTACIONES RIU-0025
1. FastAPI presente ≠ C01 integrado.
2. FastAPI soporta REST/WS ≠ contrato Paneles 1–5 recuperado.
3. Auditoría PASS ≠ C01 runtime PASS ≠ Paso 2 cerrado ≠ E2E Paso 3.

## NEXT
C01, C03, R-004, HF catalog y filtro LLM permanecen fail-closed hasta nueva evidencia. Cola 1×1 pasa a otro componente P02 independiente con source/contrato suficiente; `REUSE > PATCH > ADAPT > GENERATE`.
