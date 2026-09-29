# Fast API key de los modelos de AI en Hugging Face

## Propósito
Controlar acceso de agentes al gateway FastAPI del Router sin publicar secretos.

## Arquitectura verificada
`AGENTE -> Authorization: Bearer <router_api_key> -> FastAPI -> APIKeyGuard -> Enchufe Gate -> RedUniversal -> registry -> adapter -> destino/modelo -> verifier -> response`.

## API Key Manager
P03=`VERIFIED_CLOSED`; 100 slots/keys probados; hash-only; create/verify/rotate/revoke; slot 101 fail-closed; plaintext nunca commiteado.
Commit `af469152fd0306d706c67b8cf6548512fdc4f1c0`; gateway blob `e970b5de2281d236b916ea41492ee52df8454153`; E2E blob `23473c2a33cb9e5a451ad5a19ce5c4e5a58fc2c7`.

## Certificación HF final
`MODEL_CERTIFICATION_20_OF_20_ACCOUNTED`; M18 quedó FLAG runtime/timeout, no READY. Una key válida nunca promueve un modelo FLAG/GAP a READY.

## Regresión final
Workflow `RIU FAST-CLOSE`, run `34582284615`, job `103434377312`, success; `2 passed, 2 warnings in 6.75s` con APIKeyGuard/hot-path.

## Reglas de secretos
Las keys reales NO se guardan en README, STATE, BITACORA ni commits; sólo key_id, agent_id, hash, timestamps, status, scopes y allowed_models.

## Estado
`CORE_VERIFIED_CLOSED + MODEL_CERTIFICATION_20_OF_20_ACCOUNTED + FINAL_REGRESSION_E2E_PASS` satisfecho; `VERIFIED_CLOSED`.