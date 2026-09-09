# PLAN DE TAREAS — ROUTER INTELIGENTE UNIVERSAL

Contrato: `tel.workflow/v3` · modo `FAIL_CLOSED_LOOP`

## Lista única activa
1. 📌🛜 **Paso 1 — componentes + LLM/Hugging Face** — ACTIVE
   - ✅ componentes open source movidos a `router inteligente universal/Componente open soure router inteligente universal/`;
   - ✅ reuse local HF auditado: `huggueface/manifest.yml` + `huggueface/bridge/router_hf_bridge.py`;
   - ⏳ auditar LLM reales disponibles en Hugging Face;
   - GAP-HF-CATALOG-001: autenticación OK, pero catálogo remoto no enumerable por `model_search`; StrategyDelta = ruta alternativa autorizada de lectura;
   - ⏳ preparar adapters/FastAPI solo para `model_id` confirmados, sin crear segundo core.
2. 📌 **Paso 2 — cableado + poda + código faltante** — PENDING
   - REUSE > PATCH > ADAPT > GENERATE;
   - cablear por Enchufe Universal;
   - escribir solo faltantes de arquitectura;
   - capa/filtro de comportamiento LLM separada del DAG.
3. 📌✅ **Paso 3 — tests integración** — PENDING
   - Hugging Face + GitHub + API + agentes;
   - exigir ruta + SHA/diff + read-back + test/log.

Cola 1×1 actual: resolver enumeración real HF → registrar modelos confirmados → adapters/FastAPI.

Reglas: no sobreingeniería; no añadir pasos fuera de estos 3; componente presente ≠ integrado; GAP → StrategyDelta distinto; FLAG → registrar y continuar solo con tarea independiente segura.
