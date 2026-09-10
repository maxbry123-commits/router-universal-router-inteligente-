# PLAN DE TAREAS — ROUTER INTELIGENTE UNIVERSAL

Contrato: `tel.workflow/v3` · modo `FAIL_CLOSED_LOOP`

## Lista única activa
1. 📌 **Paso 1 — Hugging Face completo** — ACTIVE
   - ✅ Catálogo público 20 certificado.
   - ✅ HF-M01 compute + hot-path + dataset RO; provider auth sigue FLAG 403, NO READY.
   - ✅ HF-M02 compute real + dataset mount + FastAPI→Enchufe→Router→adapter; storage RW sigue FLAG 403, NO READY.
   - ✅ HF-M03 `Qwen/Qwen3-8B` compute real: Job `6aa2ecbb21047bf1b037318e` COMPLETED; `Qwen3ForCausalLM`; 8190735360 params; `RIU_HF_M03_OK`; max GPU memory 16396255232.
   - 🔄 Cola 1×1: HF-M03 adapter + dataset/storage + FastAPI/Enchufe; hasta entonces HF-M03 NO READY.
   - ⏳ HF-M04..HF-M20 después.
2. 📌 **Paso 2 — integración GitHub C01-C23** — PENDING tras P01.
3. 📌 **Paso 3 — API keys agentes + E2E** — PENDING.

No promover por presencia/compute/hot-path parcial; exigir ruta+SHA/read-back+test/log+URL.