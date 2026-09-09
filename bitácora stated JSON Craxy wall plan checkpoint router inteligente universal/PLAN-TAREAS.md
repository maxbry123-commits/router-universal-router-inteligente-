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
   - ✅ auditoría de recuperación del contrato del filtro LLM: README exige contrato definido/recuperado; Handoff referencia `enchufe/validator_v2.py`; esa ruta devuelve 404 en `main`; búsqueda de código no recuperó contrato explícito;
   - 🚩 GAP-BEHAVIOR-CONTRACT-001: prohibido generar semántica del filtro sin contrato;
   - ⏳ StrategyDelta cola 1×1: inspeccionar documentos fuente de verdad + donor local `guardrails` para recuperar contrato existente; si aparece, materializar detrás de guard/plugin y probar; si no, continuar solo tarea independiente segura P02.
3. 📌✅ **Paso 3 — tests integración** — PENDING
   - Hugging Face + GitHub + API + agentes;
   - exigir ruta + SHA/diff + read-back + test/log.

Cola 1×1 actual: recuperación contractual filtro LLM → REUSE/PATCH/ADAPT únicamente si existe contrato → guard/plugin → test → persistir.
Reglas: no sobreingeniería; no añadir pasos; REUSE > PATCH > ADAPT > GENERATE; archivo presente ≠ integrado.
