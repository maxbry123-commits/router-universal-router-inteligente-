# PLAN DE TAREAS — ROUTER INTELIGENTE UNIVERSAL

Contrato: `tel.workflow/v3` · modo `FAIL_CLOSED_LOOP` · FAST-CLOSE.

## Lista única activa
1. 📌 **Paso 1 — Hugging Face completo** — ACTIVE · 99%
   - ✅ HF-M01/M02/M03 preservados; provider/RW externos documentados.
   - ⚑ HF-M04 FLAG tras dos anomalías timeout-state; no otra ventana larga.
   - ✅ HF-M05 integración real PASS.
   - ✅ HF-M06/M07/M10/M11/M12 batch Job `6aa398fe5527934177ec4cd0` PASS con verifier individual + SHA/read-back.
   - ⚑ HF-M08/M13/M14/M15/M16/M19: FLAG exacto para `a10g-small`/formato observado por tamaño o ruta provider no autorizada; no se declara imposibilidad global.
   - 🔄 HF-M17/M18 GGUF: primer Job `6aa3a1875527934177ec4e06` falló exit127; probe halló `/app/llama-cli`; StrategyDelta Job `6aa3a24f5527934177ec4e3c` RUNNING.
   - 🔄 HF-M09 `openai/gpt-oss-20b` MXFP4 y HF-M20 `Qwen/Qwen2.5-7B-Instruct-AWQ` 4-bit: candidatos locales; vLLM smoke inicial falló por `python` fuera de PATH y probe `6aa3a2cb5527934177ec4e50` está lanzado.
2. 📌 **Paso 2 — integración GitHub C01-C23** — cerrar sólo GAPs bloqueantes del hot-path real; no reauditar donors cerrados.
3. 📌 **Paso 3 — API Key Manager + E2E** — hasta 100 slots; sólo hash; create/verify/revoke/rotate/list; E2E real agente→key→FastAPI→Enchufe→Router→adapter→destino→verifier.

Cierre del core = 100% PASS de lo ejecutable + FLAGS externos explícitos; exigir ruta+SHA/read-back+test/log+URL.