# Chat 2 · RUI — aplicación segura de componentes (V11)

Fuente: `apariencia-extra.js` (inventario canónico 01–22); se reutilizan los componentes **ya conectados**, sin clonarlos ni inventar resultados del backend.

| RUI | Componente | Ubicación existente / reutilización evaluada |
|---|---|---|
| 01 | Folder | Estado vacío de archivos |
| 02 | Bounce sidebar | Cambio de vistas; feedback breve al abrir grupos en compositor |
| 03 | Hook sidebar | Indicador del menú lateral, no trasladar al input |
| 04 | Family drawer | Hojas de Archivos/LOOP/ventanas, no duplicar modal |
| 05 | Proximity sidebar | Navegación de escritorio solamente, sin hover móvil |
| 06 | Duration picker | Duración de aviso en Configuración |
| 07 | Fluid orb | Respuesta pendiente exclusivamente |
| 08 | Scroll progress | Barra y flecha; scroll de documento móvil, scroll del historial en escritorio |
| 09 | Code block | Código de respuestas y botón copiar con estado temporal |
| 10 | OTP input | Configuración de PIN, nunca en campo de mensaje |
| 11 | Gravity letters | Bienvenida del historial vacío |
| 12 | GitHub activity | Actividad real del panel Más |
| 13 | Emoji reaction | Reacciones; microinteracción táctil sin estado falso |
| 14 | Notification bell | Cabecera existente |
| 15 | Step player | Diagramas de selectores existentes |
| 16 | Grid reveal | Iconos del panel de Apariencia; no relanzar en cada pulsación |
| 17 | Gooey nav | Navegación principal existente |
| 18 | Delete button | Cierre de chat con confirmación |
| 19 | Animated counter | Número de anclas real |
| 20 | Matrix orb | Estado real de conexión |
| 21 | Task list | Lista de tareas real del motor |
| 22 | Voice note | Micrófono activo solamente |

**Decisión V11**: recuperar cubo CSS 3D original de 6 caras + 2 anillos, visible en reposo y animado sólo cuando el chat está ocupado. No clonar cubos ni inventar estados. `chat-flujo-movil.css` es un ajuste aislado cargado desde `barra-mas.js`; la app móvil vuelve al scroll natural de página. Conserva selectores/modelos/handlers y el backend sin tocar.

**QA**: teclado Android con input 116px+, scroll de página, botón expandir, iconos sin solapamiento y botón único de bajar. Estas interacciones requieren prueba en navegador real antes de marcar PASS visual.
