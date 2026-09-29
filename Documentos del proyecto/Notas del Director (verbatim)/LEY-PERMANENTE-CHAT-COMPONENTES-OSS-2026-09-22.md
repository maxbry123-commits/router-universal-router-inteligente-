# LEY PERMANENTE CHAT — REHACER SOBRE COMPONENTES OSS

Fecha: 2026-09-22.

1. El chat NO se construye desde cero.
2. Base obligatoria: Open WebUI descargado exclusivamente con los motores canónicos de main.
3. Flujo obligatorio: MOTOR -> DESCARGAR -> EXTRAER -> EDITAR/ADAPTAR -> CABLEAR -> INCORPORAR -> READ-BACK.
4. Conservar todo el código adicional ya creado: Chat MVP, paneles Vault/Router/Jobs, selector, agentes, GitHub, documentos, Secret Bank, Crazy Wall/handoff, Archivos/Memoria y backend.
5. Ese código adicional se reutiliza como adaptación/extensión sobre Open WebUI; no se borra ni se sustituye por otra implementación desde cero.
6. Los agentes de chat ejecutan; Claude/orquestador audita y da órdenes.
7. Componentes externos solo los adquiere agent-19-chat-components-motors mediante los motores canónicos; GitHub Actions, git clone, curl/wget y gestores de paquetes NO son mecanismo autorizado de adquisición de componentes.
8. Ningún CLOSED/100% sin integración real + read-back + smoke live.
