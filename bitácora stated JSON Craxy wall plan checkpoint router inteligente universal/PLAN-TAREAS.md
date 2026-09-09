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
   - ✅ StrategyDelta recuperó desde FABLES Enchufe Universal v2 el código contractual de `enchufe/validator_v2.py`;
   - ✅ `router inteligente universal/enchufe/validator_v2.py` materializado y HF Job `6aa15fea900620b5c77e6fa1`: 6 passed in 0.02s;
   - ✅ C05 `domain/schemas/enchufe_v2.py` materializado desde JSON Schema FABLES + DOC-A02, sin duplicar invariantes conductuales del validator;
   - ✅ test `tests/test_enchufe_v2_schema.py`; local 4/4 PASS y HF Job `6aa165be32d5d0c22c5b07df` COMPLETED success, 4 passed in 0.09s;
   - 🚩 GAP-BEHAVIOR-CONTRACT-001 permanece: schema/validator/perfiles no equivalen a policy standalone de comportamiento LLM; prohibido inferir/generar semántica del filtro;
   - ⏳ cola 1×1: continuar fuentes de verdad buscando contrato explícito del filtro; si aparece → guard/plugin + test; si no → siguiente tarea P02 independiente segura con donor audit.
3. 📌✅ **Paso 3 — tests integración** — PENDING
   - Hugging Face + GitHub + API + agentes;
   - exigir ruta + SHA/diff + read-back + test/log.

Cola 1×1 actual: contrato explícito de behavior filter → REUSE/PATCH/ADAPT solo si existe → guard/plugin → test → persistir; si sigue GAP, auditar siguiente Cxx P02 antes de GENERATE.
Reglas: no sobreingeniería; no añadir pasos; REUSE > PATCH > ADAPT > GENERATE; archivo presente ≠ integrado; schema/validator PASS ≠ filtro LLM ≠ E2E.
