# Chat del Router — frontend (`chat router/chat frontend/`)

Interfaz web del chat. HTML, CSS y JavaScript en archivos separados; cada panel y cada ventana tiene su propio archivo cableado.
Este README es el **checkpoint**: aquí se anota cada cambio y cada GAP para no depender de la memoria de nadie.

## Reglas de trabajo (del Director)
- Solo se modifica el frontend y el backend del chat en GitHub. Nada de Hugging Face, GitHub Actions ni otros archivos del repo.
- Vercel es solo puente para llegar a GitHub: no se escribe nada en Vercel.
- Sin archivos monolíticos ni maquetas estáticas: cada panel un HTML, cada ventana un archivo, todo funcional.
- Se mejora lo que no existe o tiene fricción; lo que ya funciona no se cambia.
- Un solo despliegue al final de cada tanda (Vercel limita los despliegues por día).

## Direcciones
- Chat publicado: `https://riu-jev-bridge.vercel.app/` (la raíz abre `shell.html`; `/chat/ui/*` entrega estos archivos; ver `vercel.json`).
- Los archivos de esta carpeta se piden como `/chat/ui/<archivo>`.

## Los 5 paneles
`shell.html` + `shell.js` cargan cada vista con `fetch("/chat/ui/panel-<vista>.html")` y llaman a `mount()` de su JS.

| # | Panel | Vista | HTML | JS | CSS |
|---|-------|-------|------|----|-----|
| 1 | Chat | `chat` | `panel-chat.html` | `panel-chat.js` + `chat-*.js` + `ventanas-nuevas.js` | `shell.css`, `responsive.css`, `chat-*.css` |
| 2 | Canvas e imagen/video | `canvas` | `panel-canvas.html` | `panel-canvas.js` | `shell.css` |
| 3 | Planificación y seguimiento | `seguimiento` | `panel-seguimiento.html` | `panel-seguimiento.js` | `shell.css` |
| 4 | Archivos y proyecto | `archivos` | `panel-archivos.html` (pestañas Archivos / Proyecto) | `panel-archivos.js` + `proyecto.js` | `shell.css`, `ventanas-comun.css` |
| 5 | Configuración de la UI | `apariencia` | `panel-apariencia.html` | `panel-apariencia.js` + `apariencia-*.js` + `bloqueo-pin.js` | `panel-apariencia.css` |

Global (en `shell.html`): `shell.css`, `responsive.css`, `shell-riu.css`, `chat-movil.css`, `encendido.css`, `temas-nuevos.css`.
`panel-org.*` (Conectores / Plantillas / Ingeniería) son marcadores sin uso: ya no están en el menú.

## Ventanas del chat (hojas `.sheet`)
| Ventana | Se abre desde | Archivos |
|---------|---------------|----------|
| Modo, Más, Motor, Archivos, Sandbox, Anclaje | pastillas y botones del chat | hojas en `panel-chat.html`; `chat-ventanas.js`, `chat-ancla.js` |
| Workflow Loops code Yaiwes | fila «workflow Loops code Yaiwes» del panel Selectores (selección + ON/OFF) | `selector-workflows.js`, `ventana-workflows.js` / `.css` |
| Constitución sentinela | pastilla «constitución» | `ventana-constitucion.js` / `.css` |
| Banco de claves | pastilla «claves» | `ventana-claves.js` / `.css` |
| Objetivos del anclaje (Chat / Constitución / Workflows / Agentes remotos / Proyecto / Sandbox): LA MISMA ventana de Anclaje, solo cambia el objetivo; los archivos son compartidos | ventana de Anclaje | `anclaje-destinos.js`, `objetivos-ancla.js` |
| Mi handoff editable (texto + enlaces + archivos) | ventana de Anclaje | `handoff-editor.js` |
| Borrar un archivo | lista de archivos (Anclaje y Archivos) | `archivos-borrar.js` |
| Habilidades (menú al escribir «/») | caja del chat | `menu-habilidades.js` / `habilidades.css` |
| Agregar al chat (Cámara, Fotos, Archivos, proyecto, interruptores) | el clip | `agregar-al-chat.js` / `.css` |
| Notas (una por ventana; en Anclaje, una por objetivo) | al final de cada ventana | `notas-ventana.js` |
| Pensando 3D | sobre la caja de escritura mientras el chat trabaja | `pensando-3d.js` / `.css` |
| 20 mejoras de anclaje | ventana de Anclaje | `anclaje-mejoras.js` / `.css` |
| Almacén de archivos (20 mejoras) | panel Archivos | `almacen-archivos.js` / `.css` |

