# PLAN DE TAREAS — ROUTER INTELIGENTE UNIVERSAL

Contrato: `tel.workflow/v3` · modo `FAIL_CLOSED_LOOP`

## Lista única activa
1. 📌 **Paso 1 — Hugging Face completo** — ACTIVE
   - ✅ Catálogo público 20 certificado.
   - ✅ HF-M01 config/tokenizer/generation + inferencia local real.
   - ✅ FastAPI -> Enchufe Gate -> RedUniversal -> HF adapter probado en Job `6aa297195527934177ec0aed` (`2 passed`).
   - ✅ Dataset/storage read-only binding: `HuggingFaceH4/ultrachat_200k` montado en Job `6aa2983921047bf1b03725eb`; binding OK.
   - ⚑ Provider hosted auth HF-M01: Job `6aa2985921047bf1b03725ed` llegó al endpoint y devolvió 403 por permiso insuficiente; secreto redactado.
   - ✅ HF-M02 `openai-community/gpt2` compute real: Job `6aa2a4f25527934177ec0e01` COMPLETED en `cpu-upgrade`; GPT2LMHeadModel, CPU, 124439808 parámetros runtime, generación real.
   - 🔄 Cola 1×1: HF-M02 dataset/storage + adapter/FastAPI; HF-M01 conserva FLAG y NO READY.
   - ⏳ HF-M03..HF-M20: validación 1×1 posterior como P01 independiente segura mientras persista el FLAG.
2. 📌 **Paso 2 — integración GitHub C01-C23** — PENDING tras P01.
3. 📌 **Paso 3 — API keys agentes + E2E** — PENDING.

## Cola actual
Validar HF-M02 dataset/storage + adapter/FastAPI detrás del Enchufe Universal. No promover HF-M01/HF-M02 por presencia o compute aislado; exigir evidencia del criterio correspondiente.