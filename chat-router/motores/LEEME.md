# Motores
Movido aquí (git mv, 100% renombres); en las rutas viejas queda un enlace simbólico relativo:

| Antes | Ahora |
|---|---|
| `plugins/motores` (busqueda-contexto, descarga-copia, motores-caso) | `chat-router/motores/motores/` |
| `plugins/motores-descarga` (descarga y extracción) | `chat-router/motores/motores-descarga/` |
| `plugins/chat-router/11-EVIDENCIA` (buscadores y evidencia) | `chat-router/motores/evidencia/` |
| `plugins/chat-router/12-FABRICA-MOTORES` (canvas, layout, QA, flujo de acciones) | `chat-router/motores/fabrica-motores/` |

Cableado actual: `plugins/puente_chat/plugin.py` usa sus propias copias en `plugins/puente_chat/fichas/motores_descarga` y `motores_busqueda` (no dependen de estas rutas) y la ventana `chat/frontend/ventana-motor.js`. Falta ofrecerlos en el MCP y el Harness del MVP (fase 6).
