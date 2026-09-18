# RIU-0087 — HF REMOTE-INFERENCE TRUTH CORRECTION

Contrato: `tel.workflow/v3` · modo `FAIL_CLOSED_LOOP`.

## Regla autoritativa
Los modelos de AI Staff/Hugging Face NO se instalan ni se duplican como pesos persistentes en la cuenta. El Router consume modelos remotos mediante `huggingface_hub.InferenceClient`, Hugging Face Inference Providers o Endpoint remoto cuando corresponda. `RedUniversal` conserva ownership de routing.

## Evidencia runtime/código existente
- `router inteligente universal/integration/huggingface/huggingface_openai_chat.py`: lee `HF_TOKEN` sólo en runtime y ejecuta `InferenceClient.chat_completion(model=model_id, ...)`.
- `router inteligente universal/integration/huggingface/fastapi_gateway.py`: boundary HTTP -> EnchufeGate/RedUniversal -> HF adapter.
- `model_registry.json`: `gateway.base_url=https://router.huggingface.co/v1` y adapter canónico.

## Contradicciones detectadas
- RIU-0078 documentó `duplicate_repo`/`snapshot_download` como diseño de mirror/cache. Ese diseño no es la arquitectura de AI Staff y queda SUPERSEDED para integración normal de modelos.
- RIU-0085/0086 registró gates `download/hash/load` para WAN/LTX/Hunyuan/Kandinsky/Qwen-Image/FLUX. Esos gates son incorrectos para el contrato actual y deben migrarse a gates de inferencia remota.
- `MODEL_CERTIFICATION_20_OF_20_ACCOUNTED` significa catálogo/slots contabilizados, no 20 instalaciones.

## X-Ray de almacenamiento ya probado
- repos propios de modelos: 0 — HF Job `6aacb9175c02253cfb1461d1`.
- 5 Spaces auditados, sin pesos — Job `6aacc24d5c02253cfb14636e`.
- 2 buckets, 41 B y 1918 B, sin pesos — Job `6aacc21b5c02253cfb146365`.
- Inference Endpoints: UNKNOWN por 403 `inference.endpoints.read` — Job `6aacc20eb1dc2b62dc590800`; no inferir cero.
- Qwen3-0.6B, GPT-2 y Qwen3-8B fueron ejecutados/cargados en Jobs; eso es cómputo/cache efímero, no instalación persistente.

## Gate correcto por modelo
`REGISTER -> REMOTE_PROVIDER_DISCOVERY -> AUTH_REFERENCE -> REMOTE_INFERENCE_SMOKE -> FAILURE/FALLBACK_TEST -> EVIDENCE -> READY`.

Prohibido como ruta normal de AI Staff: `hf download`, `snapshot_download`, mirror/duplicate de pesos, bucket de pesos o cache persistente. Una materialización efímera dentro de un Job se etiqueta `EPHEMERAL_JOB_CACHE`, nunca `INSTALLED`.

## Auditoría abierta
1. Reconstruir historial HF Jobs y extraer cada `model_id`/provider llamado.
2. Cruzar con registry, índice HF, forensics y repo TAREA-1.
3. Clasificar: `REMOTE_CALL_VERIFIED`, `REMOTE_AUTH_GAP`, `CATALOG_ONLY`, `REQUESTED_PENDING_PROVIDER`, `EPHEMERAL_JOB_COMPUTE`.
4. Corregir gates download/mirror persistente restantes sin borrar evidencia histórica.
5. Probar modelos uno por uno por llamada remota y registrar respuesta/error verificable.

Estado: `ACTIVE_FORENSIC_REMOTE_MODEL_RECONSTRUCTION`; no global close.