# FRONTEND — Chat YAIWES (UI -> backend -> harness -> router -> modelos)

body:
  responsibility: 'Handoff de area (el registro maestro no lo copia: ver SYSTEM_WIRING_REGISTRY.yaml)'

## Detalle

Estado: DISCOVERED (cableado existente, pendiente de prueba real)
Componentes: `chat-router/chat/frontend/` (UI Chat YAIWES) · `chat-router/chatbot/frontend-yaiwes/` · `chat-router/chat/backend/` (backend) · `chat-router/chat/espejo/espejo_prod.js` (espejo de OpenClaw)
Consumidores: usuarios (UI) · agentes (selectores)
Proveedores: harness DeepSeek (`chat-router/harness/`) · router (`router-mvp/raiz_router/`) · modelos (nvidia, groq, locales)
Contrato: UI -> api -> backend -> harness -> router -> modelo; el boton de agente y el selector de workflow tienen contratos independientes
Healthcheck: streaming · historial · selector de modelo · ON/OFF · respuesta vacia · error HTTP · timeout · recuperacion de PID · persistencia
Pendiente: prueba real de cada selector (J01), boton ON/OFF de servidor y de agente, y el boton permanente de encendido en la configuracion de la UI
Evidencia: ninguna todavia (no se declara ACTIVE sin las 7 condiciones)
