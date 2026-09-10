# Readme Índice de modelos de AI Hugging Face

## Regla de verdad
Este índice registra únicamente modelos observados/validados. `CATALOG_OBSERVED` no significa `READY`.

## Evidencia actual
Catálogo público 20: HF Job `6aa2513d5527934177ebfaad`.
HF-M01 compute/hot-path/dataset RO verificados; provider auth Job `6aa2985921047bf1b03725ed` ERROR 403; NO READY.
HF-M02 compute real: Job `6aa2a4f25527934177ec0e01` COMPLETED.
HF-M02 integración: Job `6aa2cf4f21047bf1b0372e67` COMPLETED; repo ZIP SHA256 `033a19f379e56f3a23bcad488af9089bc6f9a2e1fae25df6dd17a06bee8412df`; dataset mount True/16 files; HTTP 200; `FASTAPI_ENCHUFE_ROUTER_M02_OK=True`; GPT2LMHeadModel; 124439808 params.

## Registry observado — 20 modelos
| Slot | model_id | especialidad | adapter | compute/acelerador | dataset/storage | FastAPI | estado |
|---|---|---|---|---|---|---|---|
| HF-M01 | Qwen/Qwen3-0.6B | text-generation/conversational | ENCHUFE_REDUNIVERSAL_BOUNDARY_TESTED | cpu-upgrade REAL_INFERENCE_VERIFIED | ultrachat_200k RO_BINDING_VERIFIED | HOT_PATH_DETERMINISTIC_TESTED | PROVIDER_AUTH_FLAGGED |
| HF-M02 | openai-community/gpt2 | text-generation | ENCHUFE_ROUTER_ADAPTER_VERIFIED | cpu-upgrade REAL_INFERENCE_VERIFIED | DATASET_RO_MOUNT_VERIFIED; RW_STORAGE_PENDING | HTTP_200_HOT_PATH_VERIFIED | INTEGRATION_VERIFIED_STORAGE_RW_PENDING |
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

## Siguiente cola 1×1
Certificar Storage Bucket/output RW persistente HF-M02. HF-M01 mantiene `FLAG-HF-PROVIDER-AUTH-001`; ambos siguen NO READY.