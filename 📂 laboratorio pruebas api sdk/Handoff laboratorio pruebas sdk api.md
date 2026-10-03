# Handoff - laboratorio pruebas SDK / API (OpenAI)

Estado: plugin y motor SUBIDOS a main. NO ejecutado todavia: falta la clave del Router (X-API-Key) para abrir el banco y lanzar las pruebas.

## Micro flujo
main -> Router HF 16 GB (git pull cada 60 s) -> Plugin Host -> plugins/openai_sdk_lab -> vault_hook.provider_keys(openai) -> OpenAI SDK -> RESULTADOS-OPENAI-SDK.json

## Donde esta cada cosa
- Motor: Laboratorio Code de pruebas.py (esta carpeta)
- Plugin: router inteligente universal/plugins/openai_sdk_lab/ (ficha.json + plugin.py), nace APAGADO
- Banco: proveedor openai (claves OPENAI_API_KEY_1..14) y grupo sdk en policies.json, ya cableados por otros agentes; verificar con /chat/providers
- Resultados: RESULTADOS-OPENAI-SDK.json (lo escribe el plugin con el token del Job; sin claves)

## Pasos para ejecutar (siempre con Authorization: Bearer token HF y X-API-Key clave del Router)
1. POST /plugins/sync (el Router recoge el plugin nuevo)
2. POST /plugins/openai_sdk_lab/enable
3. POST /vault/unlock con la clave del banco (solo en memoria; nunca en archivos)
4. GET /plugins y leer el reason de openai_sdk_lab: N/14 claves PASS (si dice corriendo, repetir en 1 minuto)
5. Si PASS: dejar el plugin encendido y confirmar que un agente usa el proveedor openai por el Router
6. Si FAIL: anotar la causa por clave en el README; no inventar

## Reglas del Director
Sin GitHub Actions. Sin LFS. Sin tocar el nucleo del Router. Sin claves en archivos, logs ni resultados. Sin Router nuevo ni Jobs nuevos.

## GAP
- Clave del Router: no esta en el repo; la tiene el Director.
- El paquete openai no esta en el pip del Router: el plugin lo instala solo si falta (al relanzar el Job se reinstala).
