# Readme Índice de modelos de AI Hugging Face — inventario corregido

## Regla de verdad
`ROUTER_REGISTERED != ACCOUNT_INSTALLED` y `CATALOG_OBSERVED != REMOTE_CALL_VERIFIED != READY`.

La certificación histórica de 20 slots del Router **no es un inventario de modelos instalados en la cuenta Hugging Face**. Los pesos del AI Staff no deben duplicarse ni persistirse en la cuenta: el Router los consume por inferencia remota.

## Arquitectura autoritativa de modelos
`RedUniversal -> connector_registry -> HF adapter/InferenceClient -> Hugging Face Inference Provider o Endpoint remoto -> modelo -> respuesta`.

Gate correcto por modelo:
`REGISTER -> REMOTE_PROVIDER_DISCOVERY -> AUTH_REFERENCE -> REMOTE_INFERENCE_SMOKE -> FAILURE/FALLBACK_TEST -> EVIDENCE -> READY`.

Ruta normal prohibida para AI Staff: `hf download`, `snapshot_download`, mirror/duplicate de pesos, bucket de pesos o cache persistente. Un cache efímero de HF Job se clasifica `EPHEMERAL_JOB_CACHE`, nunca `INSTALLED`.

## Registro activo / evidencia histórica
### REMOTE/COMPUTE verificado parcialmente
- `Qwen/Qwen3-0.6B` — inferencia real en HF Job; provider auth del boundary remoto sigue flaggeado.
- `openai-community/gpt2` — inferencia/integración Job verificada; no equivale a instalación persistente.
- `Qwen/Qwen3-8B` — cómputo GPU real verificado; adapter/provider remoto aún no READY.

### CATALOG_ONLY
- `Qwen/Qwen2.5-7B-Instruct`
- `Qwen/Qwen2.5-1.5B-Instruct`
- `farbodtavakkoli/OTel-2.0-LLM-31B-IT`
- `openai/gpt-oss-20b`

### REQUESTED_PENDING_PROVIDER — Video / Animation
- `Wan-AI/Wan2.2-Animate-14B` — Apache-2.0; metadata/revisión conocida; falta provider discovery + llamada remota.
- `Lightricks/LTX-Video` — licencia `other`; validar términos + provider discovery + llamada remota.
- `tencent/HunyuanVideo` — licencia `other`; validar términos + provider discovery + llamada remota.

### REQUESTED_PENDING_PROVIDER — Image / Design
- `kandinskylab/Kandinsky-5.0-T2I-Lite-sft-Diffusers` — MIT; falta provider discovery + llamada remota.
- `Qwen/Qwen-Image` — Apache-2.0; falta provider discovery + llamada remota.
- `black-forest-labs/FLUX.1-schnell` — Apache-2.0, gated; falta auth/provider discovery + llamada remota.

## Catálogo histórico retirado del registro activo
Estos IDs aparecieron en catálogo/Jobs históricos pero no se promueven sin evidencia fresh de llamada remota:
- `unsloth/Qwen3-Coder-30B-A3B-Instruct-GGUF`
- `facebook/opt-125m`
- `Qwen/Qwen2.5-0.5B-Instruct`
- `Qwen/Qwen3-4B`
- `Qwen/Qwen2.5-3B-Instruct`
- `openai/gpt-oss-120b`
- `Qwen/Qwen3-32B`
- `dphn/dolphin-2.9.1-yi-1.5-34b`
- `deepseek-ai/DeepSeek-V4-Flash-0731`
- `ornith-ai/Ornith-1.0-9B-GGUF`
- `ornith-ai/Ornith-1.5-9B-GGUF`
- `Qwen/Qwen-72B`
- `Qwen/Qwen2.5-7B-Instruct-AWQ`

## X-Ray persistente verificado
- Cuenta autenticada: `COMAND-CENTER-1`.
- Repos propios de modelos: **0**, Job `6aacb9175c02253cfb1461d1`.
- Mirrors persistentes verificados: **0**.
- Instalaciones locales persistentes verificadas: **0**.
- Spaces auditados: **5**, sin pesos de modelo, Job `6aacc24d5c02253cfb14636e`.
- Buckets: **2**, 41 B y 1918 B, sin pesos, Job `6aacc21b5c02253cfb146365`.
- Inference Endpoints: **UNKNOWN/GAP_PERMISSION** por 403 `inference.endpoints.read`, Job `6aacc20eb1dc2b62dc590800`; no inferir cero.

## Auditoría abierta
Reconstruir historial completo de HF Jobs y clasificar cada model_id como `REMOTE_CALL_VERIFIED`, `REMOTE_AUTH_GAP`, `CATALOG_ONLY`, `REQUESTED_PENDING_PROVIDER` o `EPHEMERAL_JOB_COMPUTE`; cruzar con registry, forensics y TAREA-1. No declarar PASS por presencia.