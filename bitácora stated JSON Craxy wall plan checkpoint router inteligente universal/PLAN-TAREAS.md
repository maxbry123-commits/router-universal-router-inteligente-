# PLAN DE TAREAS — ROUTER INTELIGENTE UNIVERSAL

Contrato: `tel.workflow/v3` · modo `FAIL_CLOSED_LOOP`

## Lista única activa
1. 📌🛜 **Paso 1 — componentes + LLM/Hugging Face** — PARTIAL/CLOSED_SAFE
   - ✅ componentes movidos al code root;
   - ✅ bridge HF local auditado;
   - ✅ owner público HF: COUNT 0;
   - ✅ RIU-0030 verificó Hugging Face Jobs como cómputo real del proyecto: Job `6aa1c5fd21047bf1b0370d4d`, `cpu-upgrade`, resultado `success`, clonando/auditando el repo Router;
   - 🚩 GAP-HF-CATALOG-001: privados/endpoints sin `model_id` confirmado; no inventar adapters.
2. 📌 **Paso 2 — cableado + poda + código faltante** — ACTIVE
   - ✅ Gate/conectores/registry + validator/schema/RedUniversal + C15 verificados;
   - ✅ C10 Resilience generado únicamente desde contrato explícito y verificado remotamente;
   - ✅ C11/C12/C13 auditados como `ADAPT_CANDIDATE/AUDIT_ONLY`;
   - 🚩 GAP-BEHAVIOR-CONTRACT-001: prohibido inferir/generar policy LLM;
   - 🚩 GAP-R004-EXTRACTION-001, GAP-C03-CONTRACT-001, GAP-C01-API-CONTRACT-001, GAP-C11-SEMANTIC-CACHE-CONTRACT-001, GAP-C12-COST-POLICY-CONTRACT-001, GAP-C13-SANDBOX-CONTRACT-001 permanecen fail-closed.
3. 📌✅ **Paso 3 — tests integración** — PENDING
   - Hugging Face + GitHub + API + agentes;
   - exigir ruta + SHA/diff + read-back + test/log.

Cola 1×1 actual: continuar un componente P02 independiente con source/contrato suficiente. Si existe reusable: `REUSE > PATCH > ADAPT`; `GENERATE` solo cuando arquitectura/contrato lo definan explícitamente.
Reglas: no sobreingeniería; no añadir pasos; archivo presente ≠ integrado; donor capaz ≠ contrato del Router; HF Job success ≠ catálogo LLM ni E2E; unit/contract PASS ≠ E2E.
