# PLAN DE TAREAS — ROUTER INTELIGENTE UNIVERSAL

Contrato: `tel.workflow/v3` · modo `FAIL_CLOSED_LOOP` · FAST-CLOSE.

## Lista única activa
1. 📌 **Paso 1 — Hugging Face completo** — ACTIVE · 99%
   - ✅ HF-M01/M02/M03: PASS internos preservados; provider/RW externos documentados.
   - ⚑ HF-M04: dos anomalías timeout-state; FLAG, no otra ventana larga.
   - ✅ HF-M05 integración real PASS.
   - ✅ HF-M06 `facebook/opt-125m`, M07 `Qwen/Qwen2.5-1.5B-Instruct`, M10 `Qwen/Qwen2.5-0.5B-Instruct`, M11 `Qwen/Qwen3-4B`, M12 `Qwen/Qwen2.5-3B-Instruct`: batch Job `6aa398fe5527934177ec4cd0` COMPLETED con verifier individual para cada modelo, dataset RO 10 files, summary SHA/read-back y `RIU_HF_BATCH_M06_M12_OK=True`.
   - 🔄 Siguiente: M08/M09/M13/M14/M15/M16/M17/M18/M19/M20 por compatibilidad/tamaño/scope; ejecutar compatibles y FLAG exacto lo externo/no ejecutable sin detener P01.
2. 📌 **Paso 2 — integración GitHub C01-C23** — cerrar sólo GAPs bloqueantes del hot-path real; no reauditar donors cerrados.
3. 📌 **Paso 3 — API Key Manager + E2E** — hasta 100 slots; sólo hash; create/verify/revoke/rotate/list; E2E real agente→key→FastAPI→Enchufe→Router→adapter→destino→verifier.

Cierre del core = 100% PASS de lo ejecutable + FLAGS externos explícitos; exigir ruta+SHA/read-back+test/log+URL.