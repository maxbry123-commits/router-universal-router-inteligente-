# PLAN DE TAREAS — ROUTER INTELIGENTE UNIVERSAL
Contrato: `tel.workflow/v3` · `FAIL_CLOSED_LOOP` · FAST-CLOSE.
1. **Paso 1 — Hugging Face** — ACTIVE · 99%
   - ✅ M01-M03 preservados; M04 FLAG; M05 integrado; M06/M07/M10/M11/M12 batch integrado.
   - ⚑ M08/M13/M14/M15/M16/M19: FLAGS exactos para flavor/formato/provider actual.
   - ✅ M20 `Qwen/Qwen2.5-7B-Instruct-AWQ`: Job `6aa3a3cd5527934177ec4e7e` COMPLETED; vLLM; response `OK`; SHA `5c45711905d5c34282a4711527ced24ede31e3390bf318285a01e8d78acf5302`; `HF_M20_OK=True`.
   - 🔄 M09 Job `6aa3a3dd5527934177ec4e80`; M17/M18 Job `6aa3a24f5527934177ec4e3c`.
2. **Paso 2 — C01-C23** — sólo GAPs bloqueantes del hot-path real.
3. **Paso 3 — API Key Manager + E2E** — hasta 100 slots, sólo hash, create/verify/revoke/rotate/list.
Cierre = 100% PASS de lo ejecutable + FLAGS externos explícitos.