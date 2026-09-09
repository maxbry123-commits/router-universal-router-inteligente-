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
Gate/conectores v6/registry/validator/schema/RedUniversal y PATCH C15 v1.5→v2.0 verificados; HF Job C15 `6aa16ff732d5d0c22c5b0912`: `5 passed in 0.09s`.

## RIU-0021 — P02 AUDIT R-004 BACKUP / RESPALDO
Handoff declara C19/R-004 `EXISTING_COMPLETE → REUSE`, pero no se recuperó `.py` exacto; fail-closed.

## RIU-0022 — P02 AUDIT C03 CONFIG DONOR
`pydantic-settings` confirmado MIT/Pydantic v2; `ADAPT_CANDIDATE`, no integrado; `GAP-C03-CONTRACT-001` por campos/env/defaults/perfiles no definidos.

## RIU-0023..0024 — STRATEGYDELTA R-004
PDF canónico localizado y origen/identidad verificados; materialización binaria bloqueada. `GAP-R004-EXTRACTION-001` permanece OPEN; auditoría commit `f41db4710a7af645288fe1b1339fa5aba6cc894f`.

## RIU-0025 — P02 AUDIT C01 FASTAPI DONOR
Donor FastAPI local auditado; auditoría commit `c8d297ed1046445c74190d6ba51bc1a39307462d`. Decisión `ADAPT_CANDIDATE`, no integrado; `GAP-C01-API-CONTRACT-001` por falta del contrato exacto Paneles 1–5.

## RIU-0026 — P02 MATERIALIZE C10 RESILIENCE
Cola 1×1 seleccionó C10 porque DOC-A02 y arquitectura v6 definen explícitamente comportamiento, defaults y destino, y no existe implementación Router-owned previa que reutilizar. Se aplicó `GENERATE_FROM_EXPLICIT_CONTRACT`, sin dependencia externa ni skill de descarga.

Producción: `router inteligente universal/engine/resilience.py`; commit `6b408a781d886a8bde43c3f62b48247d872afd36`; read-back blob `6a92375926909864d6fe604b4966b306a9aac449`. Implementa R5 Retry (`intentos=3`, `base_ms=500`, backoff exponencial) + R6 Circuit Breaker por nodo (`CLOSED→OPEN→HALF_OPEN`, umbral 5, ventana 60s, cooldown 30s). No resuelve conectores: acepta una operación async ya autorizada para conservar ownership Enchufe Universal/RedUniversal.

Test: `router inteligente universal/tests/test_resilience_c10.py`; commit final `a0e74c04c93dfc2cc0c96da9c31234d98b44333c`; blob `77ce9fef2e899215eff9ed2dc2f473adc82950b7`.

StrategyDelta: job HF inicial `6aa1adb121047bf1b03707ea` falló por ausencia de `git`; el siguiente intento cambió instalación de entorno; cierre final usó estrategia materialmente distinta descargando únicamente raw blobs desde el commit fijado. HF Job `6aa1ae8221047bf1b03707ff` → `5 passed in 0.10s`. Auditoría persistida en `router inteligente universal/integration/audits/C10-RESILIENCE-MATERIALIZATION.md`, commit `538e0e04f2ca99ee891ddfbee8b233cc7459dd1d`.

## COUNCIL12 / CROSS-CHECK / CODA / VERIFY_FINAL RIU-0026
Council12 PASS: objetivo, INPUT, destino, estado, evidencia, reusable, arquitectura, concurrencia, dependencia, test, rollback y cierre. Cross-check DOC-A02↔v6↔Handoff↔STATE↔CHECKPOINT↔PLAN↔RECOVERY PASS. CODA `PASS_SAFE_DELTA`. `verify_final = PASS_C10_RUNTIME_CONTRACT`.

## 3 REFUTACIONES RIU-0026
1. C10 presente ≠ verificado: se exigió pytest remoto sobre commit fijado.
2. C10 runtime PASS ≠ Paso 2 completo ≠ E2E Paso 3.
3. Retry/Breaker no posee routing ni registro; todo destino sigue pasando por Enchufe Universal/RedUniversal.

## NEXT
C01, C03, R-004, HF catalog y filtro LLM permanecen fail-closed hasta nueva evidencia. Cola 1×1 pasa a otro componente P02 independiente con source/contrato suficiente; `REUSE > PATCH > ADAPT > GENERATE`.
