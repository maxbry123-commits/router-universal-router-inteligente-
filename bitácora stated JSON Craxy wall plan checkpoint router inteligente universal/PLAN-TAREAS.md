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
   - 🚩 GAP-BEHAVIOR-CONTRACT-001: prohibido inferir/generar policy LLM;
   - 🚩 GAP-R004-EXTRACTION-001: fuente Python exacta no materializada; no regenerar desde PDF/contrato;
   - 🚩 GAP-C03-CONTRACT-001: `pydantic-settings` es ADAPT_CANDIDATE, pero campos/env/defaults/perfiles no definidos;
   - ✅ C01 FastAPI donor auditado: local `fastapi/pyproject.toml` blob `06c82344a7010eefaf98f567468dea8be5a5ae10`, MIT, upstream `https://github.com/fastapi/fastapi`; auditoría commit `c8d297ed1046445c74190d6ba51bc1a39307462d`;
   - 🚩 GAP-C01-API-CONTRACT-001: faltan rutas/métodos/schemas/auth/error/WS de Paneles 1–5; no generar `api/` especulativo.
3. 📌✅ **Paso 3 — tests integración** — PENDING
   - Hugging Face + GitHub + API + agentes;
   - exigir ruta + SHA/diff + read-back + test/log.

Cola 1×1 actual: auditar el siguiente componente P02 independiente con contrato/source suficiente. Si existe reusable: `REUSE > PATCH > ADAPT`; solo `GENERATE` cuando la arquitectura lo autorice y el contrato esté completo.
Reglas: no sobreingeniería; no añadir pasos; archivo presente ≠ integrado; donor capaz ≠ contrato del Router; unit/contract PASS ≠ E2E.
