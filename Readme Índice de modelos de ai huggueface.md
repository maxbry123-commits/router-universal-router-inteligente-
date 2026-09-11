# Readme Índice de modelos de AI Hugging Face

## Regla de verdad
Este índice registra únicamente modelos observados/validados. `CATALOG_OBSERVED` no significa `READY`; FAST-CLOSE permite cerrar core con FLAGS externos demostrados.

## Evidencia actual
Catálogo público 20: HF Job `6aa2513d5527934177ebfaad`.
HF-M01/M02/M03: PASS internos previos; auth/provider/RW storage externos quedan FLAGS/GAP.
HF-M04: dos Jobs cancelados tras anomalía timeout-state; FLAG, NO PASS.
HF-M05 `Qwen/Qwen2.5-7B-Instruct`: compute Job `6aa3781121047bf1b0374a5c` PASS + integración Job `6aa3977e21047bf1b0374e94` COMPLETED; HTTP 200; dataset RO True/10 files; CUDA True; response `RIU_HF_M05_ROUTE_OK`; SHA256 `d3352d066152f07379352c94eaae94dd415be1adcda68b43791f8736c9653e79`; read-back True; `FASTAPI_ENCHUFE_ROUTER_M05_OK=True`; persistent RW storage external GAP.

## Registry observado — 20 modelos
| Slot | model_id | especialidad | adapter | compute/acelerador | dataset/storage | FastAPI | estado |
|---|---|---|---|---|---|---|---|
| HF-M01 | Qwen/Qwen3-0.6B | text-generation/conversational | ENCHUFE_REDUNIVERSAL_BOUNDARY_TESTED | cpu-upgrade REAL_INFERENCE_VERIFIED | ultrachat_200k RO_BINDING_VERIFIED | HOT_PATH_DETERMINISTIC_TESTED | CORE_PASS_PROVIDER_AUTH_FLAGGED |
| HF-M02 | openai-community/gpt2 | text-generation | ENCHUFE_ROUTER_ADAPTER_VERIFIED | cpu-upgrade REAL_INFERENCE_VERIFIED | Salesforce/wikitext RO_MOUNT_VERIFIED; RW_STORAGE_AUTH_FLAGGED | HTTP_200_HOT_PATH_VERIFIED | CORE_PASS_STORAGE_RW_FLAGGED |
| HF-M03 | Qwen/Qwen3-8B | text-generation/conversational | ENCHUFE_ROUTER_ADAPTER_VERIFIED | a10g-small REAL_INFERENCE_VERIFIED | ultrachat_200k RO_MOUNT_VERIFIED; RW_STORAGE_EXTERNAL_GAP | HTTP_200_HOT_PATH_VERIFIED | CORE_PASS_STORAGE_RW_FLAGGED |
| HF-M04 | unsloth/Qwen3-Coder-30B-A3B-Instruct-GGUF | text-generation/code | PENDING | a10g-small llama.cpp CUDA; two timeout-state anomalies; NO PASS | PENDING | PENDING | COMPUTE_FLAGGED |
| HF-M05 | Qwen/Qwen2.5-7B-Instruct | text-generation/instruct | ENCHUFE_ROUTER_ADAPTER_VERIFIED | a10g-small REAL_INFERENCE_VERIFIED | ultrachat_200k RO_MOUNT_VERIFIED; RW_STORAGE_EXTERNAL_GAP | HTTP_200_HOT_PATH_VERIFIED | CORE_INTEGRATION_VERIFIED |
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

## Siguiente cola
Batch compatible M06/M07/M10/M11/M12 en una corrida HF Job; persistir evidencia individual. M08/M09/M13-M20 después por compatibilidad/tamaño/scope, registrando FLAG exacto sin atascar el proyecto.