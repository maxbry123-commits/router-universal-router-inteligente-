# PLAN DE TAREAS — ROUTER INTELIGENTE UNIVERSAL

Contrato: `tel.workflow/v3` · modo `FAIL_CLOSED_LOOP`

## Lista única activa
1. 📌 **Paso 1 — Hugging Face completo** — ACTIVE
   - ✅ Catálogo público 20 certificado.
   - ✅ HF-M01 compute + hot-path + dataset RO; provider auth sigue FLAG 403, NO READY.
   - ✅ HF-M02 compute real + dataset mount + FastAPI→Enchufe→Router→adapter; storage RW sigue FLAG 403, NO READY.
   - ✅ HF-M03 compute real + integración FastAPI→Enchufe→Router→adapter + dataset RO; storage RW persistente sigue PENDING/FLAG, NO READY.
   - ⚑ HF-M04 compute real: Jobs `6aa316585527934177ec29ee` y `6aa34d825527934177ec3d2c` cancelados tras anomalía timeout-state repetida sin inferencia final; FLAG, NO PASS.
   - 🔄 HF-M05 `Qwen/Qwen2.5-7B-Instruct`: Job `6aa3781121047bf1b0374a5c` lanzado en a10g-small, timeout 30m; NO PASS hasta COMPLETED+output.
   - ⏳ HF-M06..HF-M20 después.
2. 📌 **Paso 2 — integración GitHub C01-C23** — PENDING tras P01.
3. 📌 **Paso 3 — API keys agentes + E2E** — PENDING.

No promover por presencia/compute/hot-path parcial; exigir ruta+SHA/read-back+test/log+URL.