# PLAN DE TAREAS — ROUTER INTELIGENTE UNIVERSAL

Contrato: `tel.workflow/v3` · modo `FAIL_CLOSED_LOOP`

## Lista única activa
1. 📌🛜 **Paso 1 — componentes + LLM/Hugging Face** — PARTIAL/CLOSED_SAFE
   - ✅ componentes movidos al code root;
   - ✅ bridge HF local auditado;
   - ✅ owner público HF: COUNT 0;
   - ✅ HF Jobs como cómputo real verificado: Job `6aa1c5fd21047bf1b0370d4d`, `cpu-upgrade`, `success`;
   - ✅ RIU-0031 confirmó boundary de credencial: identidad conectada `COMAND-CENTER-1`; Job `6aa1d38621047bf1b0370f3f` completado con `public_model_count=0` y `hf_token_present=false`;
   - 🚩 GAP-HF-CATALOG-001 refinado: no afirmar privados/endpoints sin ruta de credencial segura y evidencia; no inventar adapters/FastAPI.
2. 📌 **Paso 2 — cableado + poda + código faltante** — ACTIVE
   - ✅ Gate/conectores/registry + validator/schema/RedUniversal + C15 verificados;
   - ✅ C10 Resilience verificado remotamente;
   - ✅ C11/C12/C13 `ADAPT_CANDIDATE/AUDIT_ONLY`;
   - 🚩 GAP-BEHAVIOR-CONTRACT-001 y demás GAPs contractuales siguen fail-closed.
3. 📌✅ **Paso 3 — tests integración** — PENDING
   - Hugging Face + GitHub + API + agentes;
   - exigir ruta + SHA/diff + read-back + test/log.

Cola 1×1 actual: continuar un componente P02 independiente con source/contrato suficiente. Reintentar catálogo privado HF solo si aparece una ruta segura explícita para credenciales/evidencia. `REUSE > PATCH > ADAPT > GENERATE`; no usar presencia física como PASS.
