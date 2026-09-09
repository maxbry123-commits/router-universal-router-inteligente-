# PLAN DE TAREAS — ROUTER INTELIGENTE UNIVERSAL

Contrato: `tel.workflow/v3` · modo `FAIL_CLOSED_LOOP`

## Lista única activa
1. 📌🛜 **Paso 1 — componentes + LLM/Hugging Face** — ACTIVE
   - mover componentes open source a `router inteligente universal/Componente open soure router inteligente universal/`;
   - auditar LLM disponibles en Hugging Face;
   - preparar adapters/FastAPI por modelo sin crear un segundo core.
2. 📌 **Paso 2 — cableado + poda + código faltante** — PENDING
   - REUSE > PATCH > ADAPT > GENERATE;
   - cablear por Enchufe Universal;
   - escribir solo faltantes de arquitectura;
   - capa/filtro de comportamiento LLM separada del DAG.
3. 📌✅ **Paso 3 — tests integración** — PENDING
   - Hugging Face + GitHub + API + agentes;
   - exigir ruta + SHA/diff + read-back + test/log.

Reglas: cola 1×1; no sobreingeniería; no añadir pasos fuera de estos 3; componente presente ≠ integrado; GAP → StrategyDelta distinto; FLAG → registrar y continuar solo con tarea independiente segura.
