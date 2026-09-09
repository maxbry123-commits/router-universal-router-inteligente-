# PLAN DE TAREAS — ROUTER INTELIGENTE UNIVERSAL

Contrato: `tel.workflow/v3` · modo `FAIL_CLOSED_LOOP`

## Lista única activa
1. 📌🛜 **Paso 1 — componentes + LLM/Hugging Face** — PARTIAL/CLOSED_SAFE
   - ✅ componentes movidos al code root;
   - ✅ bridge HF local auditado;
   - ✅ owner público HF: COUNT 0;
   - 🚩 GAP-HF-CATALOG-001: privados/endpoints sin `model_id` confirmado; no inventar adapters.
2. 📌 **Paso 2 — cableado + poda + código faltante** — ACTIVE
   - ✅ Gate/conectores/registry + validator/schema/RedUniversal + C15 verificados;
   - ✅ C10 Resilience generado únicamente desde contrato explícito y verificado remotamente;
   - ✅ RIU-0027 C11 Semantic Cache → `ADAPT_CANDIDATE/AUDIT_ONLY`;
   - ✅ RIU-0028 C12 Cost Optimizer → `ADAPT_CANDIDATE/AUDIT_ONLY`;
   - ✅ RIU-0029 C13 CodeSandbox dual: docker-py local validado → `ADAPT_CANDIDATE/AUDIT_ONLY`;
   - 🚩 GAP-BEHAVIOR-CONTRACT-001: prohibido inferir/generar policy LLM;
   - 🚩 GAP-R004-EXTRACTION-001: fuente Python exacta no materializada;
   - 🚩 GAP-C03-CONTRACT-001: campos/env/defaults/perfiles no definidos;
   - 🚩 GAP-C01-API-CONTRACT-001: contrato Paneles 1–5 no recuperado;
   - 🚩 GAP-C11-SEMANTIC-CACHE-CONTRACT-001: contrato semantic-cache incompleto;
   - 🚩 GAP-C12-COST-POLICY-CONTRACT-001: budget/cost policy Router incompleta;
   - 🚩 GAP-C13-SANDBOX-CONTRACT-001: faltan allowlists, recursos/red/fs, timeout/cancel, IO, secretos, paridad Docker↔subprocess, schema resultado y boundary Enchufe.
3. 📌✅ **Paso 3 — tests integración** — PENDING
   - Hugging Face + GitHub + API + agentes;
   - exigir ruta + SHA/diff + read-back + test/log.

Cola 1×1 actual: auditar el siguiente componente P02 independiente con contrato/source suficiente. Si existe reusable: `REUSE > PATCH > ADAPT`; `GENERATE` solo cuando la arquitectura/contrato lo definan explícitamente.
Reglas: no sobreingeniería; no añadir pasos; archivo presente ≠ integrado; donor capaz ≠ contrato del Router; unit/contract PASS ≠ E2E.
