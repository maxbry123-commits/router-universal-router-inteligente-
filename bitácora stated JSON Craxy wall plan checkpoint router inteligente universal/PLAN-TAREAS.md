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
   - ✅ REUSE `ConectorVPS`, `ConectorMemoria`, `ConectorInterno`, `ConectorWebhook` + registry/tests remotos PASS;
   - ✅ registry v6 fijado por `tests/test_connector_registry_v6.py`; HF Job `6aa15404900620b5c77e6c45`: 13 passed in 0.05s;
   - ✅ StrategyDelta recuperó desde FABLES Enchufe Universal v2 el código contractual de `enchufe/validator_v2.py` (source blob `1f2de5b0578391164e6f6f7331507299130e8579`);
   - ✅ `router inteligente universal/enchufe/validator_v2.py` materializado commit `2e20488e384ad658675d1ccaf6726fa1edd02034`, blob `418f230e705d18525aae63d6930311ccb7b9297b`;
   - ✅ tests contractuales previstos por la fuente materializados; HF Job `6aa15fea900620b5c77e6fa1` COMPLETED con `6 passed in 0.02s`;
   - 🚩 GAP-BEHAVIOR-CONTRACT-001 permanece: recuperar `validator_v2` no equivale a recuperar una policy standalone de comportamiento LLM; prohibido inferir/generar semántica del filtro;
   - ⏳ cola 1×1: continuar fuentes de verdad buscando contrato explícito del filtro; si aparece → guard/plugin + test; si no → tarea P02 independiente segura.
3. 📌✅ **Paso 3 — tests integración** — PENDING
   - Hugging Face + GitHub + API + agentes;
   - exigir ruta + SHA/diff + read-back + test/log.

Cola 1×1 actual: contrato explícito de behavior filter → REUSE/PATCH/ADAPT solo si existe → guard/plugin → test → persistir.
Reglas: no sobreingeniería; no añadir pasos; REUSE > PATCH > ADAPT > GENERATE; archivo presente ≠ integrado; validator PASS ≠ filtro LLM ≠ E2E.
