# Laboratorio de pruebas API / SDK

Estado: **LABORATORIO ACTIVO — conectado al Router por Plugin Host**.

Objetivo: mantener un punto único, auditable y reutilizable para comprobar APIs/SDK sin modificar el núcleo del Router. Este laboratorio no guarda claves, tokens ni contraseñas en el repositorio.

## Flujo

`main → Router HF activo → git pull periódico → Plugin Host autosync → plugins/openai_sdk_lab → banco secreto desbloqueado en memoria → OpenAI API/SDK → resultado saneado`

## Archivos

- `README pruebas.md` — arquitectura, método y resultados.
- `Laboratorio Code de pruebas.py` — motor real de pruebas.
- `Handoff laboratorio pruebas sdk api.md` — handoff y trazabilidad de conexiones.
- Adaptador runtime: `router inteligente universal/plugins/openai_sdk_lab/plugin.py`.
- Contrato Plugin Host: `router inteligente universal/plugins/openai_sdk_lab/ficha.json`.

## Contrato de prueba OpenAI

Por cada clave OpenAI disponible en el banco:

1. Identidad HTTP: `GET https://api.openai.com/v1/me`.
2. Catálogo por SDK: `client.models.list()` → `/v1/models`.
3. Generación por SDK: `client.responses.create(...)` → `/v1/responses`.

La prueba nunca devuelve ni escribe claves. Solo registra índice de credencial, estado HTTP/código de error, modelo usado, tiempo y PASS/FAIL.

## Conexiones canónicas

Arquitectura del Router:
https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/main/Readme%20arquitectura%20router%20inteligente%20universal/ARQUITECTURA-ROUTER-Y-CONEXIONES.md

Arquitectura de fichas / enchufe:
https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/main/Readme%20arquitectura%20router%20inteligente%20universal/ARQUITECTURA-ROUTER-FICHAS-FABLES.md

Banco secreto implementado:
https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/main/Readme%20arquitectura%20router%20inteligente%20universal/ADENDA-RIU-0110-secret-bank-implementado.md

Handoff global:
https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/main/Estado%20y%20handoff%20global/HANDOFF.md

Handoff del Router:
https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/main/router%20inteligente%20universal/HANDOFF-PROVISIONAL-ROUTER.md

## Estado del Router usado por el laboratorio

- Job controlador: `6abf9d1a404719ba37622215`.
- Hardware: `cpu-basic` / 16 GB.
- `PAUSED=false`.
- Plugin Host ya está montado en el Router.
- `RIU_PLUGINS_AUTOSYNC_S=60`: nuevos plugins se reescanean sin reiniciar el Router.

## Resultados

### Última ejecución

`PENDIENTE_DE_EJECUCION_LIVE`

La sección se actualiza después de la corrida real. No se considera PASS hasta tener evidencia devuelta por el plugin desde el Router vivo.
