# Readme Índice de modelos de AI Hugging Face

## Regla de verdad
Este índice registra únicamente modelos observados/validados. `CATALOG_OBSERVED` no significa `READY`.

## Evidencia actual
HF Job `6aa2513d5527934177ebfaad` (`cpu-upgrade`) enumeró exactamente 20 modelos públicos, no gated, `library=transformers`, `pipeline=text-generation`.
HF-M01 config/tokenizer/generation: Job `6aa26cc321047bf1b0371f28` COMPLETED.
HF-M01 inferencia local real: Job `6aa288a521047bf1b0372324` COMPLETED.
HF-M01 Enchufe/Router hot-path determinista: Job `6aa297195527934177ec0aed` COMPLETED, read-back desde `main`, `2 passed in 1.25s`, `RIU_HOT_PATH_TEST_RC 0`.

## Registry observado — 20 modelos
| Slot | model_id | especialidad | adapter | compute/acelerador | dataset/storage | FastAPI | estado |
|---|---|---|---|---|---|---|---|
| HF-M01 | Qwen/Qwen3-0.6B | text-generation/conversational | ENCHUFE_REDUNIVERSAL_BOUNDARY_TESTED | cpu-upgrade REAL_INFERENCE_VERIFIED | PENDING_BINDING | HOT_PATH_DETERMINISTIC_TESTED | DATASET_AUTH_PENDING |
| HF-M02 | openai-community/gpt2 | text-generation | PENDING | PENDING | PENDING | PENDING | CATALOG_OBSERVED |
| HF-M03 | Qwen/Qwen3-8B | text-generation | PENDING | PENDING | PENDING | PENDING | CATALOG_OBSERVED |
| HF-M04 | unsloth/Qwen3-Coder-30B-A3B-Instruct-GGUF | text-generation/code | PENDING | PENDING | PENDING | PENDING | CATALOG_OBSERVED |
| HF-M05 | Qwen/Qwen2.5-7B-Instruct | text-generation/instruct | PENDING | PENDING | PENDING | PENDING | CATALOG_OBSERVED |
| HF-M06 | facebook/opt-125m | text-generation | PENDING | PENDING | PENDING | PENDING | CATALOG_OBSERVED |
| HF-M07 | Qwen/Qwen2.5-1.5B-Instruct | text-generation/instruct | PENDING | PENDING | PENDING | PENDING | CATALOG_OBSERVED |
| HF-M08 | farbodtavakkoli/OTel-2.0-LLM-31B-IT | text-generation | PENDING | PENDING | PENDING | PENDING | CATALOG_OBSERVED |
| HF-M09 | openai/gpt-oss-20b | text-generation | PENDING | PENDING | PENDING | PENDING | CATALOG_OBSERVED |
| HF-M10 | Qwen/Qwen2.5-0.5B-Instruct | text-generation/instruct | PENDING | PENDING | PENDING | PENDING | CATALOG_OBSERVED |
| HF-M11 | Qwen/Qwen3-4B | text-generation | PENDING | PENDING | PENDING | PENDING | CATALOG_OBSERVED |
| HF-M12 | Qwen/Qwen2.5-3B-Instruct | text-generation/instruct | PENDING | PENDING | PENDING | PENDING | CATALOG_OBSERVED |
| HF-M13 | openai/gpt-oss-120b | text-generation | PENDING | PENDING | PENDING | PENDING | CATALOG_OBSERVED |
| HF-M14 | Qwen/Qwen3-32B | text-generation | PENDING | PENDING | PENDING | PENDING | CATALOG_OBSERVED |
| HF-M15 | dphn/dolphin-2.9.1-yi-1.5-34b | text-generation | PENDING | PENDING | PENDING | PENDING | CATALOG_OBSERVED |
| HF-M16 | deepseek-ai/DeepSeek-V4-Flash-0731 | text-generation | PENDING | PENDING | PENDING | PENDING | CATALOG_OBSERVED |
| HF-M17 | ornith-ai/Ornith-1.0-9B-GGUF | text-generation | PENDING | PENDING | PENDING | PENDING | CATALOG_OBSERVED |
| HF-M18 | ornith-ai/Ornith-1.5-9B-GGUF | text-generation | PENDING | PENDING | PENDING | PENDING | CATALOG_OBSERVED |
| HF-M19 | Qwen/Qwen-72B | text-generation | PENDING | PENDING | PENDING | PENDING | CATALOG_OBSERVED |
| HF-M20 | Qwen/Qwen2.5-7B-Instruct-AWQ | text-generation/instruct | PENDING | PENDING | PENDING | PENDING | CATALOG_OBSERVED |

## Cableado aprobado
`FastAPI gateway -> Enchufe Gate -> RedUniversal -> model registry/adapter -> Hugging Face -> verifier`.

## Siguiente cola 1×1
HF-M01: dataset/storage binding -> provider hosted autenticado por hot-path -> solo después READY y HF-M02.

## GAP privado
`GAP-HF-CATALOG-001` sigue abierto únicamente para catálogo privado de `COMAND-CENTER-1`; no bloquea validación pública 1×1.