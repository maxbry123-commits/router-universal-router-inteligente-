# PLAN DE TAREAS — ROUTER INTELIGENTE UNIVERSAL

Contrato: `tel.workflow/v3` · modo `FAIL_CLOSED_LOOP`

## Lista única activa
1. 📌 **Paso 1 — Hugging Face completo** — ACTIVE
   - ✅ Catálogo público 20 certificado.
   - ✅ HF-M01 compute + hot-path + dataset RO; provider auth sigue FLAG 403, NO READY.
   - ✅ HF-M02 compute real: Job `6aa2a4f25527934177ec0e01` COMPLETED.
   - ✅ HF-M02 dataset mount + FastAPI→Enchufe→Router→adapter: Job `6aa2cf4f21047bf1b0372e67` COMPLETED; mount True/16 files; HTTP 200; `FASTAPI_ENCHUFE_ROUTER_M02_OK=True`; 124439808 params.
   - 🔄 Cola 1×1: certificar Storage Bucket/output RW persistente HF-M02; hasta entonces HF-M02 NO READY.
   - ⏳ HF-M03..HF-M20 después.
2. 📌 **Paso 2 — integración GitHub C01-C23** — PENDING tras P01.
3. 📌 **Paso 3 — API keys agentes + E2E** — PENDING.

No promover por presencia/compute/hot-path parcial; exigir ruta+SHA/read-back+test/log+URL.