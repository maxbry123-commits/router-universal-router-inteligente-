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
`huggueface/manifest.yml` y `router_hf_bridge.py` son REUSE confirmados. HF Job verificó 0 modelos públicos del owner `COMAND-CENTER-1`; `coneccion huggueface Github/registry/repos.json` contiene 19 namespaces GitHub y ningún `model_id` HF. No se generan adapters por modelos supuestos.

## 7. Estado Paso 2
Deltas REUSE materializados desde la fuente canónica antes de ampliar capacidad:
- `../router inteligente universal/red/enchufe_gate.py` — commit `4007983f2cabecdf78198a1a7ae23aff5fcfa8ce`.
- `../router inteligente universal/tests/test_enchufe_gate_v15.py` — commit `7328d377726dbf435cbc877d6909a5f74a9bcbb3`; `PASS_ENCHUFE_GATE_V15_REUSE`.
- `../router inteligente universal/red/conectores.py` — commit `8dc43490cc14f21c6d09d9e3d824606868679766`; baseline canónico conserva `ConectorHTTP`, `ConectorMCP`, GitHub, VPS, memoria, interno y webhook.
- `../router inteligente universal/tests/test_conectores_baseline.py` — commit `94ad8b8879c8c03b2f084ac62059bd346da6a610`; ejecución local determinista `3 passed in 0.11s`.

Siguiente delta 1×1: PATCH/ADAPT del catálogo v6 sobre ese baseline, únicamente con capacidades demostradas por arquitectura y donors locales, sin reescribir los conectores base.

## 8. Regla de cierre
`archivo presente != integrado`
`componente descargado != adaptado`
`codigo escrito != ejecutado`
`mock != test real`

Solo `VERIFIED_CLOSED` después del test integral del Paso 3.
