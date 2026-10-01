# T-06 — inventario funcional y validación pendiente

Contrato: `PLAN-DSL-DAG-UI.yaml` (T-06), skill `../../📂 Skills Maxbry UI fromtend/diseno/😄SKILL.md` y paleta V07. Cada fila exige prueba en navegador con backend real. `PENDIENTE` no significa PASS.

| ID | Componente | Botón / función | Entrada | Acción | Salida esperada | Estado esperado | Dependencia | Resultado |
|---|---|---|---|---|---|---|---|---|
| T06-F01 | Shell | Chat | click | cargar panel | composer y selectores | READY | panel-chat + API | PENDIENTE |
| T06-F02 | Shell | Archivos | click | cargar panel | lista y upload | READY/EMPTY | panel-archivos + /chat/org/files | PENDIENTE |
| T06-F03 | Shell | Seguimiento | click | cargar panel | grafo, cola y bitácora | READY/EMPTY | panel-seguimiento + State Hub | PENDIENTE |
| T06-F04 | Shell | Canvas | click | cargar panel | lista de adjuntos | READY/EMPTY | panel-canvas + /chat/org/files | PENDIENTE |
| T06-F05 | Shell | Conectores | click | cargar panel | estado real | READY/EMPTY | /chat/org/connectors | PENDIENTE |
| T06-F06 | Shell | Plantillas | click | cargar panel | plantillas LOCKED | READY/EMPTY | /chat/org/templates | PENDIENTE |
| T06-F07 | Shell | Ingeniería | click | cargar panel | controles de solo lectura | READY/EMPTY | /chat/org/engineering | PENDIENTE |
| T06-F08 | Header | Reintentar conexión | click | recargar shell y autenticación nativa | backend accesible o 401 | CONNECTED/DISCONNECTED | Router / browser Basic | PENDIENTE |
| T06-F09 | Chat | Proveedor | selección | GET modelos | lista del proveedor o error | READY/ERROR | /chat/providers/{id}/models | PENDIENTE |
| T06-F10 | Chat | Modelo | selección | seleccionar modelo | valor elegido | READY | respuesta del proveedor | PENDIENTE |
| T06-F11 | Chat | Agente | selección | seleccionar agente | modo agent en petición | READY | /chat/agents | PENDIENTE |
| T06-F12 | Chat | Modo | selección | ajustar max_tokens | fast/balanced/think | READY | composer | PENDIENTE |
| T06-F13 | Chat | Grupo | selección | mantener selección visible | valor elegido | READY | grupo configurado | PENDIENTE |
| T06-F14 | Chat | Cuenta GitHub | selección | mantener selección visible | valor elegido | READY | /chat/github/accounts | PENDIENTE |
| T06-F15 | Chat | Rama | input deshabilitado | impedir edición | sin mutación | BLOCKED | UI-T-05 | PENDIENTE |
| T06-F16 | Chat | Enviar al Router | texto /ayuda, vacío, orden real | validar, enviar, mostrar respuesta o GAP | historial actualizado | LOADING/SUCCESS/ERROR | /chat/send + proveedor real | PENDIENTE |
| T06-F17 | Control | Pausar agentes | click | POST | confirmación o error | SUCCESS/ERROR | /control/pause-agents | PENDIENTE |
| T06-F18 | Control | Reanudar agentes | click | POST | confirmación o error | SUCCESS/ERROR | /control/resume-agents | PENDIENTE |
| T06-F19 | Control | Emergencia | click | POST | confirmación o error | SUCCESS/ERROR | /control/emergency-stop | PENDIENTE |
| T06-F20 | Control | Encender Router | click | POST | confirmación o error | SUCCESS/ERROR | /control/resume-router | PENDIENTE |
| T06-F21 | Archivos | Buscar | texto | filtrar lista | resultados/empty | READY/EMPTY | archivos cargados | PENDIENTE |
| T06-F22 | Archivos | Actualizar | click | GET | lista actualizada/error | LOADING/READY/ERROR | /chat/org/files | PENDIENTE |
| T06-F23 | Archivos | Subir archivo | selección + submit | validar tamaño y POST | ID Router/error | SUCCESS/WARNING/ERROR | /chat/documents | PENDIENTE |
| T06-F24 | Canvas | Vista previa dinámica | click por archivo | obtener media o resumen | imagen/video/texto/error | SUCCESS/ERROR | /chat/media/{id} o /chat/documents/{id} | PENDIENTE |
| T06-F25 | Seguimiento | ID de ejecución | texto | validar ID | error o ID válido | READY/WARNING | validación local | PENDIENTE |
| T06-F26 | Seguimiento | Consultar | click | GET ledger | JSON o error | SUCCESS/ERROR | /chat/org/dag/{id} | PENDIENTE |
| T06-F27 | UI | Resize desktop/tablet/mobile | ancho de ventana | reflujo sin overflow | navegación y controles visibles | READY | CSS V07 y navegador | PENDIENTE |
| T06-F28 | UI | Teclado, foco y touch | tab/tap | activar control | foco visible | READY | CSS, browser | PENDIENTE |
| T06-F29 | Seguridad | Autenticación | desafío nativo / cookie y storage vacíos | autenticar contra Router | 200 o 401 explícito; sin clave en DOM/JS/storage | CONNECTED/BLOCKED | RIU_ROUTER_API_KEY | PENDIENTE |
| T06-F30 | UI | Red y consola | cargas y acciones | observar requests y excepciones | cero errores críticos inesperados | READY/ERROR | navegador | PENDIENTE |

Estados a verificar: IDLE, READY, LOADING, CONNECTING, CONNECTED, DISCONNECTED, SUCCESS, WARNING, ERROR, BLOCKED, EMPTY, NEEDS_INTERVENTION. Si uno no está implementado, registrar `NOT_IMPLEMENTED` y no declarar PASS global.

La tabla de aceptación, capturas, diferencias visuales, correcciones y segunda pasada se completan solo a partir de una ejecución observada; no se rellenan mediante inspección estática.
