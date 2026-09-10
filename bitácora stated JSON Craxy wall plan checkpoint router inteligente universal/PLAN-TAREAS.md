# PLAN DE TAREAS — ROUTER INTELIGENTE UNIVERSAL

Contrato: `tel.workflow/v3` · modo `FAIL_CLOSED_LOOP`

## Lista única activa
1. 📌 **Paso 1 — Hugging Face completo** — ACTIVE
   - ✅ HF Jobs compute real verificado.
   - ✅ HF Job `6aa2513d5527934177ebfaad` enumeró exactamente 20 modelos públicos, no gated, `transformers`, `text-generation`.
   - ✅ HF-M01 `Qwen/Qwen3-0.6B`: metadata + `config.json` + `tokenizer_config.json` + `generation_config.json` validados con Job real `6aa26cc321047bf1b0371f28` COMPLETED.
   - 🔄 HF-M01 pendiente: serving compute/acelerador → dataset/storage → adapter → FastAPI → llamada real/read-back.
   - ⏳ HF-M02..HF-M20: repetir validación 1×1.
   - 🚩 catálogo privado sigue GAP separado; no bloquea el trabajo público.
2. 📌 **Paso 2 — integración GitHub C01-C23** — PENDING tras P01
   - cruzar donors locales; `REUSE > PATCH > ADAPT > GENERATE`; podar duplicados; cablear solo por Enchufe Universal; test + SHA + read-back.
3. 📌 **Paso 3 — API keys agentes + E2E** — PENDING
   - API Key Manager propio; hash-only; revocar/rotar; `Authorization: Bearer <key>`; entrega one-time; prueba agente→FastAPI→Router→HF/GitHub/API.

## Cola actual
`HF-M01 Qwen/Qwen3-0.6B` → cerrar serving real; no promover READY antes del hot path verificado. Después HF-M02 1×1.
