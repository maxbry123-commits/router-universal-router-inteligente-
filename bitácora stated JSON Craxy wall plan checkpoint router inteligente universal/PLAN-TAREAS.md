# PLAN DE TAREAS — ROUTER INTELIGENTE UNIVERSAL

Contrato: `tel.workflow/v3` · modo `FAIL_CLOSED_LOOP`

## Lista única activa
1. 📌 **Paso 1 — Hugging Face completo** — ACTIVE
   - ✅ Catálogo público 20 certificado.
   - ✅ HF-M01 config/tokenizer/generation + inferencia local real.
   - ✅ FastAPI -> Enchufe Gate -> RedUniversal -> HF adapter probado en Job `6aa297195527934177ec0aed` (`2 passed`).
   - ✅ Dataset/storage read-only binding: `HuggingFaceH4/ultrachat_200k` montado en Job `6aa2983921047bf1b03725eb`; binding OK.
   - ⚑ Provider hosted auth: Job `6aa2985921047bf1b03725ed` llegó al endpoint y devolvió 403 por permiso insuficiente; secreto redactado.
   - 🔄 HF-M01 NO READY hasta resolver permiso Inference Providers; outputs persistentes RW bucket no certificados.
   - ⏳ HF-M02..HF-M20: validación 1×1 después o como trabajo independiente seguro si el FLAG persiste.
2. 📌 **Paso 2 — integración GitHub C01-C23** — PENDING tras P01.
3. 📌 **Paso 3 — API keys agentes + E2E** — PENDING.

## Cola actual
Resolver `FLAG-HF-PROVIDER-AUTH-001` con credencial autorizada existente; si no está disponible, continuar solo validaciones P01 independientes sin promover HF-M01.