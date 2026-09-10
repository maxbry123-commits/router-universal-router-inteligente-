# PLAN DE TAREAS — ROUTER INTELIGENTE UNIVERSAL

Contrato: `tel.workflow/v3` · modo `FAIL_CLOSED_LOOP`

## Lista única activa
1. 📌 **Paso 1 — Hugging Face completo** — ACTIVE
   - ✅ Catálogo público 20 certificado.
   - ✅ HF-M01 compute + hot-path + dataset RO; provider auth sigue FLAG 403, NO READY.
   - ✅ HF-M02 compute real + dataset mount + FastAPI→Enchufe→Router→adapter; storage RW sigue FLAG 403, NO READY.
   - ✅ HF-M03 compute real + integración FastAPI→Enchufe→Router→adapter + dataset RO: Job `6aa2f8e921047bf1b03732b7` COMPLETED; HTTP 200; `RIU_HF_M03_ROUTE_OK`; storage RW persistente sigue PENDING/FLAG, NO READY.
   - 🔄 Cola 1×1: HF-M04 compute real.
   - ⏳ HF-M05..HF-M20 después.
2. 📌 **Paso 2 — integración GitHub C01-C23** — PENDING tras P01.
3. 📌 **Paso 3 — API keys agentes + E2E** — PENDING.

No promover por presencia/compute/hot-path parcial; exigir ruta+SHA/read-back+test/log+URL.