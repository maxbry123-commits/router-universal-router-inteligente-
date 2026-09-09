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

## RIU-0013 — P02 REUSE + WIRE CONECTOR MEMORIA V6
`ConectorMemoria` ya existía en `red/conectores.py`; se reutilizó sin duplicar adapter. Registry `memoria` commit `3987856e107e848e111d96317e3a9c92c40a6cbb`, blob `878d0fb69fce49b62fc9e2d934b3d8896c5cc4c9`; test `tests/test_conector_memoria_v6.py` commit `de82bd75e630f13141df7b2b2b74131163e52200`, blob `0263e511694b7a45b3b8ffaec0f3d0e7b9e2d582`. HF Job `6aa1318d32d5d0c22c5afe2c` descargó 5 archivos exactos de `main` y dio `3 passed in 0.04s`.

## RIU-0014 — P02 REUSE + RECONCILE CONECTOR INTERNO V6
`ConectorInterno` ya existía en `red/conectores.py` y `interno` ya estaba cableado en `red/connector_registry.py`; se evitó adapter duplicado. Registry blob `4beb5b96e5abb6ff7263cdf2297628058a98e790`; test `tests/test_conector_interno_webhook_v6.py` blob `b7dc3343b7515ad9a1f57ccee983ace65bb03a6b`. HF Job `6aa13ab432d5d0c22c5b008f` dio `3 passed in 0.11s`.

## RIU-0015 — P02 REUSE + RECONCILE CONECTOR WEBHOOK V6
`ConectorWebhook` ya existía en `red/conectores.py` y `webhook` ya estaba registrado; no se generó adapter duplicado. Test `tests/test_conector_interno_webhook_v6.py` verifica fail-closed; HF Job `6aa13ab432d5d0c22c5b008f`: `3 passed in 0.11s`.

## RIU-0016 — P02 AUDIT RECOVERY CONTRATO FILTRO LLM
README arquitectura ordenó materializar filtro LLM únicamente con contrato definido/recuperado. Handoff referenciaba `enchufe/validator_v2.py`, inicialmente ausente; se abrió `GAP-BEHAVIOR-CONTRACT-001` sin generar policy.

## RIU-0017 — P02 RECOVER + MATERIALIZE VALIDATOR V2
StrategyDelta sobre documentos fuente de verdad recuperó el código completo de `validator_v2.py` desde `FABLES ENCHUFE UNIVERSAL v2`, source blob `1f2de5b0578391164e6f6f7331507299130e8579`. Se materializó `router inteligente universal/enchufe/validator_v2.py` commit `2e20488e384ad658675d1ccaf6726fa1edd02034`, blob `418f230e705d18525aae63d6930311ccb7b9297b`. Los seis tests nombrados por la fuente quedaron en `tests/test_validator_v2_contract.py`, final commit `de9326ff0167a04024a09fc60617c8bf6b75ae28`, blob `4aa5d4a878f582b82f254cd5ff1fda8d9161fe14`. Primer harness falló por registro `sys.modules`; se corrigió el test sin alterar validator. HF Job sparse-clone `6aa15fea900620b5c77e6fa1` terminó COMPLETED: `6 passed in 0.02s`.

## RIU-0018 — P02 MATERIALIZE C05 ENCHUFE SCHEMA PYDANTIC V2
Búsqueda literal del behavior filter no recuperó policy standalone; FAIL_CLOSED prohibió inventarla. StrategyDelta tomó una tarea P02 independiente ya especificada: DOC-A02 C05 + JSON Schema FABLES. Se materializó `router inteligente universal/domain/schemas/enchufe_v2.py` commit `14d86fb07caa02e552a2c5a7788c197084a8d11f`, blob `faf0b8a2f1474c044143728bf7fdfd41d1a751fa`; test `router inteligente universal/tests/test_enchufe_v2_schema.py` commit `96448365568950d9bbd7405f58e001f7eb419f1c`, blob `53d4ee813b51000609532817ca1b5d02a71459f8`. Primer harness local falló por `importlib`/anotaciones diferidas y se corrigió solo el harness; local final `4 passed`. Primer HF run fue refutado porque `python:3.12-slim` no trae `git`; StrategyDelta materialmente distinto descargó blobs exactos de `main` por raw GitHub. HF Job `6aa165be32d5d0c22c5b07df` terminó COMPLETED/success: `4 passed in 0.09s`.

## 3 REFUTACIONES
1. C05 Pydantic + `validator_v2` PASS ≠ behavior filter standalone implementado.
2. Donor `guardrails` físicamente disponible ≠ policy de comportamiento autorizada.
3. Tests C05/validator/conectores PASS ≠ Paso 2 cerrado ≠ E2E Paso 3.

## NEXT
Cola 1×1: buscar exclusivamente contrato explícito del filtro LLM en fuentes de verdad; si existe → REUSE/PATCH/ADAPT detrás de `guard/plugin` → test fijado → persistir. Si no existe, auditar y ejecutar únicamente la siguiente tarea independiente segura P02 respaldada por arquitectura.
