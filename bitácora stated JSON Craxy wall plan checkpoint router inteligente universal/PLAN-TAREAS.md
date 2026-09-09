# PLAN DE TAREAS — ROUTER INTELIGENTE UNIVERSAL

Contrato: `tel.workflow/v3` · modo `FAIL_CLOSED_LOOP`

## Lista única activa
1. 📌🛜 **Paso 1 — componentes + LLM/Hugging Face** — PARTIAL/CLOSED_SAFE
   - ✅ componentes movidos al code root;
   - ✅ bridge HF local auditado;
   - ✅ owner público HF: COUNT 0;
   - 🚩 GAP-HF-CATALOG-001: privados/endpoints sin `model_id` confirmado; no inventar adapters.
2. 📌 **Paso 2 — cableado + poda + código faltante** — ACTIVE
   - ✅ REUSE `red/enchufe_gate.py` + baseline determinista PASS;
   - ✅ REUSE `red/conectores.py` sin reescribir HTTP/MCP;
   - ✅ PATCH/ADAPT `ConectorHuggingFace` + pytest 3/3 PASS;
   - ✅ PATCH/ADAPT `ConectorDB` v6 en el mismo módulo, DSN solo por entorno, Postgres/MySQL/Redis fail-closed;
   - ✅ verify commit fijado en HF Job `6aa1105432d5d0c22c5af971`: pytest 3/3 PASS (`PASS_CONECTOR_DB_V6_CONTRACT`);
   - ⏳ siguiente cola 1×1: siguiente conector v6 prioritario demostrado por arquitectura, preservando baselines;
   - ⏳ capa/filtro comportamiento LLM pendiente hasta contrato definido/recuperado.
3. 📌✅ **Paso 3 — tests integración** — PENDING
   - Hugging Face + GitHub + API + agentes;
   - exigir ruta + SHA/diff + read-back + test/log.

Cola 1×1 actual: `red/conectores.py` → siguiente connector PATCH/ADAPT v6 → test → persistir.
Reglas: no sobreingeniería; no añadir pasos; REUSE > PATCH > ADAPT > GENERATE; archivo presente ≠ integrado.
