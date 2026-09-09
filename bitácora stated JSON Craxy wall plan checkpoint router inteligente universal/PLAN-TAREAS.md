# PLAN DE TAREAS — ROUTER INTELIGENTE UNIVERSAL

Contrato: `tel.workflow/v3` · modo `FAIL_CLOSED_LOOP`

## Lista única activa
1. 📌🛜 **Paso 1 — componentes + LLM/Hugging Face** — PARTIAL/CLOSED_SAFE
   - ✅ componentes movidos a `router inteligente universal/Componente open soure router inteligente universal/`;
   - ✅ bridge HF local auditado;
   - ✅ owner público HF auditado: COUNT 0 modelos públicos;
   - ✅ registry HF/GitHub cruzado: contiene namespaces GitHub, no `model_id` HF;
   - 🚩 GAP-HF-CATALOG-001: privados/endpoints sin modelo confirmado; no generar adapters inventados.
2. 📌 **Paso 2 — cableado + poda + código faltante** — ACTIVE
   - ✅ REUSE `red/enchufe_gate.py` desde fuente canónica al code root;
   - ✅ test determinista v1.5 PASS (`PASS_ENCHUFE_GATE_V15_REUSE`);
   - ✅ REUSE `red/conectores.py` desde la misma fuente canónica, sin reescribir HTTP/MCP;
   - ✅ baseline determinista de conectores: `pytest` 3/3 PASS;
   - ✅ PATCH/ADAPT `ConectorHuggingFace` desde contrato v6, sin model_id inventado;
   - ✅ test exact-blob HF: `pytest` 3/3 PASS (`PASS_CONECTOR_HUGGINGFACE_V6_CONTRACT`);
   - ⏳ siguiente cola 1×1: siguiente conector v6 de mayor valor demostrado por arquitectura, conservando baselines;
   - ⏳ capa/filtro comportamiento LLM queda pendiente hasta contrato definido/recuperado.
3. 📌✅ **Paso 3 — tests integración** — PENDING
   - Hugging Face + GitHub + API + agentes;
   - exigir ruta + SHA/diff + read-back + test/log.

Cola 1×1 actual: `red/conectores.py` → siguiente connector PATCH/ADAPT v6 → test → persistir.
Reglas: no sobreingeniería; no añadir pasos; REUSE > PATCH > ADAPT > GENERATE; archivo presente ≠ integrado.
