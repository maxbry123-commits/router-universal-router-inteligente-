# HARNESS DEEPSEEK — centro de distribucion

body:
  responsibility: 'Handoff de area (el registro maestro no lo copia: ver SYSTEM_WIRING_REGISTRY.yaml)'

## Detalle

Estado: CONFIGURED (existe y esta cableado; falta prueba de contrato)
Componentes: `chat-router/harness/` (plugin.py, server.py, ficha.json) · `chat-router/chat/backend/deepseek_harness/` · `chat-router/plugins/deepseek_harness/`
Consumidores: chat · agentes · motores · loop/cola
Proveedores: nvidia · groq · modelos locales · memoria · storage
Contrato obligatorio por plugin: identificador, entry point, acciones, esquema de entrada, esquema de salida, autenticacion, timeout y politica de errores
Healthcheck: llamada de contrato con entrada y salida comparadas; J12 (distribucion correcta)
GAP conocido: el plugin_host no acepta todavia el entry point `router.router_api.plugin:handle`; resolver respetando las fronteras de seguridad (no ampliar imports a lo bruto)
Pendiente: J12 + prueba de que el prompt llega al payload del proveedor y persiste en Loop y reanudaciones
Evidencia: ninguna todavia
