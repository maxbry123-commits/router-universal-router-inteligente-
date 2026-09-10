# PLAN DE TAREAS — ROUTER INTELIGENTE UNIVERSAL

Contrato: `tel.workflow/v3` · modo `FAIL_CLOSED_LOOP`

## Lista única activa
1. 📌 **Paso 1 — Hugging Face completo** — ACTIVE
   - ✅ HF Jobs compute real verificado.
   - ✅ Catálogo público de 20 modelos certificado por Job `6aa2513d5527934177ebfaad`.
   - ✅ HF-M01 metadata/config/tokenizer/generation validados por Job `6aa26cc321047bf1b0371f28`.
   - ✅ HF-M01 inferencia local real en HF Job `6aa288a521047bf1b0372324`: `RIU_HF_M01_OK`, CPU, 596049920 parámetros runtime, 7.108s.
   - ✅ Adapter `huggingface_openai_chat.py` materializado y read-back verificado.
   - ✅ Gateway FastAPI único `fastapi_gateway.py` materializado y read-back verificado.
   - 🔄 HF-M01 pendiente: Enchufe/Router hot path + dataset/storage; hosted provider auth sigue separado.
   - ⏳ HF-M02..HF-M20: repetir validación 1×1.
2. 📌 **Paso 2 — integración GitHub C01-C23** — PENDING tras P01
   - `REUSE > PATCH > ADAPT > GENERATE`; no monolito; Enchufe Universal obligatorio.
3. 📌 **Paso 3 — API keys agentes + E2E** — PENDING
   - hash-only; revocar/rotar; Bearer; entrega one-time; E2E real.

## Cola actual
`HF-M01 Qwen/Qwen3-0.6B` → FastAPI→Enchufe→Router + dataset/storage → solo después HF-M02.
