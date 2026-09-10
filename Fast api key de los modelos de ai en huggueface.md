# Fast API key de los modelos de AI en Hugging Face

## Propósito
Controlar el acceso de agentes al gateway FastAPI del Router sin publicar secretos en GitHub.

## Arquitectura
`AGENTE -> Authorization: Bearer <router_api_key> -> FastAPI -> APIKeyGuard -> Enchufe Gate -> RedUniversal -> model registry -> adapter -> Hugging Face`

## Regla de seguridad
Las API keys reales NO se guardan en este archivo ni en ningún commit. El Router debe guardar solo hash/metadata; plaintext una sola vez.

## Estado actual
- Gateway FastAPI único + Enchufe Gate + RedUniversal: hot-path determinista HF-M01 verificado.
- HF-M02 FastAPI→Enchufe→Router→adapter validado en Job `6aa2cf4f21047bf1b0372e67`: HTTP 200 y `FASTAPI_ENCHUFE_ROUTER_M02_OK=True`.
- Provider hosted auth HF-M01: FLAG; Job `6aa2985921047bf1b03725ed` recibió 403 por permisos insuficientes para Inference Providers; secreto redactado.
- HF-M02 storage RW persistente: FLAG/GAP; Job `6aa2ebc15527934177ec1eb6` recibió 403 al crear Storage Bucket porque la credencial autorizada carece de permiso create/write; secreto protegido no expuesto; HF-M02 NO READY.
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