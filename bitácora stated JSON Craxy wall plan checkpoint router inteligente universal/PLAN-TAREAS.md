# PLAN DE TAREAS — ROUTER INTELIGENTE UNIVERSAL

Contrato: `tel.workflow/v3` · modo `FAIL_CLOSED_LOOP`

## Lista única activa
1. 📌 **Paso 1 — Hugging Face completo** — ACTIVE
   - ✅ HF Jobs compute real verificado.
   - ✅ Catálogo público de 20 modelos certificado por Job `6aa2513d5527934177ebfaad`.
   - ✅ HF-M01 metadata/config/tokenizer/generation validados por Job `6aa26cc321047bf1b0371f28`.
   - ✅ Adapter `huggingface_openai_chat.py` materializado y read-back verificado.
   - ✅ Gateway FastAPI único `fastapi_gateway.py` materializado y read-back verificado.
   - 🔄 HF-M01 pendiente: runtime inference + Enchufe/Router hot path + dataset/storage + acelerador.
   - ⏳ HF-M02..HF-M20: repetir validación 1×1.
2. 📌 **Paso 2 — integración GitHub C01-C23** — PENDING tras P01
   - `REUSE > PATCH > ADAPT > GENERATE`; no monolito; Enchufe Universal obligatorio.
3. 📌 **Paso 3 — API keys agentes + E2E** — PENDING
   - hash-only; revocar/rotar; Bearer; entrega one-time; E2E real.

## Cola actual
`HF-M01 Qwen/Qwen3-0.6B` → runtime inference + Enchufe/Router + dataset/storage → solo después HF-M02.
