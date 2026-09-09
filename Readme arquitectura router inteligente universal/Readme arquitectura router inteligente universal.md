# Router Inteligente Universal — Arquitectura y método de trabajo

Contrato operativo: `tel.workflow/v3` · modo `FAIL_CLOSED_LOOP`.

## 1. Objetivo
Backend Python 95% determinista / 5% LLM. El Router no inventa DAGs: clasifica la tarea y activa una plantilla fija autorizada. Todo destino/origen entra por Enchufe Universal como Conector.

## 2. Flujo funcional
`INPUT -> classifier -> template DAG fija -> validator/Enchufe Gate -> Router/RedUniversal -> worker/conector -> destino -> verify/state`

La IA puede producir contenido dentro de nodos autorizados, pero no crear, borrar, reordenar ni sustituir el DAG.

## 3. Plan autorizado — solo 3 pasos
1. **Componentes + Hugging Face/LLM:** centralizar componentes bajo `../router inteligente universal/Componente open soure router inteligente universal/`, auditar LLM disponibles y preparar adapters/FastAPI por modelo.
2. **Cableado + poda + faltantes:** `REUSE > PATCH > ADAPT > GENERATE`; separar contracts/adapters/plugins/registry/loader/guards/tests; conectar únicamente por Enchufe Universal; crear capa/filtro de comportamiento LLM separada del DAG.
3. **Test integral:** Hugging Face + GitHub + API + agentes con evidencia real.

No añadir fases, servicios ni arquitecturas paralelas salvo GAP demostrado dentro de estos tres pasos.

## 4. Arquitectura de trabajo LOOP
```text
INPUT LITERAL -> SHERIFF -> STATE/CHECKPOINT/PLAN/RECOVERY -> RESEARCH/REUSE
-> PLAN 1x1 -> EXECUTE DELTA -> VALIDATE/VERIFY/REFUTE
-> PASS:PERSIST:NEXT | GAP:StrategyDelta:RETRY | FLAG:RECOVERY:NEXT SAFE
```

## 5. Separación obligatoria
```text
contracts/
adapters/
plugins/
registry/
loader/
guards/
tests/
evidence/
```

Componente descargado ≠ integrado. Vendor/donor no se convierte en segundo dueño del workflow.

## 6. Fuentes de verdad
1. INPUT literal del Director.
2. `../readme Handoff indice componentes.md`.
3. `../bitácora stated JSON Craxy wall plan checkpoint router inteligente universal/STATE.json`.
4. CHECKPOINT + PLAN + RECOVERY + BITACORA.
5. Documentos de arquitectura del proyecto.
6. HEAD real + pruebas.

## 7. Evidencia mínima
`ruta + commit/tree/blob SHA + read-back + test/log + URL/SHA externo cuando aplique`.

## 8. Regla de cierre
`archivo presente != integrado`
`componente descargado != adaptado`
`codigo escrito != ejecutado`
`mock != test real`

Solo `VERIFIED_CLOSED` después del test integral del Paso 3.
