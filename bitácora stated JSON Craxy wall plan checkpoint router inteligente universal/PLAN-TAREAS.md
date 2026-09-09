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
   - ✅ PATCH/ADAPT conectores HF/DB/GitLab/MCPApp + REUSE VPS/Memoria/Interno/Webhook; registry/tests remotos PASS;
   - ✅ registry v6 fijado por `tests/test_connector_registry_v6.py`; HF Job `6aa15404900620b5c77e6c45`: 13 passed in 0.05s;
   - ✅ StrategyDelta recuperó y materializó `enchufe/validator_v2.py`; HF Job `6aa15fea900620b5c77e6fa1`: 6 passed in 0.02s;
   - ✅ C05 `domain/schemas/enchufe_v2.py` materializado desde JSON Schema FABLES + DOC-A02; HF Job `6aa165be32d5d0c22c5b07df`: 4 passed in 0.09s;
   - ✅ auditoría física detectó R-003 ausente del code root aunque Handoff lo marcaba `EXISTING_COMPLETE`; se aplicó REUSE desde blob fuente `692daca7ace7ac983aeb585dd05ac281e571f2f3`;
   - ✅ `router inteligente universal/red/red_universal.py` commit `189a605fbccf703a81269d05777573c14acb68fb`, blob `66154b60ad53aa797094df8741389c8427f9bec0`;
   - ✅ test `tests/test_red_universal_r003.py` commit `b7ed873fa8c8b8f848d46c3fd1217206a51480c3`, blob `2be8bcf56fac0bb1c88b0f18edd0330538364726`; primer HF harness refutado por ruta plana; StrategyDelta preservó `red/tests`; HF Job `6aa16b68900620b5c77e7259`: 5 passed in 0.05s;
   - 🚩 GAP-BEHAVIOR-CONTRACT-001 permanece: schema/validator/perfiles no equivalen a policy standalone de comportamiento LLM; prohibido inferir/generar semántica del filtro;
   - ⏳ cola 1×1 siguiente: auditar C15 compatibilidad v1.5→v2.0 contra EnchufeV2/validator recuperados; PATCH únicamente si el delta exacto queda demostrado.
3. 📌✅ **Paso 3 — tests integración** — PENDING
   - Hugging Face + GitHub + API + agentes;
   - exigir ruta + SHA/diff + read-back + test/log.

Cola 1×1 actual: C15 audit → REUSE/PATCH solo con contrato demostrado → test → persistir; filtro LLM sigue fail-closed hasta policy explícita.
Reglas: no sobreingeniería; no añadir pasos; REUSE > PATCH > ADAPT > GENERATE; archivo presente ≠ integrado; unit/contract PASS ≠ E2E.
