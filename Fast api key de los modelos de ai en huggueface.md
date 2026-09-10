# Fast API key de los modelos de AI en Hugging Face

## Propósito
Controlar el acceso de agentes al gateway FastAPI del Router sin publicar secretos en GitHub.

## Arquitectura
`AGENTE -> Authorization: Bearer <router_api_key> -> FastAPI -> APIKeyGuard -> Enchufe Gate -> RedUniversal -> model registry -> adapter -> Hugging Face`

## Regla de seguridad
Las API keys reales NO se guardan en este archivo ni en ningún commit. El Router debe guardar solo hash/metadata; plaintext una sola vez.

## Estado actual
- Gateway FastAPI único + Enchufe Gate + RedUniversal: hot-path determinista verificado en Job `6aa297195527934177ec0aed` (`2 passed`).
- HF-M01 dataset/storage RO: verificado con `HuggingFaceH4/ultrachat_200k` en Job `6aa2983921047bf1b03725eb`.
- Provider hosted auth: FLAG; Job `6aa2985921047bf1b03725ed` recibió 403 por permisos insuficientes para Inference Providers; el secreto quedó redactado.
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

Paso 3 no inicia mientras P01 no cierre; `FLAG-HF-PROVIDER-AUTH-001` debe resolverse con credencial autorizada y alcance Inference Providers.