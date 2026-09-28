# T10 — Endurecimiento del enrutamiento gratuito de OmniRoute

**Motor:** OmniRoute v3.8.50 precompilado. **Estado:** correcciones locales parciales; inferencia gratuita externa aún sin PASS.
[Bitácora T03](../README-BITACORA-T03.md) · [Handoff](../../06-ESPEJOS/HANDOFF-ESPEJOS.md) · [Contrato T10](../../06-ESPEJOS/tareas/T10.md).

## Causa y alcance
El runtime OmniRoute ya tuvo 9 tests PASS, puerto 20128 abierto y health 200 (HF Job 6aba04746b030d633f69bc1c). Sin embargo, auto/best-free devolvió chat 502: OpenCode 403, Felo 400/429; pruebas individuales con DDG 418, UncloseAI 502, AI Horde 406. El procesador no es el proveedor del modelo.

El upstream v3.8.50 tiene allowlist de no-auth limitada a opencode/felo-web para el selector auto general (aunque existen selectores por familia). Esa allowlist está compilada, por tanto **no aplicar un parche de TypeScript sobre un paquete npm ya compilado**, ni volver a compilar OmniRoute en la máquina de runtime.

## Implementado una corrección a la vez
1. Lanzador T03: habilitar OMNIROUTE_ROTATE_ON_400=true por defecto, respetando el valor explícito del operador. 429/500/502 ya se manejan en upstream. Mantener OMNIROUTE_AUTO_FREE_FALLBACK_TO_FULL_POOL=false por defecto para no caer en modelos de pago.
2. diagnostico.py: llama a health y al catálogo; sin --modelo NO envía chats. Con hasta cinco --modelo, solo una solicitud por cada modelo anunciado, no hay reintentos, valida contenido real y separa 200 vacío/400/403/418/429/502. Omite por defecto los modelos ya rechazados en pruebas previas. Nunca imprime respuesta completa o secretos.
3. bloqueos.py: usa la API NATIVA /api/settings (blockedProviders). DRY-RUN por defecto; --aplicar explícito y revisión condicional (If-Match y expectedRevision); --desbloquear revierte únicamente lo solicitado. No deshabilitar un proveedor entero por un error puntual de modelo.
4. tests/test_diagnostico.py y tests/test_bloqueos.py: pruebas deterministas sin proveedores reales ni claves.

## Uso desde el host que ejecuta OmniRoute

~~~bash
# Inspección sin POST a modelos:
python3 diagnostico.py

# Un candidato concreto PUBLICADO en /v1/models y permitido por su proveedor:
python3 diagnostico.py --modelo "PREFIJO/MODELO"

# Previsualización de exclusión, NO modifica ajustes:
python3 bloqueos.py --proveedor opencode

# Bloqueo de proveedor persistente SOLO tras comprobar que su acceso está restringido:
python3 bloqueos.py --proveedor opencode --aplicar

# Reversión cuando el proveedor vuelva a estar disponible:
python3 bloqueos.py --proveedor opencode --desbloquear --aplicar
~~~

**Seguridad:** el acceso a la configuración debe hacerse por localhost con permisos de administrador; no difundir claves ni revelar el resto de settings. Un HTTP 403 del proveedor no se arregla intentando aparentar ser un cliente autorizado. Un 429 exige respetar su límite, no reintentar sin control.

## Estado detallado frente a las ocho soluciones investigadas

| Paso | Estado verificado |
|---|---|
| 1. Candidatos con contenido real | Auditor implementado; respuesta live nueva PENDIENTE |
| 2. Rotación en 400 | APLICADA en start_omniroute.sh (cambio de entorno, sin build) |
| 3. Error 403 sin falso éxito | Clasificador del auditor implementado; binario upstream NO modificado |
| 4. PR posterior v3.8.51 | INVESTIGADO; no se reemplaza la versión estable sin publicación/test |
| 5. Filtro de auto | Uso nativo de blockedProviders preparado; NO escrito sobre runtime vivo |
| 6. Cooldowns y circuit breaker | Ya están implementados en OmniRoute; NO duplicados |
| 7. 200 sin contenido | El auditor devuelve EMPTY_RESPONSE y no marca PASS |
| 8. IDs obsoletos | El auditor exige que el modelo esté anunciado por /v1/models; actualización nativa del catálogo pendiente |

## Evidencia oficial
- [v3.8.50 fuente](https://github.com/diegosouzapw/OmniRoute/tree/v3.8.50)
- [Selector nativo](https://github.com/diegosouzapw/OmniRoute/blob/v3.8.50/open-sse/services/autoCombo/virtualFactory.ts)
- [Rotación](https://github.com/diegosouzapw/OmniRoute/blob/v3.8.50/open-sse/services/rotationConfig.ts)
- [API de ajustes](https://github.com/diegosouzapw/OmniRoute/blob/v3.8.50/src/app/api/settings/route.ts)
- [Troubleshooting](https://github.com/diegosouzapw/OmniRoute/blob/v3.8.50/docs/guides/TROUBLESHOOTING.md)
- [Incidencia OpenCode 403](https://github.com/diegosouzapw/OmniRoute/issues/13935)
- [PR posterior a 3.8.50](https://github.com/diegosouzapw/OmniRoute/pull/14013)
- [Catálogos obsoletos / discusión](https://github.com/diegosouzapw/OmniRoute/discussions/14327)

**Gate:** ni T10 completo ni FREE_PROVIDER_PASS sin POST OmniRoute /v1/chat/completions HTTP 200 con texto no vacío. Todo bloqueo por falta de autorización permanece externo; no pretender corregirlo en el procesador.
