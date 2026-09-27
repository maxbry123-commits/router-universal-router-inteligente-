# Plugin Hermes → Router RIU (fase 1)

Este paquete es un **puente externo**: Hermes llama la API HTTP que ya ofrece el Router. No importa módulos del Router, no añade rutas a `app.py`/`router.py`, no cambia SQLite y no activa llamadas al HF Dataset ni al HF Storage Bucket.

## Herramientas expuestas

- `riu_router_health`: consulta `/health`.
- `riu_storage_status`: consulta `/chat/storage` (solo lectura).
- `riu_list_conversations` y `riu_read_conversation`: leen el historial existente.
- `riu_send_chat_turn`: manda el turno a `/chat/send`; el almacenamiento normal del Router guarda la conversación.
- `riu_upload_text_document`: sube texto a `/chat/documents`; no lo sincroniza con Hugging Face.
- `riu_graph_status`: consulta `/chat/graph` (solo lectura).

La escritura solo ocurre al invocar explícitamente enviar un turno o subir un documento. No hay operación de sincronización ni llamada directa a Hugging Face en esta fase.

## Configuración necesaria en el entorno de Hermes

El administrador de Hermes debe configurar, sin poner secretos en el repositorio:

- `RIU_ROUTER_BASE_URL`: origen HTTPS de la API del Router, sin ruta adicional.
- `RIU_ROUTER_API_KEY`: la API key que el Router ya acepta.

La herramienta valida TLS fuera de localhost, no acepta una URL arbitraria desde los argumentos, limita el texto/archivos y no escribe los cuerpos de error del servidor en los logs de la herramienta.

## Estado / activación

- `plugin.yaml` identifica un plugin de herramientas Hermes. Esta carpeta bajo el repo **no instala ni activa** por sí sola el plugin en una instancia Hermes.
- La ficha FABLES queda con estado `testing`, clave de firma pendiente y permisos limitados. No convertirla a `active` ni saltar el gate de aprobación/firma.
- El repositorio inspeccionado contiene el código fuente del agente Hermes y su cargador MCP/plugins, pero no un Hermes Harness ejecutable/configurado en este checkout. El puente solo estará disponible cuando una instancia Hermes autorizada lo instale/importe y habilite explícitamente.

## Prueba local

Desde la raíz del repo:

```bash
python3 -m unittest 'chat router.plugins.riu_router_bridge.test_bridge'
python3 'chat router/plugins/riu_router_bridge/ficha_contract_v2.py'
```

Los tests usan un servidor HTTP falso local; no contactan al Router, Hugging Face, GitHub ni Vercel.