Partes comunes: `ventanas-comun.js` / `.css` (crear ventana, pastillas, bloque de anclas), `almacen.js` (localStorage), `contexto.js` (lógica pura del contexto), `chat-contexto.js` (lo engancha al envío).
Las ventanas nuevas se construyen por JS y cargan su propio CSS al abrirse; `ventanas-nuevas.js` las cablea (un fallo en una no rompe a las demás).

## Cableado con el chat
- `window.RIU_CHAT` (lo define `panel-chat.js`): `{ chat(), tokens(), pintar() }`. Da acceso a lo anclado del chat activo.
- `window.RIU_HARNESS` (de `api.js`) queda envuelto por `chat-contexto.js`: si hay constitución o workflows encendidos, su texto se antepone al mensaje y las claves compartidas con el chat viajan como `secreto:<referencia>` (solo el nombre). Sin nada encendido, el envío es idéntico al de antes.
- `window.RIU_WORKFLOW_ADAPTERS[id] = { nombre, enviar(wf, entrada, ctx) }`: aquí se registran los plugins que conectan un workflow en curso. Hoy: `chat` y `webhook` (HTTPS).
- Instrucciones a un workflow: desde el chat `/wf <nombre> <instrucción>` (no va a la IA, queda en su ventana de ejecución); la IA escribe en esa ventana con `[[WF:<nombre>]]instrucción[[/WF]]` (el system prompt del workflow encendido se lo explica).
- Anclaje por objetivo: `window.RIU_OBJETIVO_ANCLA()` devuelve el objetivo activo (si no existe, es el chat). `panel-chat.js` usa `chatA()` solo para lo anclado; los archivos y la sesión del servidor siguen siendo los del chat (carpeta compartida). `window.RIU_ANCLA_ABRIR(tipo, id)` abre la ventana con ese objetivo y `window.RIU_ANCLA_REFRESCAR()` la refresca.
- Almacenamiento (localStorage): `riu_chats_v1`, `riu_hist_v1`, `riu_proy_v1`, `riu_apariencia_v1`, `riu_tema`, `riu_avisos_v1`, `riu_reac_v1`, `riu_pin_v1`, `riu_workflows_v1`, `riu_constitucion_v1`, `riu_claves_v1`, `riu_destinos_v1`. sessionStorage: `riu_clave`, `riu_sesion`, `riu_const_oficial`, `riu_borrador_v1`.

## Backend que usa este frontend
- Acciones del puente (`router inteligente universal/plugins/puente_chat/plugin.py`): status, modelos, chat, estado, apagar, herramientas_estado, apagar_todo, subir, archivos, xray, auditor_code, handoff, handoff_texto, sandbox, mover_raiz, descargas, chat_async, resultado. Se llaman con `window.RIU_ACCION(accion, payload)`.
- Banco secreto (`router inteligente universal/integration/chat_mvp/vault_api.py`): `/vault/status|unlock|lock|credentials|rotate|import`. El valor nunca vuelve al navegador.
- Constitución oficial: `plugins/puente_chat/constitucion/CONSTITUCION-YAIWES.json` (se lee por raw.githubusercontent.com, solo lectura).

## Cómo añadir
- **Un panel:** `panel-<vista>.html` + `panel-<vista>.js` (exporta `mount(root, { api, tell })`) + su CSS; registrarlo en `shell.js` (`panels`, `labels`) y en el menú de `shell.html`.
- **Una ventana del chat:** `ventana-<nombre>.js` + `.css`; usar `crearVentana()` y `agregarPill()` de `ventanas-comun.js` y cablearla en `ventanas-nuevas.js`.

