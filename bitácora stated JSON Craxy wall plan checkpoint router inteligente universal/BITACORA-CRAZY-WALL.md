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
Fuente: arquitectura v6 / TASK-03 R-002. Se creó adapter separado `red/conector_gitlab.py` para no engordar el módulo base. Acciones declaradas: project_info/get_file/create_issue/create_mr/trigger_pipeline; `GITLAB_TOKEN` solo por entorno; acción desconocida fail-closed.
Adapter commit `122e5baeec061e89be2fe32411d0b3d5ee70f6aa`, blob `d0e1de92a0cb3ab1577e29c2c83adf020806f4c1`.
Se creó `red/connector_registry.py` commit `0c13109de1f2e120b9c3eea7990026b4c80f8639`, preservando HTTP/MCP/GitHub/HF/DB e incorporando GitLab.
Test actualizado commit `0e5dbf8d4efa34df83397fea6631a74bb7896c12`; HF Job `6aa11334900620b5c77e5ca7` status success ejecutando pytest del adapter + registry.
No se declara GitLab remoto real: eso pertenece al Paso 3.

## 3 REFUTACIONES
1. COUNT 0 público ≠ ausencia de privados/endpoints HF.
2. Adapter/registry GitLab PASS ≠ GitLab remoto real verificado.
3. Tests contractuales PASS ≠ Paso 2/3 completos.

## NEXT
Cola 1×1: siguiente conector v6 prioritario respaldado por arquitectura → adapter/registry → test fijado → persistir; conservar baselines verificados.
