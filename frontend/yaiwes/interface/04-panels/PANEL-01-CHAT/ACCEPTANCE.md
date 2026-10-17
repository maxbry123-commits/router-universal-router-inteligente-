# PANEL-01-CHAT · criterios técnicos de aceptación

Estado objetivo: `PROTOTYPE / FRONTEND FUNCTIONAL / BACKEND BOUNDARY`.

| ID | Requisito | PASS cuando |
|---|---|---|
| AC01 | Arranque | `index.html` abre sin excepción JS y muestra el compositor. |
| AC02 | Fidelidad | Matte/negro/grises, Little azul para selección/foco y naranja no usado como marca. |
| AC03 | Nuevo chat | Crea conversación, la selecciona y aparece en la lista. |
| AC04 | Selector de modo | Heavy/Expert/Fast/Auto abre, selecciona, cambia estado visual y persiste. |
| AC05 | Herramientas | `+` abre sheet; Cámara/Fotos/Archivo disparan input nativo; Audio usa MediaRecorder si está disponible. |
| AC06 | Tool toggles | Investigación/Web/Artefactos cambian `aria-pressed` y estado visual. |
| AC07 | Mensajería local | Enter o Enviar añade el mensaje real al hilo y limpia el input. |
| AC08 | Fail-closed | Sin bridge se muestra `BRIDGE_REQUIRED`; nunca se inventa una respuesta IA. |
| AC09 | Cancelación | Durante QUEUED/RUNNING, Detener cancela el dispatch local y emite `cancel_run`. |
| AC10 | Adjuntos | Se previsualizan, se pueden retirar y pasan como metadatos del mensaje. |
| AC11 | Menú | Renombrar, exportar JSON y eliminar mensajes tienen efecto observable. |
| AC12 | Persistencia | Chats, modo y tools sobreviven `reload` mediante localStorage. |
| AC13 | Responsive | Escritorio muestra rail+chat+inspector; móvil usa rail deslizable y composer persistente. |
| AC14 | Teclado | Foco visible; Enter envía, Shift+Enter agrega línea, Escape cierra menú/rail, flechas navegan modos. |
| AC15 | Cero controles muertos | Todo control visible ejecuta una acción o cambia estado. |
| AC16 | Originales | No se modifica `01-original/`. |

Cierre permitido solo con `AC01..AC16 = PASS` para el alcance frontend local. Integración real con Action Bus/bridge requiere aprobación `OK PANEL-01-CHAT`.
