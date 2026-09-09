# PLAN DE TAREAS — ROUTER INTELIGENTE UNIVERSAL

Contrato: `tel.workflow/v3` · modo `FAIL_CLOSED_LOOP`

## Lista única activa
1. 📌🛜 **Paso 1 — componentes + LLM/Hugging Face** — PARTIAL/CLOSED_SAFE
   - ✅ componentes movidos al code root;
   - ✅ bridge HF local auditado;
   - ✅ owner público HF: COUNT 0;
   - 🚩 GAP-HF-CATALOG-001: privados/endpoints sin `model_id` confirmado; no inventar adapters.
2. 📌 **Paso 2 — cableado + poda + código faltante** — ACTIVE
   - ✅ REUSE `red/conectores.py`; conectores HF/DB/GitLab/MCPApp/VPS/Memoria/Interno/Webhook + registry verificados;
   - ✅ `enchufe/validator_v2.py`, C05 `domain/schemas/enchufe_v2.py` y R-003 `red/red_universal.py` materializados/verificados desde fuentes canónicas;
   - ✅ C15 PATCH v1.5→v2.0 verificado; HF Job `6aa16ff732d5d0c22c5b0912` = `5 passed in 0.09s`;
   - ✅ C10 `engine/resilience.py` generado solo desde contrato explícito DOC-A02 + v6: R5 Retry + R6 Circuit Breaker; commit `6b408a781d886a8bde43c3f62b48247d872afd36`, blob `6a92375926909864d6fe604b4966b306a9aac449`; test commit `a0e74c04c93dfc2cc0c96da9c31234d98b44333c`; HF Job `6aa1ae8221047bf1b03707ff` = `5 passed in 0.10s`;
   - 🚩 GAP-BEHAVIOR-CONTRACT-001: prohibido inferir/generar policy LLM;
   - 🚩 GAP-R004-EXTRACTION-001: fuente Python exacta no materializada; no regenerar desde PDF/contrato;
   - 🚩 GAP-C03-CONTRACT-001: `pydantic-settings` es ADAPT_CANDIDATE, pero campos/env/defaults/perfiles no definidos;
   - ✅ C01 FastAPI donor auditado; auditoría commit `c8d297ed1046445c74190d6ba51bc1a39307462d`;
   - 🚩 GAP-C01-API-CONTRACT-001: faltan rutas/métodos/schemas/auth/error/WS de Paneles 1–5; no generar `api/` especulativo.
3. 📌✅ **Paso 3 — tests integración** — PENDING
   - Hugging Face + GitHub + API + agentes;
   - exigir ruta + SHA/diff + read-back + test/log.

Cola 1×1 actual: auditar el siguiente componente P02 independiente con contrato/source suficiente. Si existe reusable: `REUSE > PATCH > ADAPT`; `GENERATE` solo cuando la arquitectura/contrato lo definan explícitamente, como C10.
Reglas: no sobreingeniería; no añadir pasos; archivo presente ≠ integrado; donor capaz ≠ contrato del Router; unit/contract PASS ≠ E2E.
