# RIU-0091 — HF REMOTE 20 RECOVERY X-RAY

Contrato: `tel.workflow/v3` · modo `FAIL_CLOSED_LOOP` · fecha 2026-09-18.

## Hallazgo principal
Existieron **dos inventarios distintos de 20 modelos** y fueron mezclados posteriormente.

### A. Inventario REMOTO real del Router — RIU-HF-MODEL-REGISTRY-V2
Fuente Git: commit `fc61718c658b60a4f2b9ecbad3b0bfabf1c5847f`.
Fuente HF Router: `https://router.huggingface.co/v1/models`.
Jobs históricos:
- `6aa245235527934177ebf8aa` — enumeró 132 modelos remotos y fijó los primeros 20.
- `6aa245405527934177ebf8ac` — leyó metadata/sha/gated/private de esos mismos 20.

Fresh verification:
- Job `6aad0a2951992417dfcc6844` — el router remoto devolvió 139 modelos y **los 20 V2 siguen presentes; cada uno tiene al menos un provider live**.

| # | model_id | providers live observados fresh |
|---:|---|---|
| 1 | Qwen/Qwen3.8-27B | novita, cerebras, ovhcloud, deepinfra |
| 2 | deepseek-ai/DeepSeek-V4-Flash-Vision-Exp | novita, fireworks-ai, deepinfra |
| 3 | zai-org/GLM-5.3-Flash | novita, together, fireworks-ai, featherless-ai, zai-org, baseten, deepinfra |
| 4 | zai-org/GLM-5.3 | novita, together, fireworks-ai, featherless-ai, zai-org, baseten, deepinfra |
| 5 | inclusionAI/Ling-3.0-flash-Fin | novita, deepinfra |
| 6 | moonshotai/Kimi-K3 | together, fireworks-ai, featherless-ai, baseten, deepinfra |
| 7 | meta-llama/Llama-3.1-8B-Instruct | novita, nscale, featherless-ai, deepinfra |
| 8 | inclusionAI/Ling-3.0-flash-VL | novita, deepinfra |
| 9 | deepseek-ai/DeepSeek-V4-Flash-0731 | novita, together, fireworks-ai, featherless-ai, scaleway, baseten, deepinfra |
| 10 | prism-ml/Ternary-Bonsai-27B-gguf | together |
| 11 | meta-models/Muse-Glimmer-30B | together, fireworks-ai, featherless-ai, deepinfra |
| 12 | google/gemma-4-31B-it | novita, featherless-ai, deepinfra |
| 13 | openai/gpt-oss-120b | groq, novita, cerebras, nscale, together, fireworks-ai, featherless-ai, scaleway, baseten, ovhcloud, deepinfra |
| 14 | Qwen/Qwen3.6-35B-A3B | featherless-ai, scaleway, deepinfra |
| 15 | openai/gpt-oss-20b | groq, novita, nscale, featherless-ai, ovhcloud, deepinfra |
| 16 | deepseek-ai/DeepSeek-V4-Pro | novita, featherless-ai, baseten |
| 17 | deepseek-ai/DeepSeek-V4-Flash | novita, featherless-ai, deepinfra |
| 18 | Qwen/Qwen3.5-9B | together, featherless-ai, ovhcloud, deepinfra |
| 19 | inclusionAI/Ling-3.0-flash | novita, deepinfra |
| 20 | ibm-granite/granite-4.2-3b | deepinfra |

Clasificación actual de estos 20: `REMOTE_PROVIDER_DISCOVERY_VERIFIED`.
Esto prueba disponibilidad remota/provider live, **no todavía una inferencia autenticada PASS individual para cada uno**.

### B. Segundo catálogo de 20 — NO es el inventario remoto V2
Job `6aa2513d5527934177ebfaad` ejecutó una búsqueda pública por `pipeline_tag=text-generation`, ordenada por downloads y filtrada a public/nongated/transformers. Ese proceso produjo otra lista de 20 (Qwen3-0.6B, GPT-2, Qwen3-8B, etc.).
Commit `8ce5ceaa98fcf62c7b6ba2d47b067edaaa6b4d4e` reemplazó V2 con este catálogo y dejó explícito `CATALOG_OBSERVED != READY`.
Más tarde la certificación 20/20 mezcló pruebas de compute efímero en HF Jobs con esta segunda lista. No equivale a 20 rutas remotas provider-hosted.

### Evidencia de arquitectura remota
- `huggueface/manifest.yml`: `mode: REMOTE_ONLY`, `external_weights_persisted: false`.
- `huggueface/bridge/router_hf_bridge.py`: Hugging Face base `https://router.huggingface.co/v1`; chat usa `/chat/completions`.
- `integration/huggingface/huggingface_openai_chat.py`: usa `InferenceClient(token=HF_TOKEN).chat_completion(model=model_id,...)`.
- Bucket `COMAND-CENTER-1/yaiwes-v54`: `persistent_external_weights=false`, `weights_copy_count=0`; sólo manifiesto/evidencia.

### X-Ray de TAREA-1
`maxbry123-commits/TAREA-1` contiene resolución runtime de credenciales HF y un workflow de publicación de Space estático, pero no contiene `model_registry`, ni `router.huggingface.co`, ni el catálogo de 20 modelos remotos.

### GAP actual
El `model_registry.json` vigente V12 ya no contiene la clave `models`, pero `huggingface_openai_chat.py::allowed_model_ids()` todavía exige `_registry()["models"]`. El adapter remoto está por tanto desincronizado con el registry actual.

## Cierre del nodo
- REMOTE-20 histórico recuperado: PASS.
- Los 20 siguen presentes en HF Router y con provider live: PASS fresh.
- 20 inferencias autenticadas individuales: PENDING.
- Pesos persistentes en HF: 0 verificados; arquitectura REMOTE_ONLY preservada.
- Restauración/corrección del registry runtime: GAP; no se modifica ciegamente en este nodo.
