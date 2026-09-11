# Readme Índice de modelos de AI Hugging Face

## Regla de verdad
Este índice registra únicamente modelos observados/validados. `CATALOG_OBSERVED` no significa `READY`; FAST-CLOSE permite cerrar core con FLAGS externos demostrados.

## Evidencia actual
Catálogo público 20: HF Job `6aa2513d5527934177ebfaad`.
HF-M01/M02/M03: PASS internos previos; auth/provider/RW storage externos quedan FLAGS/GAP.
HF-M04: dos Jobs cancelados tras anomalía timeout-state; FLAG, NO PASS.
HF-M05: compute + integración real PASS.
HF-M06/M07/M10/M11/M12: batch Job `6aa398fe5527934177ec4cd0` COMPLETED; todos pasaron verifier individual detrás del mismo FastAPI→Enchufe→Router→HFAdapter; dataset RO True/10 files; summary SHA256 `c3b38014bdd5423cd85b42f14d54fc13c95247a0aa29e3729eb3ac84264dd6a5`; summary read-back True; `RIU_HF_BATCH_M06_M12_OK=True`.

## Registry observado — 20 modelos
| Slot | model_id | especialidad | adapter | compute/acelerador | dataset/storage | FastAPI | estado |
|---|---|---|---|---|---|---|---|
| HF-M01 | Qwen/Qwen3-0.6B | text-generation/conversational | ENCHUFE_REDUNIVERSAL_BOUNDARY_TESTED | REAL_INFERENCE_VERIFIED | RO_BINDING_VERIFIED | HOT_PATH_VERIFIED | CORE_PASS_PROVIDER_AUTH_FLAGGED |
| HF-M02 | openai-community/gpt2 | text-generation | ENCHUFE_ROUTER_ADAPTER_VERIFIED | REAL_INFERENCE_VERIFIED | RO_MOUNT_VERIFIED; RW_AUTH_FLAGGED | HTTP_200_HOT_PATH_VERIFIED | CORE_PASS_STORAGE_RW_FLAGGED |
| HF-M03 | Qwen/Qwen3-8B | text-generation/conversational | ENCHUFE_ROUTER_ADAPTER_VERIFIED | a10g-small REAL_INFERENCE_VERIFIED | RO_MOUNT_VERIFIED; RW_EXTERNAL_GAP | HTTP_200_HOT_PATH_VERIFIED | CORE_PASS_STORAGE_RW_FLAGGED |
| HF-M04 | unsloth/Qwen3-Coder-30B-A3B-Instruct-GGUF | text-generation/code | PENDING | two timeout-state anomalies; NO PASS | PENDING | PENDING | COMPUTE_FLAGGED |
| HF-M05 | Qwen/Qwen2.5-7B-Instruct | text-generation/instruct | ENCHUFE_ROUTER_ADAPTER_VERIFIED | REAL_INFERENCE_VERIFIED | RO_MOUNT_VERIFIED; RW_EXTERNAL_GAP | HTTP_200_HOT_PATH_VERIFIED | CORE_INTEGRATION_VERIFIED |
| HF-M06 | facebook/opt-125m | text-generation | ENCHUFE_ROUTER_ADAPTER_VERIFIED | a10g-small BATCH_REAL_INFERENCE_VERIFIED | ultrachat_200k RO_MOUNT_VERIFIED | HTTP_200_BATCH_VERIFIED | CORE_INTEGRATION_VERIFIED |
| HF-M07 | Qwen/Qwen2.5-1.5B-Instruct | text-generation/instruct | ENCHUFE_ROUTER_ADAPTER_VERIFIED | a10g-small BATCH_REAL_INFERENCE_VERIFIED | ultrachat_200k RO_MOUNT_VERIFIED | HTTP_200_BATCH_VERIFIED | CORE_INTEGRATION_VERIFIED |
| HF-M08 | farbodtavakkoli/OTel-2.0-LLM-31B-IT | text-generation | PENDING | PENDING | PENDING | PENDING | CATALOG_OBSERVED |
| HF-M09 | openai/gpt-oss-20b | text-generation | PENDING | PENDING | PENDING | PENDING | CATALOG_OBSERVED |
| HF-M10 | Qwen/Qwen2.5-0.5B-Instruct | text-generation/instruct | ENCHUFE_ROUTER_ADAPTER_VERIFIED | a10g-small BATCH_REAL_INFERENCE_VERIFIED | ultrachat_200k RO_MOUNT_VERIFIED | HTTP_200_BATCH_VERIFIED | CORE_INTEGRATION_VERIFIED |
| HF-M11 | Qwen/Qwen3-4B | text-generation | ENCHUFE_ROUTER_ADAPTER_VERIFIED | a10g-small BATCH_REAL_INFERENCE_VERIFIED | ultrachat_200k RO_MOUNT_VERIFIED | HTTP_200_BATCH_VERIFIED | CORE_INTEGRATION_VERIFIED |
| HF-M12 | Qwen/Qwen2.5-3B-Instruct | text-generation/instruct | ENCHUFE_ROUTER_ADAPTER_VERIFIED | a10g-small BATCH_REAL_INFERENCE_VERIFIED; Qwen2ForCausalLM; 3085938688 params | ultrachat_200k RO_MOUNT_VERIFIED | HTTP_200_BATCH_VERIFIED | CORE_INTEGRATION_VERIFIED |
| HF-M13 | openai/gpt-oss-120b | text-generation | PENDING | PENDING | PENDING | PENDING | CATALOG_OBSERVED |
| HF-M14 | Qwen/Qwen3-32B | text-generation | PENDING | PENDING | PENDING | PENDING | CATALOG_OBSERVED |
| HF-M15 | dphn/dolphin-2.9.1-yi-1.5-34b | text-generation | PENDING | PENDING | PENDING | PENDING | CATALOG_OBSERVED |
| HF-M16 | deepseek-ai/DeepSeek-V4-Flash-0731 | text-generation | PENDING | PENDING | PENDING | PENDING | CATALOG_OBSERVED |
| HF-M17 | ornith-ai/Ornith-1.0-9B-GGUF | text-generation | PENDING | PENDING | PENDING | PENDING | CATALOG_OBSERVED |
| HF-M18 | ornith-ai/Ornith-1.5-9B-GGUF | text-generation | PENDING | PENDING | PENDING | PENDING | CATALOG_OBSERVED |
| HF-M19 | Qwen/Qwen-72B | text-generation | PENDING | PENDING | PENDING | PENDING | CATALOG_OBSERVED |
| HF-M20 | Qwen/Qwen2.5-7B-Instruct-AWQ | text-generation/instruct | PENDING | PENDING | PENDING | PENDING | CATALOG_OBSERVED |

## Siguiente cola
M08/M09/M13-M20: clasificar por tamaño/flavor/scope, ejecutar compatibles y registrar FLAG exacto en no ejecutables/provider-only/gated; no atascar el proyecto.