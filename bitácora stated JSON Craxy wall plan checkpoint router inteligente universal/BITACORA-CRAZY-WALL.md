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
`ConectorHuggingFace` reutiliza `ConectorHTTP`; commit `eb3d9fc2f67a33d8cf22056488ea299a2ffa7875`; contract test PASS.

## RIU-0009 — P02 ADAPT CONECTOR DB V6
`ConectorDB` preserva HTTP/MCP/GitHub/HF; DSN solo por env; Postgres/MySQL/Redis; HF Job `6aa1105432d5d0c22c5af971` PASS contractual.

## RIU-0010 — P02 ADAPT + WIRE CONECTOR GITLAB V6
Adapter `red/conector_gitlab.py`; secretos solo por entorno; acción desconocida fail-closed. Adapter commit `122e5baeec061e89be2fe32411d0b3d5ee70f6aa`; registry y test verificados por HF Job `6aa11334900620b5c77e5ca7` success.

## RIU-0011 — P02 ADAPT + WIRE CONECTOR MCP APP V6
`red/conector_mcp_app.py` extiende `ConectorMCP`; no crea segundo core. Commit `8a45204be6c3de7a2b8e95f648ef2cbc678dbda0`; registry `1289c5b57e72029a95f9d794eac5ea648c71f9e2`; test `1df8b57fc5a410a383a1a1b4e2b78535eedc5efe`; HF Job `6aa11dac32d5d0c22c5afb80` success.

## RIU-0012 — P02 REUSE + WIRE CONECTOR VPS V6
`ConectorVPS` ya existía en `red/conectores.py`; se reutilizó sin crear adapter duplicado. Registry `vps` commit `2b57fe8e4ef7965ee23a6a086415ef8c21db7f60`; test `tests/test_conector_vps_v6.py` commit `7f04404876b2fb1123742d32dd4d48741a2b388d`. HF Job `6aa12c19900620b5c77e61d2` status success con `PASS_CONECTOR_VPS_V6: 3/3`; unknown command fail-closed.

## 3 REFUTACIONES
1. COUNT 0 público ≠ ausencia de privados/endpoints HF.
2. ConectorVPS contractual PASS ≠ VPS remoto real del Paso 3.
3. Tests contractuales PASS ≠ Paso 2/3 completos.

## NEXT
Cola 1×1: siguiente conector v6 prioritario respaldado por arquitectura → REUSE/PATCH/ADAPT → registry → test fijado → persistir; conservar baselines verificados.
