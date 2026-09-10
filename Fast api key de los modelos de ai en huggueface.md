# Fast API key de los modelos de AI en Hugging Face

## Propósito
Controlar el acceso de agentes al gateway FastAPI del Router sin publicar secretos en GitHub.

## Arquitectura
`AGENTE -> Authorization: Bearer <router_api_key> -> FastAPI -> APIKeyGuard -> Enchufe Gate -> RedUniversal -> model registry -> adapter -> Hugging Face`

## Regla de seguridad
Las API keys reales NO se guardan en este archivo ni en ningún commit. El Router debe guardar solo hash/metadata; plaintext una sola vez.

## Estado actual
- Gateway FastAPI único + Enchufe Gate + RedUniversal: hot-path determinista HF-M01 verificado.
- HF-M02 FastAPI→Enchufe→Router→adapter validado en Job `6aa2cf4f21047bf1b0372e67`; storage RW sigue FLAG 403; HF-M02 NO READY.
- HF-M03 `Qwen/Qwen3-8B` FastAPI→Enchufe→Router→adapter + dataset RO validado en Job `6aa2f8e921047bf1b03732b7`; HTTP 200, `RIU_HF_M03_ROUTE_OK`, `Qwen3ForCausalLM`, 8190735360 params, CUDA True; storage RW persistente sigue PENDING; HF-M03 NO READY.
- Provider hosted auth HF-M01: `FLAG-HF-PROVIDER-AUTH-001` por 403 de Inference Providers.
- APIKeyGuard/API Key Manager: PENDING Paso 3.
- `PLAINTEXT_KEYS: NOT_GENERATED_YET`.

## Formato objetivo de key
`riu_<agent_id>_<random-secret>`

## Operaciones requeridas
create/verify/revoke/rotate/list; persistir solo `key_id`, `agent_id`, `key_hash`, timestamps, status, scopes y allowed_models.

## Endpoints objetivo
`POST /v1/keys`, `POST /v1/keys/{key_id}/rotate`, `DELETE /v1/keys/{key_id}`, `GET /v1/models`, `POST /v1/chat/completions`.

## Criterio PASS
Key válida -> routing permitido; revocada/inválida -> 401/403; scope inválido -> 403; ningún secreto en logs/GitHub/STATE/BITACORA.

Paso 3 no inicia mientras P01 no cierre.