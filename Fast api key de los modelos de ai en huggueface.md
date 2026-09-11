# Fast API key de los modelos de AI en Hugging Face

## Propósito
Controlar acceso de agentes al gateway FastAPI del Router sin publicar secretos.

## Arquitectura verificada
`AGENTE -> Authorization: Bearer <router_api_key> -> FastAPI -> APIKeyGuard -> Enchufe Gate -> RedUniversal -> registry -> adapter -> destino/modelo -> verifier -> response`.

## Estado real del API Key Manager
- P03=`VERIFIED_CLOSED`.
- Capacidad probada: **100 slots/keys**.
- Persistencia: hash-only; plaintext no se commitea.
- Operaciones verificadas: create/verify/rotate/revoke; slot 101 fail-closed.
- Seguridad E2E: 401 sin key, 403 después de revoke, hot-path real verificado.
- GitHub Actions run `34582284615`, job `103208408709`: success, `2 passed in 6.79s`.

## Evidencia de implementación
Commit `af469152fd0306d706c67b8cf6548512fdc4f1c0`; gateway blob `e970b5de2281d236b916ea41492ee52df8454153`; E2E test blob `23473c2a33cb9e5a451ad5a19ce5c4e5a58fc2c7`.

## Reglas de secretos
Las keys reales NO se guardan en README, STATE, BITACORA ni commits. El Router sólo conserva `key_id`, `agent_id`, hash, timestamps, status, scopes y allowed_models. Plaintext se entrega una sola vez en el canal autorizado.

## Estado HF asociado
La certificación individual de HF_M01..HF_M20 está actualmente `ACTIVE_LOOP_MODEL_CERTIFICATION`. Una key válida no convierte un modelo FLAG/GAP en READY: el Router debe consultar registry/estado de modelo antes del routing.

## Criterio final de esta etapa
Después de contabilizar los 20 modelos con PASS o FLAG/GAP explícito, reejecutar regresión/E2E global con APIKeyGuard activo. Sólo entonces cerrar el gate ampliado.