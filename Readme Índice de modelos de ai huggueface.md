# Readme Índice de modelos de AI Hugging Face

## Estado FAST-CLOSE RIU-0058
P01=`CLOSED_EXECUTABLE_SET`; el proyecto global quedó `VERIFIED_CLOSED 100%` sin convertir límites externos en PASS. `CATALOG_OBSERVED != READY` sigue aplicando a cualquier modelo no ejecutado/certificado.

- PASS preservados: M01-M03 internos, M05, M06/M07/M10/M11/M12, M20.
- M20 `Qwen/Qwen2.5-7B-Instruct-AWQ`: Job `6aa3a3cd5527934177ec4e7e` COMPLETED; response `OK`; SHA `5c45711905d5c34282a4711527ced24ede31e3390bf318285a01e8d78acf5302`; `HF_M20_OK=True`.
- M09 `openai/gpt-oss-20b`: Job `6aa3a3dd5527934177ec4e80` COMPLETED; SHA `43a490a128c6a64b845cd2397a881c2e85969d7a15db669a47f0b230f4bb4e68`; `content=null` con reasoning-only -> `FLAG-HF-M09-RESPONSE-CONTRACT-001`, no hot-path PASS.
- M17 `ornith-ai/Ornith-1.0-9B-GGUF`: Job `6aa3a24f5527934177ec4e3c` superó ventana corta y fue CANCELED -> `FLAG-HF-M17-TIMEOUT-001`.
- M18 `ornith-ai/Ornith-1.5-9B-GGUF`: no alcanzado en el job secuencial -> `FLAG-HF-M18-NOT_REACHED_DUE_M17_TIMEOUT-001`.
- M04, M08, M13-M16, M19, provider auth y RW-storage conservan sus FLAGS/GAP exactos en STATE.

## Cierre
Los FLAGS externos/runtime anteriores no bloquean el cierre del core ejecutable porque P02 hot-path y P03 E2E fueron verificados independientemente. No se afirma READY para ningún boundary externo.