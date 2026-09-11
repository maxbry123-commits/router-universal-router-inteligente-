# Readme Índice de modelos de AI Hugging Face

## Estado FAST-CLOSE RIU-0053
P01=`CLOSED_EXECUTABLE_SET`; `CATALOG_OBSERVED != READY` y FLAGS externos no se convierten en PASS.

- PASS preservados: M01-M03 internos, M05, M06/M07/M10/M11/M12, M20.
- M20 `Qwen/Qwen2.5-7B-Instruct-AWQ`: Job `6aa3a3cd5527934177ec4e7e` COMPLETED; response `OK`; SHA `5c45711905d5c34282a4711527ced24ede31e3390bf318285a01e8d78acf5302`; `HF_M20_OK=True`.
- M09 `openai/gpt-oss-20b`: Job `6aa3a3dd5527934177ec4e80` COMPLETED y model_id exacto; SHA `43a490a128c6a64b845cd2397a881c2e85969d7a15db669a47f0b230f4bb4e68`; generación apareció sólo en `reasoning`, `content=null`, finish_reason=`length`; estado `REAL_COMPUTE_VERIFIED_RESPONSE_CONTRACT_FLAGGED`, no hot-path PASS.
- M17 `ornith-ai/Ornith-1.0-9B-GGUF`: StrategyDelta Job `6aa3a24f5527934177ec4e3c` excedió ventana 600s y fue CANCELED; `TIMEOUT_FLAGGED`.
- M18 `ornith-ai/Ornith-1.5-9B-GGUF`: era segundo nodo secuencial del mismo Job y no se afirma ejecutado; `NOT_REACHED_FLAGGED`.
- M04, M08, M13-M16, M19 y provider/RW storage conservan FLAGS/GAP exactos previamente documentados.

## Siguiente
P02 sólo bloqueantes físicos del hot-path; luego P03 API Key Manager + E2E real.