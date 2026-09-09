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
   - ✅ PATCH/ADAPT `ConectorHuggingFace` + test contractual PASS;
   - ✅ PATCH/ADAPT `ConectorDB` v6 + test contractual PASS;
   - ✅ ADAPT/WIRE `ConectorGitLab` + registry + test remoto PASS;
   - ✅ ADAPT/WIRE `ConectorMCPApp` + registry + test remoto PASS;
   - ✅ REUSE `ConectorVPS` existente; WIRE `vps` en registry; test fail-closed remoto PASS (`HF Job 6aa12c19900620b5c77e61d2`);
   - ⏳ siguiente cola 1×1: siguiente conector v6 prioritario demostrado por arquitectura;
   - ⏳ capa/filtro comportamiento LLM pendiente hasta contrato definido/recuperado.
3. 📌✅ **Paso 3 — tests integración** — PENDING
   - Hugging Face + GitHub + API + agentes;
   - exigir ruta + SHA/diff + read-back + test/log.

Cola 1×1 actual: siguiente conector v6 → REUSE/PATCH/ADAPT → registry → test → persistir.
Reglas: no sobreingeniería; no añadir pasos; REUSE > PATCH > ADAPT > GENERATE; archivo presente ≠ integrado.
