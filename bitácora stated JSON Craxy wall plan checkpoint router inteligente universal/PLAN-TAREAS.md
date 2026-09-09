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
   - ✅ REUSE `ConectorMemoria` existente; WIRE `memoria` en registry; read/commit/snapshot/health + fail-closed PASS (`HF Job 6aa1318d32d5d0c22c5afe2c`, 3 passed in 0.04s);
   - ✅ REUSE `ConectorInterno` existente y registry ya cableado; test exact-main PASS (`HF Job 6aa13ab432d5d0c22c5b008f`, 3 passed in 0.11s); no adapter duplicado;
   - ✅ REUSE `ConectorWebhook` existente y registry ya cableado; el mismo test exact-main acredita registry + `env_faltante` fail-closed (`HF Job 6aa13ab432d5d0c22c5b008f`, 3 passed in 0.11s); no adapter duplicado;
   - ⏳ siguiente cola 1×1: siguiente componente/conector v6 prioritario demostrado por arquitectura;
   - ⏳ capa/filtro comportamiento LLM pendiente hasta contrato definido/recuperado.
3. 📌✅ **Paso 3 — tests integración** — PENDING
   - Hugging Face + GitHub + API + agentes;
   - exigir ruta + SHA/diff + read-back + test/log.

Cola 1×1 actual: siguiente delta arquitectónico → REUSE/PATCH/ADAPT → registry/loader/guard según corresponda → test → persistir.
Reglas: no sobreingeniería; no añadir pasos; REUSE > PATCH > ADAPT > GENERATE; archivo presente ≠ integrado.
