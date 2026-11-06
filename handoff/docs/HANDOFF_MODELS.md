# MODELOS, API Y SERVICIOS CENTRALES

body:
  responsibility: 'Handoff de area (el registro maestro no lo copia: ver SYSTEM_WIRING_REGISTRY.yaml)'

## Detalle

Estado: DISCOVERED (pendiente de inferencia real)
Componentes: `chat-router/SWE CODE/` (mini_router y cascada) · `chat-router/motores/` (fabrica de motores, pruebas nvidia/groq) · `router-mvp/raiz_fichas_prompt/`
Consumidores: selectores de modelo · harness · agentes
Proveedores: nvidia (NVIDIA_BASE_URL) · groq (GROQ_BASE_URL) · modelos locales (1 por servidor)
Contrato: 3 niveles obligatorios por proveedor: (1) conectividad y autenticacion, (2) inferencia real, (3) integracion con selector + prompt + motor
Politica de cola: al 85 % salta al siguiente; 15 min sin actividad duerme; hasta 3 servidores en cola; al estar lleno espera 1 servidor por modelo; a los 15 min abandona y duerme
Healthcheck: respuesta real desde el selector + recepcion del system prompt + latencia registrada + sin errores criticos
Pendiente: J08 (nvidia) y J09 (locales) con la clave por entorno; medir latencia; verificar failover
Evidencia: ninguna todavia
