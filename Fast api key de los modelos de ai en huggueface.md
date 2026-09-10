# Fast API key de los modelos de AI en Hugging Face

## Propósito
Controlar el acceso de agentes al gateway FastAPI del Router sin publicar secretos en GitHub.

## Arquitectura
`AGENTE -> Authorization: Bearer <router_api_key> -> FastAPI -> APIKeyGuard -> Enchufe Gate -> RedUniversal -> model registry -> adapter -> Hugging Face`

## Regla de seguridad
Las API keys reales NO se guardan en este archivo ni en ningún commit. El Router debe guardar solo hash/metadata; la key plaintext se entrega una sola vez al crearla.

## Estado actual
- Gateway FastAPI único: materializado y delegado al hot-path Enchufe Gate → RedUniversal.
- Hot-path determinista: HF Job `6aa297195527934177ec0aed` COMPLETED, `2 passed`, RC=0.
- HF-M01 provider hosted autenticado: PENDING; dataset/storage: PENDING.
- APIKeyGuard/API Key Manager: PENDING Paso 3.
- 20 slots públicos: catálogo certificado; HF-M02..HF-M20 aún no validados 1×1.
- Hugging Face Jobs: disponible como compute real.

## Formato objetivo de key
`riu_<agent_id>_<random-secret>`

Metadata persistida por key:
- `key_id`
- `agent_id`
- `key_hash`
- `created_at`
- `status`
- `scopes`
- `allowed_models`
- `last_used_at`

## Operaciones requeridas
- create: genera y muestra plaintext una sola vez.
- verify: compara hash, nunca plaintext persistido.
- revoke: invalida key.
- rotate: crea key nueva e invalida anterior.
- list: muestra metadata sin secreto.

## Endpoints objetivo
- `POST /v1/keys` — crear key para agente.
- `POST /v1/keys/{key_id}/rotate` — rotar.
- `DELETE /v1/keys/{key_id}` — revocar.
- `GET /v1/models` — modelos permitidos según key.
- `POST /v1/chat/completions` — ejecución autenticada vía Router.

## Estado de entrega
`PLAINTEXT_KEYS: NOT_GENERATED_YET`

No se generarán keys definitivas hasta cerrar P01. El código de routing determinista ya está verificado, pero todavía falta provider hosted autenticado + dataset/storage de HF-M01.

## Criterio PASS
Agente con key válida -> 200 y routing permitido.
Key revocada/inválida -> 401/403 fail-closed.
Key sin scope de modelo -> 403.
Ningún secreto aparece en logs, GitHub, STATE, BITACORA o respuestas de listado.