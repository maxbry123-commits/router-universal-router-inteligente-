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
- `ConectorDB` v6 añadido siguiendo v6 §4.4 y TASK-03 R-002: DSN únicamente por env; adapters lazy para Postgres/MySQL/Redis; fail-closed para motor/params/acción inválidos.
- `ConectorGitLab` y `ConectorMCPApp` adaptados/cableados en registry y verificados contractualmente.
- `ConectorVPS` reutilizado desde `red/conectores.py`, cableado en registry y verificado sin crear adapter duplicado.
- `ConectorMemoria` reutilizado desde `red/conectores.py` y cableado como `memoria` en `connector_registry.py`; registry commit `3987856e107e848e111d96317e3a9c92c40a6cbb`, blob `878d0fb69fce49b62fc9e2d934b3d8896c5cc4c9`.
- Test Memoria: `tests/test_conector_memoria_v6.py`, commit `de82bd75e630f13141df7b2b2b74131163e52200`, blob `0263e511694b7a45b3b8ffaec0f3d0e7b9e2d582`; HF Job `6aa1318d32d5d0c22c5afe2c` descargó archivos exactos de `main` y produjo `3 passed in 0.04s`.

Los PASS actuales demuestran contratos/adapters, no servicios remotos reales. Esos pertenecen al Paso 3.

Siguiente delta 1×1: siguiente conector v6 prioritario respaldado por arquitectura, preservando todos los baselines ya verificados.

## 8. Regla de cierre
`archivo presente != integrado`
`componente descargado != adaptado`
`codigo escrito != ejecutado`
`mock/injection != test remoto real`

Solo `VERIFIED_CLOSED` después del test integral del Paso 3.
