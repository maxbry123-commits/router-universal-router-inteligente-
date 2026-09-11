# PLAN DE TAREAS — ROUTER INTELIGENTE UNIVERSAL

Contrato: `tel.workflow/v3` · modo `FAIL_CLOSED_LOOP` · FAST-CLOSE.

## Lista única activa
1. 📌 **Paso 1 — Hugging Face completo** — ACTIVE
   - ✅ Catálogo público 20 certificado.
   - ✅ HF-M01 compute + hot-path + dataset RO; provider auth sigue FLAG 403, NO READY externo.
   - ✅ HF-M02 compute + FastAPI→Enchufe→Router→adapter; storage RW sigue FLAG 403 externo.
   - ✅ HF-M03 compute + FastAPI→Enchufe→Router→adapter + dataset RO; storage RW persistente externo pendiente.
   - ⚑ HF-M04: dos Jobs cancelados por anomalía timeout-state; `FLAG-HF-M04-COMPUTE-001`; no consumir otra ventana larga.
   - ✅ HF-M05 `Qwen/Qwen2.5-7B-Instruct`: compute PASS + integración real PASS en Job `6aa3977e21047bf1b0374e94`; HTTP 200; dataset RO 10 files; CUDA; respuesta `RIU_HF_M05_ROUTE_OK`; SHA/read-back PASS; RW persistente queda GAP externo.
   - 🔄 Lote compatible siguiente: HF-M06 `facebook/opt-125m`, M07 `Qwen/Qwen2.5-1.5B-Instruct`, M10 `Qwen/Qwen2.5-0.5B-Instruct`, M11 `Qwen/Qwen3-4B`, M12 `Qwen/Qwen2.5-3B-Instruct` en una misma corrida; persistir resultado individual.
   - ⏳ M08/M09/M13-M20 después, usando ejecución compatible o FLAG exacto por tamaño/scope/provider.
2. 📌 **Paso 2 — integración GitHub C01-C23** — cerrar sólo GAPs que bloquean hot-path real; no reauditar donors cerrados.
3. 📌 **Paso 3 — API Key Manager + E2E** — hasta 100 slots; solo hash; revocar/rotar; E2E real.

Cierre del core no depende de proveedor externo probado como FLAG; exigir ruta+SHA/read-back+test/log+URL para lo ejecutable.