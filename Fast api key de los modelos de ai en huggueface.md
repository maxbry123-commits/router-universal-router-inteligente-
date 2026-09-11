# Fast API key de los modelos de AI en Hugging Face

## Propósito
Controlar el acceso de agentes al gateway FastAPI del Router sin publicar secretos en GitHub.

## Arquitectura
`AGENTE -> Authorization: Bearer <router_api_key> -> FastAPI -> APIKeyGuard -> Enchufe Gate -> RedUniversal -> model registry -> adapter -> Hugging Face`

## Regla de seguridad
Las API keys reales NO se guardan en este archivo ni en ningún commit. El Router debe guardar solo hash/metadata; plaintext una sola vez.

## Estado actual
- Gateway FastAPI único + Enchufe Gate + RedUniversal: hot-path determinista verificado.
- HF-M02 y HF-M03: FastAPI→Enchufe→Router→adapter previamente validados.
- HF-M05 `Qwen/Qwen2.5-7B-Instruct`: Job integrado `6aa3977e21047bf1b0374e94` COMPLETED; HTTP 200; dataset RO mount True/10 files; CUDA True; route verified; response `RIU_HF_M05_ROUTE_OK`; SHA256 `d3352d066152f07379352c94eaae94dd415be1adcda68b43791f8736c9653e79`; read-back True; `FASTAPI_ENCHUFE_ROUTER_M05_OK=True`.
- Provider hosted auth HF-M01: `FLAG-HF-PROVIDER-AUTH-001` por 403; no bloquea core cuando la ruta local/adapter está certificada.
- APIKeyGuard/API Key Manager: PENDING Paso 3.
- `PLAINTEXT_KEYS: NOT_GENERATED_YET`.

## Formato objetivo de key
`riu_<agent_id>_<random-secret>`; hasta 100 slots/keys, una distinta por agente/slot según política.

## Operaciones requeridas
create/verify/revoke/rotate/list; persistir solo `key_id`, `agent_id`, `key_hash`, timestamps, status, scopes y allowed_models.

## Endpoints objetivo
`POST /v1/keys`, `POST /v1/keys/{key_id}/rotate`, `DELETE /v1/keys/{key_id}`, `GET /v1/models`, `POST /v1/chat/completions`.

## Criterio PASS
Key válida -> routing permitido; revocada/inválida -> 401/403; scope inválido -> 403; ningún secreto en logs/GitHub/STATE/BITACORA; E2E agente→key→FastAPI→Enchufe→Router→adapter→destino→verifier.