## GAP (lo que no está resuelto; no se inventa)
1. **Workflows en curso:** el backend no tiene una acción `workflow`; la ejecución se conecta por adaptadores. Falta el adaptador real al backend.
2. **Agentes remotos + SDK:** se ancla la URL del repo con la marca «SDK»; falta definir la ruta/formato de la SDK de cada agente.
3. **Borrar archivos:** el servidor no tiene todavía la acción `archivo_borrar`; se agregó al backend del chat (`plugin.py`) y entra cuando se reinicie el servidor. Mientras tanto el archivo se quita de la lista y de todo lo anclado en este navegador.
4. **Banco de claves:** necesita que `/vault/*` esté expuesto en el mismo servidor que `harnessUrl` y que el servidor acepte la clave del Router. El servidor no lista credenciales: la lista para compartir se guarda local.
5. **Canvas:** solo vista previa de adjuntos; no genera imagen ni video.
6. **Imágenes del skill:** no se pueden abrir desde el túnel; la etapa de imágenes espera a que se suban.
7. **Configuración de la UI dentro del chat:** se sacó el selector de tema de la barra. Si hay más ajustes de UI dentro del chat, indicar cuáles.
8. **Vercel:** límite diario de despliegues; subir en una sola tanda.

## Checkpoint — registro de cambios
| Commit | Cambio |
|--------|--------|
| `21cd470dfa` | Reversión a un estado conocido cuando el chat desapareció (causa: caché vieja de Edge). |
| `3aaa183ddf` | Restauración de lo revertido + vista smartphone centrada (`chat-movil.css`) + cabeceras no-cache en `vercel.json`. |
| `628c1ca9ad` | Salida del chat 3× más larga; Anclaje se desliza entero; PIN opcional; orbe de conexión; orden del menú; soltar archivos; inventario de los 22 componentes RUI. |
| rama `fast-reply-boton` | Botón «⚡ Rápida» junto al modo: estado por chat, se envía como `fast_reply`, `api.js` devuelve `execution_path` y `ms`, y el chat avisa por qué camino respondió. El backend (fichas_qwen) vuelve a validar. Sin mergear a main hasta que pasen las 8 pruebas. |
| este cambio (6) | Clave de acceso al servidor: `api.js` la lee de `riu_clave` pero nada la pedia ni la guardaba. Ahora se pide sola cuando el servidor rechaza (401/403) y reintenta (`acceso-clave.js`); se puede escribir/probar en Configuración (sección 12); si el envío falla el mensaje vuelve a la caja y la burbuja de error trae Reintentar. |
| este cambio (5) | Paneles Seguimiento y Canvas con datos REALES (`seguimiento-real.js`, `canvas-visor.js`): ya no llaman a la ruta vieja /chat/org/* (daba «Not Found» y quedaban vacíos); Seguimiento muestra de cuándo es la dirección del servidor y avisa si puede estar apagado. |
| este cambio (4) | 20 mejoras de anclaje (`anclaje-mejoras.js`); 20 mejoras del almacenamiento de archivos con el almacén real del chat (`almacen-archivos.js`, adiós «Not Found»); hoja «Agregar al chat» (`agregar-al-chat.js`); notas distintas en cada ventana (`notas-ventana.js`); animación 3D del pensamiento (`pensando-3d.js`); backend: `archivo_borrar` acepta `restaurar`. |
| este cambio (3) | Botón de enviar rectangular y azul eléctrico; anclaje = LA MISMA ventana con 6 objetivos (Chat, Constitución, Workflows, Agentes remotos, Proyecto, Sandbox); borrar un archivo; Mi handoff editable con texto, enlaces y archivos; menú de Habilidades al escribir «/»; backend: acción `archivo_borrar`. |
| este cambio (2) | Botón blanco de enviar devuelto a su forma original; «encendido» ahora enciende el símbolo en azul eléctrico (sin cuadro azul); fila «workflow Loops code Yaiwes» con selección y ON/OFF en Selectores; README y handoff anclables al chat desde Configuración (sección 11). |
| `2ba8c7a35a` | Botón de enviar corregido; «encendido» en azul eléctrico (`encendido.css`); borrar chats con la X de cada pestaña; 5 paneles (Configuración, pestaña Proyecto); ventanas Workflow Loops, Constitución sentinela y Banco de claves; destinos del anclaje; README y HANDOFF. |

Cada cambio nuevo se agrega como una fila arriba de esta tabla.
