# PLAN DE TAREAS — ROUTER INTELIGENTE UNIVERSAL

Contrato: `tel.workflow/v3` · modo `FAIL_CLOSED_LOOP`

## Lista única activa
1. 📌🛜 **Paso 1 — componentes + LLM/Hugging Face** — PARTIAL/CLOSED_SAFE
   - ✅ componentes movidos al code root;
   - ✅ bridge HF local auditado;
   - ✅ owner público HF: COUNT 0;
   - ✅ HF Jobs como cómputo real verificado previamente: Job `6aa1c5fd21047bf1b0370d4d`, `cpu-upgrade`, success;
   - ✅ RIU-0031 confirmó boundary de credencial: identidad conectada `COMAND-CENTER-1`; Job `6aa1d38621047bf1b0370f3f` completado con `public_model_count=0` y `hf_token_present=false`;
   - ✅ RIU-0032 reconfirmó cómputo real `cpu-upgrade`: Job `6aa24ea35527934177ebfa5c` COMPLETED con `HF_JOB_COMPUTE_OK`;
   - ❌ intento de catálogo del ciclo Job `6aa24e7921047bf1b0371acc` falló antes de producir inventario; no se promovió ningún `model_id`;
   - 🚩 GAP-HF-CATALOG-001 sigue OPEN: no afirmar privados/endpoints sin ruta segura de credencial y evidencia; no inventar adapters/FastAPI.
2. 📌 **Paso 2 — cableado + poda + código faltante** — ACTIVE
   - ✅ Gate/conectores/registry + validator/schema/RedUniversal + C15 verificados;
   - ✅ C10 Resilience verificado remotamente;
   - ✅ C11/C12/C13 `ADAPT_CANDIDATE/AUDIT_ONLY`;
   - 🚩 GAP-BEHAVIOR-CONTRACT-001 y demás GAPs contractuales siguen fail-closed.
3. 📌 **Paso 3 — API keys + tests integración** — PENDING
   - crear API Key Manager solo después del gateway/auth verificable;
   - keys distintas por agente, hash-only, revocación/rotación y `Authorization: Bearer <key>`;
   - test integral Hugging Face + GitHub + API + agentes con ruta + SHA/diff + read-back + log.

Cola 1×1 actual: continuar P02 independiente mientras GAP-HF-CATALOG-001 permanece abierto; reintentar catálogo HF únicamente mediante una ruta segura explícita de credencial/evidencia. `REUSE > PATCH > ADAPT > GENERATE`; no usar presencia física como PASS.
