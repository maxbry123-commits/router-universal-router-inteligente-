# PLAN DE TAREAS — ROUTER INTELIGENTE UNIVERSAL

Contrato: `tel.workflow/v3` · modo `FAIL_CLOSED_LOOP`

## Lista única activa
1. 📌 **Paso 1 — Hugging Face completo** — ACTIVE
   - ✅ Catálogo público 20 certificado.
   - ✅ HF-M01 compute + hot-path + dataset RO; provider auth sigue FLAG 403, NO READY.
   - ✅ HF-M02 compute real: Job `6aa2a4f25527934177ec0e01` COMPLETED.
   - ✅ HF-M02 dataset mount + FastAPI→Enchufe→Router→adapter: Job `6aa2cf4f21047bf1b0372e67` COMPLETED; mount True/16 files; HTTP 200; `FASTAPI_ENCHUFE_ROUTER_M02_OK=True`; 124439808 params.
   - ⚑ HF-M02 Storage Bucket RW: Job `6aa2ebc15527934177ec1eb6` ERROR 403; secreto autorizado no expuesto, credencial actual sin permiso bucket write/create; `FLAG-HF-M02-RW-STORAGE-AUTH-001`; HF-M02 NO READY.
   - 🔄 Cola 1×1: HF-M03 real compute; mantener FLAGs HF-M01/HF-M02 abiertos.
   - ⏳ HF-M04..HF-M20 después.
2. 📌 **Paso 2 — integración GitHub C01-C23** — PENDING tras P01.
3. 📌 **Paso 3 — API keys agentes + E2E** — PENDING.

No promover por presencia/compute/hot-path parcial; exigir ruta+SHA/read-back+test/log+URL.