# Laboratorio de pruebas API / SDK (temporal)

**Estado: plugin subido a main y conectado al Router por el Plugin Host. Falta la primera corrida con las claves del banco; el resultado se anota abajo.**
Correccion 2026-10-03: la version anterior de este README decia que el plugin y el handoff ya existian. No existian; ahora si.

## Que prueba
Las claves de OpenAI del banco secreto, con el SDK oficial `openai`. Por cada clave:
1. `models.list()` (/v1/models): cuenta las modelos.
2. `responses.create()` (/v1/responses) con una frase de 16 tokens: genera.
3. `/me`: solo informativo (no es un endpoint oficial de claves API).
PASS de una clave = 1 y 2 bien. 14 claves esperadas x 3 = 42 comprobaciones.

## Flujo
`main -> Router HF 16 GB (git pull cada 60 s) -> Plugin Host -> plugins/openai_sdk_lab -> vault_hook (banco abierto en memoria) -> OpenAI -> resumen sin claves -> RESULTADOS-OPENAI-SDK.json`

## Reglas
No se toca el nucleo del Router. Sin GitHub Actions. Sin LFS. Sin Jobs nuevos. Ninguna clave en el repo, logs ni resultados.

## Archivos
- `README pruebas.md`: este archivo.
- `Laboratorio Code de pruebas.py`: motor (lee `vault_hook.provider_keys("openai")`).
- `Handoff laboratorio pruebas sdk api.md`: conexiones y pendientes.
- `RESULTADOS-OPENAI-SDK.json`: lo escribe el plugin al correr (aun no existe).
- `router inteligente universal/plugins/openai_sdk_lab/`: ficha.json + plugin.py.

## Como se corre (4 pasos, con la clave del Router)
1. `POST /plugins/sync`
2. `POST /plugins/openai_sdk_lab/enable`
3. `POST /vault/unlock` con la clave del banco
4. `GET /plugins`: el health del plugin corre las pruebas y devuelve el resumen en `reason`.

## Resultados
Pendiente de la primera corrida.
