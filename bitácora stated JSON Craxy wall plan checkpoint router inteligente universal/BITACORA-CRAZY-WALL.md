# BITÁCORA CRAZY WALL — ROUTER INTELIGENTE UNIVERSAL

**Contrato:** `tel.workflow/v3` · **Modo:** `FAIL_CLOSED_LOOP`.

## RIU-0087 — HF REMOTE-INFERENCE TRUTH CORRECTION — ACTIVE
- Regla autoritativa: los modelos de AI Staff/Hugging Face **NO se instalan ni se duplican como pesos persistentes en la cuenta**. El Router consume modelos remotos por `huggingface_hub.InferenceClient`, Hugging Face Inference Providers o Endpoint remoto cuando corresponda.
- Boundary existente confirmado en código: `FastAPI -> EnchufeGate -> RedUniversal -> HFAdapter -> InferenceClient -> provider/model remoto`. `RedUniversal` conserva ownership de routing.
- Evidencia de código: `router inteligente universal/integration/huggingface/huggingface_openai_chat.py` lee `HF_TOKEN` en runtime y llama `InferenceClient.chat_completion(model=model_id, ...)`; `fastapi_gateway.py` mantiene el hot-path detrás de RedUniversal.
- Contradicción detectada: RIU-0078 documentó `duplicate_repo`/`snapshot_download` como diseño y RIU-0085/0086 dejó gates `download/hash/load`; esos gates **no son el método de integración de AI Staff** y quedan SUPERSEDED para modelos remotos.
- Evidencia de almacenamiento ya auditada: owned model repos=0 (Job `6aacb9175c02253cfb1461d1`); 5 Spaces sin pesos (Job `6aacc24d5c02253cfb14636e`); 2 buckets de 41 B/1918 B sin pesos (Job `6aacc21b5c02253cfb146365`). Endpoints permanece UNKNOWN por 403 de permiso `inference.endpoints.read` (Job `6aacc20eb1dc2b62dc590800`), por lo que no se infiere cero.
- Modelos ejecutados históricamente en Jobs (`Qwen/Qwen3-0.6B`, `openai-community/gpt2`, `Qwen/Qwen3-8B`) prueban ejecución/carga efímera, **no instalación persistente**.
- Gate correcto por modelo: `REGISTER -> REMOTE_PROVIDER_DISCOVERY -> AUTH_REFERENCE -> REMOTE_INFERENCE_SMOKE -> FAILURE/FALLBACK_TEST -> EVIDENCE -> READY`.
- Prohibido como ruta normal: `hf download`, `snapshot_download`, mirror/duplicate de pesos, bucket de pesos o cache persistente. Si una prueba efímera de Job materializa cache, se clasifica `EPHEMERAL_JOB_CACHE`, no instalación.
- Inventario histórico de 20 slots se audita como catálogo/registro de llamadas remotas; `MODEL_CERTIFICATION_20_OF_20_ACCOUNTED` no equivale a 20 instalaciones.

### Auditoría X-Ray abierta
1. Reconstruir historial HF Jobs y extraer todos los `model_id`/provider realmente llamados, deduplicados, con job/evidencia.
2. Cruzar esos IDs con `model_registry.json`, README índice HF, forensics y notas de TAREA-1.
3. Clasificar cada modelo: `REMOTE_CALL_VERIFIED`, `REMOTE_AUTH_GAP`, `CATALOG_ONLY`, `REQUESTED_PENDING_PROVIDER`, `EPHEMERAL_JOB_COMPUTE`.
4. Corregir cualquier gate de descarga/mirror persistente restante sin borrar evidencia histórica.
5. Probar integración remota uno por uno; PASS sólo con respuesta real o error remoto verificable y evidencia.

Estado: `ACTIVE_FORENSIC_REMOTE_MODEL_RECONSTRUCTION`; cierre global prohibido mientras falte reconstruir los 20+ modelos históricos y sincronizar STATE/PLAN/CHECKPOINT/Handoff.
