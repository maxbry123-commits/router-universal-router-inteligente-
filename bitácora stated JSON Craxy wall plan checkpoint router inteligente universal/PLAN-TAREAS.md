# PLAN DE TAREAS — ROUTER INTELIGENTE UNIVERSAL

Contrato: `tel.workflow/v3` · modo `FAIL_CLOSED_LOOP`

## Lista única activa
1. 📌🛜 **Paso 1 — componentes + LLM/Hugging Face** — ACTIVE
   - ✅ componentes open source movidos a `router inteligente universal/Componente open soure router inteligente universal/`;
   - ✅ reuse local HF auditado: `huggueface/manifest.yml` + `huggueface/bridge/router_hf_bridge.py`;
   - ✅ StrategyDelta autorizado: Hugging Face Job + `HfApi.list_models(author='COMAND-CENTER-1')` verificó `COUNT 0` modelos públicos propiedad de la cuenta;
   - ✅ verificado que el contenedor del Job no recibe `HF_TOKEN`; por tanto `COUNT 0` no prueba ausencia de privados/endpoints;
   - ⏳ auditar IDs reales detrás de endpoints/configuración HF consumibles por el Router;
   - GAP-HF-CATALOG-001 PARTIAL: catálogo público del owner resuelto, privados/endpoints aún no enumerados;
   - ⏳ preparar adapters/FastAPI solo para `model_id` confirmados, sin crear segundo core.
2. 📌 **Paso 2 — cableado + poda + código faltante** — PENDING
   - REUSE > PATCH > ADAPT > GENERATE;
   - cablear por Enchufe Universal;
   - escribir solo faltantes de arquitectura;
   - capa/filtro de comportamiento LLM separada del DAG.
3. 📌✅ **Paso 3 — tests integración** — PENDING
   - Hugging Face + GitHub + API + agentes;
   - exigir ruta + SHA/diff + read-back + test/log.

Cola 1×1 actual: reconciliar referencias HF configuradas/endpoints → confirmar `model_id/revision/task` → adapters/FastAPI.

Reglas: no sobreingeniería; no añadir pasos fuera de estos 3; componente presente ≠ integrado; GAP → StrategyDelta distinto; FLAG → registrar y continuar solo con tarea independiente segura.
