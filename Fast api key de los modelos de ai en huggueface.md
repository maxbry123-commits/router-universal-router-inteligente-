# Fast API key de los modelos de AI en Hugging Face

## Propósito
Controlar el acceso de agentes al gateway FastAPI del Router sin publicar secretos en GitHub.

## Arquitectura
`AGENTE -> Authorization: Bearer <router_api_key> -> FastAPI -> APIKeyGuard -> Enchufe Universal -> Router -> model registry -> adapter -> Hugging Face`

## Regla de seguridad
Las API keys reales NO se guardan en este archivo ni en ningún commit. El Router debe guardar solo hash/metadata; la key plaintext se entrega una sola vez al crearla.

## Estado actual
- Gateway FastAPI único: PENDING integración final.
- APIKeyGuard/API Key Manager: PENDING Paso 3.
- 20 slots de modelos: creados en índice, model IDs todavía PENDING por GAP de catálogo HF privado.
- Hugging Face Jobs: disponible como compute real.
- Bridge HF/GitHub: existente.

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

No se generarán keys definitivas hasta que el gateway, registry y al menos un model adapter real estén cableados y verificados. Cuando se generen, se entregarán una sola vez fuera del repositorio y este documento registrará únicamente `key_id/hash/status/scopes`.

## Criterio PASS
Agente con key válida -> 200 y routing permitido.
Key revocada/inválida -> 401/403 fail-closed.
Key sin scope de modelo -> 403.
Ningún secreto aparece en logs, GitHub, STATE, BITACORA o respuestas de listado.
