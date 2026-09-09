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
Handoff declara C19/R-004 `EXISTING_COMPLETE → REUSE`, pero no se recuperó source/ownership físico; se abrió `GAP-R004-SOURCE-001` y no se generó sustituto.

## RIU-0022 — P02 AUDIT C03 CONFIG DONOR
Handoff declara C03 `Config inmutable` como MISSING y ordena `env única fuente de configuración`. Se inspeccionó primero el donor físico local `router inteligente universal/Componente open soure router inteligente universal/pydantic-settings/`. README blob `84c893ab07d3282555622f69cee358686ba4ea99`; `pyproject.toml` blob `21c3e4780e6da923cccf8435498930f4d9e1bece`; upstream declarado `https://github.com/pydantic/pydantic-settings`; licencia MIT; capacidad `Settings management using Pydantic`, Pydantic v2 y `python-dotenv` demostrados. Se creó evidencia `router inteligente universal/integration/audits/C03-CONFIG-DONOR-AUDIT.md`, commit `fa787fe101858ecd2ddf02e1f9ff25238a2148ef`. Decisión `ADAPT_CANDIDATE`, no integrado: no existe contrato recuperado de nombres env/campos, requeridos, defaults o perfiles, por lo que se abre `GAP-C03-CONTRACT-001` y no se inventa `settings.py`.

## COUNCIL12 / CROSS-CHECK / CODA / VERIFY_FINAL RIU-0022
PASS de auditoría/provenance: objetivo, INPUT, destino, estado, evidencia donor, reusable, arquitectura, concurrencia, dependencia, rollback y cierre de auditoría son coherentes; test runtime N/A porque no se reclama código ejecutable. Cross-check Handoff↔donor↔README arquitectura confirma que `pydantic-settings` es donor apropiado pero no define contrato específico del Router. CODA preserva `REUSE > PATCH > ADAPT > GENERATE`; verify_final prohíbe subir progreso por mera presencia.

## 3 REFUTACIONES
1. Donor `pydantic-settings` presente ≠ C03 integrado.
2. Donor capaz + `env única fuente` ≠ contrato de campos del Router definido.
3. Auditoría C03 PASS ≠ código C03 PASS ≠ Paso 2 cerrado ≠ E2E Paso 3.

## NEXT
Cola 1×1: recuperar contrato de campos/env C03 desde evidencia del proyecto. Si aparece, ADAPT mínimo sobre donor local → read-back/blob → test → persistir. Si no aparece, mantener GAP y continuar exclusivamente otra tarea P02 independiente con contrato suficiente. R-004 y filtro LLM permanecen fail-closed.
