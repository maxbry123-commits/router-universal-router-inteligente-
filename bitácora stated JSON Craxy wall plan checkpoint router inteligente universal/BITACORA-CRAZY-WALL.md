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

## RIU-0006 — P02 REUSE ENCHUFE GATE
`router inteligente universal/red/enchufe_gate.py` commit `4007983f2cabecdf78198a1a7ae23aff5fcfa8ce`; `PASS_ENCHUFE_GATE_V15_REUSE`.

## RIU-0007 — P02 REUSE CONECTORES BASELINE
`red/conectores.py` baseline commit `8dc43490cc14f21c6d09d9e3d824606868679766`; pytest 3/3 PASS.

## RIU-0008 — P02 ADAPT CONECTOR HUGGING FACE V6
`ConectorHuggingFace` reutiliza `ConectorHTTP`; commit `eb3d9fc2f67a33d8cf22056488ea299a2ffa7875`; exact-blob pytest 3/3 PASS.

## RIU-0009 — P02 ADAPT CONECTOR DB V6
Fuente: arquitectura v6 §4.4 + TASK-03 R-002. Se añadió únicamente `ConectorDB` a `red/conectores.py`, preservando HTTP/MCP/GitHub/HF. DSN solo por env; Postgres/MySQL/Redis; motor/acción inválidos fail-closed.
Código commit `885cf992222e59097e5042b74b5371a3a4aa7d1a`, blob `beca488fdb34ff14ee2f5b4e4ef8c8de45ee9c78`.
Test commit `0f6681e17988554a3206d9d3fac7326028ae24dc`.
Verify: primer HF Job detectó dependencia de test ausente (`pytest`); StrategyDelta distinto instaló pytest/httpx y ejecutó el commit fijado. HF Job `6aa1105432d5d0c22c5af971`: `3 passed in 0.10s`; `PASS_CONECTOR_DB_V6_CONTRACT`.
Esto es evidencia contractual/injection, no conexión a DB remota del Paso 3.

## 3 REFUTACIONES
1. COUNT 0 público ≠ ausencia de privados/endpoints.
2. Adapter HF/DB PASS ≠ servicios remotos reales verificados.
3. Tests contractuales PASS ≠ Paso 2/3 completos.

## NEXT
Cola 1×1: siguiente conector v6 prioritario respaldado por arquitectura → PATCH/ADAPT → test fijado a commit → persistir; conservar baselines verificados.
