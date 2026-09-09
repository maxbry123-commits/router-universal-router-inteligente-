# Router Inteligente Universal — Arquitectura y método de trabajo

Contrato operativo: `tel.workflow/v3` · modo `FAIL_CLOSED_LOOP`.

## 1. Objetivo
Backend Python 95% determinista / 5% LLM. El Router no inventa DAGs: clasifica la tarea y activa una plantilla fija autorizada. Todo destino/origen entra por Enchufe Universal como Conector.

## 2. Flujo funcional
`INPUT -> classifier -> template DAG fija -> validator/Enchufe Gate -> Router/RedUniversal -> worker/conector -> destino -> verify/state`

La IA puede producir contenido dentro de nodos autorizados, pero no crear, borrar, reordenar ni sustituir el DAG.

## 3. Plan autorizado — solo 3 pasos
1. **Componentes + Hugging Face/LLM:** componentes centralizados; owner público HF auditado; privados/endpoints sin `model_id` confirmado permanecen FLAG.
2. **Cableado + poda + faltantes:** ACTIVE. `REUSE > PATCH > ADAPT > GENERATE`; conectar por Enchufe Universal; separar contracts/adapters/plugins/registry/loader/guards/tests.
3. **Test integral:** Hugging Face + GitHub + API + agentes con evidencia real.

## 4. Arquitectura de trabajo LOOP
`INPUT LITERAL -> SHERIFF -> STATE/CHECKPOINT/PLAN/RECOVERY -> RESEARCH/REUSE -> PLAN 1x1 -> EXECUTE -> VERIFY/REFUTE -> PERSIST -> NEXT`

## 5. Evidencia mínima
`ruta + commit/tree/blob SHA + read-back + test/log + URL/SHA externo cuando aplique`.

## 6. Estado Hugging Face
Bridge HF REUSE confirmado. HF Job verificó 0 modelos públicos del owner `COMAND-CENTER-1`; registry sin `model_id` HF. No se generan adapters por modelos supuestos.

## 7. Estado Paso 2
- Enchufe Gate v1.5 reutilizado y verificado.
- Conectores baseline reutilizados sin reescribir HTTP/MCP.
- `ConectorHuggingFace` v6 añadido sobre `ConectorHTTP`; contrato verificado 3/3.
- `ConectorDB` v6 añadido en `../router inteligente universal/red/conectores.py` siguiendo v6 §4.4 y TASK-03 R-002: DSN únicamente por env; adapters lazy para Postgres/MySQL/Redis; fail-closed para motor/params/acción inválidos.
- Código DB: commit `885cf992222e59097e5042b74b5371a3a4aa7d1a`, blob `beca488fdb34ff14ee2f5b4e4ef8c8de45ee9c78`.
- Test: `../router inteligente universal/tests/test_conector_db_v6.py`, commit `0f6681e17988554a3206d9d3fac7326028ae24dc`; HF Job fijado al commit `6aa1105432d5d0c22c5af971` => `3 passed in 0.10s`.

Los PASS actuales demuestran contratos/adapters, no servicios remotos reales. Esos pertenecen al Paso 3.

Siguiente delta 1×1: siguiente conector v6 prioritario respaldado por arquitectura, preservando todos los baselines ya verificados.

## 8. Regla de cierre
`archivo presente != integrado`
`componente descargado != adaptado`
`codigo escrito != ejecutado`
`mock/injection != test remoto real`

Solo `VERIFIED_CLOSED` después del test integral del Paso 3.
