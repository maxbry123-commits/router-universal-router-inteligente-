# Laboratorio de pruebas API / SDK (temporal)

Estado: plugin y motor SUBIDOS a main. Pruebas NO ejecutadas todavia (falta abrir el banco en el Router vivo). Aun no hay resultados.

(Correccion: una version anterior de este README decia laboratorio activo y citaba un plugin y un handoff que no existian. Era falso y se quito.)

## Que prueba
El SDK de OpenAI con las claves del banco secreto (proveedor openai). Por cada clave, 3 comprobaciones:
1. /me (solo informativa: las claves de API normales suelen no tener ese endpoint)
2. models.list() -> /v1/models
3. responses.create() -> /v1/responses
Una clave cuenta como PASS si pasan la 2 y la 3.

## Micro flujo
main -> Router HF 16 GB (git pull cada 60 s) -> Plugin Host -> plugins/openai_sdk_lab -> vault_hook (banco abierto en memoria) -> OpenAI SDK -> RESULTADOS-OPENAI-SDK.json

## Archivos
- Laboratorio Code de pruebas.py: el motor. No guarda ni imprime claves.
- router inteligente universal/plugins/openai_sdk_lab/ (ficha.json + plugin.py): lo conecta al Router. Nace APAGADO.
- Handoff laboratorio pruebas sdk api.md: pasos y conexiones.
- RESULTADOS-OPENAI-SDK.json: lo escribe el plugin al terminar (sin claves).

## Reglas
Sin GitHub Actions. Sin LFS. Sin tocar el nucleo del Router. Sin claves en archivos, logs ni resultados.

## Resultados
PENDIENTE.
