# Cambios del FRONTEND del chat (todos los commits)

Generado por `chat-router/chat/auditoria/cambios.py` desde `git log`. Para auditar un cambio: `git show <commit> -- <archivo>`.
Columnas: commit · fecha · autor · qué · archivos · funciones (+ añadidas / − quitadas).

Total de commits: **217**

| Commit | Fecha | Autor | Cambio | Archivos | Funciones |
|---|---|---|---|---|---|
| `11eb8842e8` | 2026-10-21 | Maxbry | fix(public_chat_app): excepts de anyio y autopull loguean type(exc).__name__ sin cambiar flujo | `acceso-clave.css`, `acceso-clave.js`, `agentes-mirror.js`, `agregar-al-chat.css`, `agregar-al-chat.js`, `almacen-archivos.css`, `almacen-archivos.js` … (+278) | +App, +F, +FAST_SEL, +Icon, +LucideProvider, +N, +ORD, +SEL_GLOBAL … |
| `6208f52bf7` | 2026-10-22 | Maxbry | chat: cerrar selector y controles | `api.js`, `panel-chat.html`, `panel-chat.js`, `tools-ventana.js` | — |
| `fb653e8d46` | 2026-10-22 | Maxbry | chat: enrutar el selector Qwen y ampliar la espera de respuesta | `api.js` | — |
| `93be675bfe` | 2026-10-22 | Maxbry | fix(chat-ui): compactar editor autoajustable y ampliar salida del modelo | `chat-espacio.css`, `panel-chat.js` | +ajustarAlturaEditor |
| `be896f6774` | 2026-10-22 | Maxbry | chat: validar modelos del catalogo y ejecutar herramientas GitHub y HF desde el banco | `api.js`, `chat-selector-modelos.js`, `panel-chat.js`, `tools-ventana.js` | — |
| `71664b7640` | 2026-10-23 | Maxbry | chat: limitar interruptores a IA delegada, conservar contexto y continuar respuestas truncadas | `panel-chat.js`, `tools-ventana.js` | — |
| `1ca3f8af2c` | 2026-10-23 | Maxbry | fix(frontend): exportar conectarSelectores para cargar la interfaz del chat | `chat-selectores.js` | — |
| `c456907f71` | 2026-10-23 | Maxbry | fix(chat): restaurar HTML truncado de ventanas y selectores sin perder controles nuevos | `panel-chat.html` | — |
| `57931a7f58` | 2026-10-23 | Maxbry | chat: corregir ancho movil de IA, reintentar catalogo y omitir LIVE_URL inexistente | `api.js`, `chat-movil.css`, `chat-selector-modelos.js`, `config.js` | +cargarCatalogo |
| `85eb29f018` | 2026-10-23 | Maxbry | chat: cargar dimensiones del editor antes de calcular su altura inicial | `shell.html` | — |
| `62fbb681c4` | 2026-10-23 | Claude | chat: IA/agentes ON/OFF desde el servidor, ventanas de Conexiones y ROOM, checklist de pendientes | `controles-ventana.js`, `panel-chat.js`, `pendientes-panel.js`, `shell.js`, `tools-ventana.js` | +aplicarIA, +avisar, +btn, +campo, +checklist, +dibujar, +el, +falla … |
| `59f811887e` | 2026-10-23 | Claude | chat: Maxbry UI (composer ordenado, ＋ Agregar al chat, chips, toast), salida ancha y backend de archivos/sandbox/proyectos/pensamiento | `chat-maxbry.css`, `controles-ventana.js`, `maxbry-ui.js`, `panel-chat.html`, `panel-chat.js`, `pendientes-panel.js`, `shell.html` … (+2) | +SVG, +ajustar, +avisos, +cerrar, +colocar, +el, +estado, +modo … |
| `28bcf2b6f3` | 2026-10-23 | Claude | chat: handoff_texto, filas de selector como mode-option y documentacion Maxbry UI + verificacion cruzada | `chat-maxbry.css` | — |
| `9607eb66ad` | 2026-10-23 | Claude | chat: boton Servidor (encender/apagar/reiniciar) via /api/power en Vercel, vercel.json y CORS del Router | `power.js`, `controles-ventana.js`, `maxbry-ui.js`, `power.test.js`, `vercel.json` | +boton, +hf, +igual, +lanzar, +leer, +llamar, +pintarPower, +power … |
| `62c3e0d1ee` | 2026-10-23 | Claude | mvp: los 23 modelos del plan Standard (13 texto, 3 imagen, 3 audio, 4 video) con generacion multimedia y medios en el chat | `chat-maxbry.css`, `maxbry-ui.js` | +medios |
| `7548c2cc87` | 2026-10-23 | Claude | chat: agentes conectables (1 a 50, cada uno con su modelo) y dos botones separados IA / Agentes | `chat-maxbry.css`, `maxbry-ui.js`, `tools-ventana.js` | +aplicarFlags, +chip · −aplicarIA |
| `748db5a6e5` | 2026-10-24 | Claude | Chat: capa de formato, system prompt ON/OFF, yaiwes.md global, organizador de pendientes, constitucion y pendientes al modelo | `anclaje-destinos.js`, `chat-maxbry.css`, `chat-ventanas.js`, `maxbry-ui.js`, `panel-chat.html`, `panel-chat.js`, `pendientes-panel.js` … (+1) | — |
| `24b26c7735` | 2026-10-24 | Claude | Boton Servidor: usa HF_TOKEN_1 del entorno de Vercel | `power.js` | — |
| `5be2929688` | 2026-10-24 | Claude | ROOM: turno de agentes y modelos; READMEs de arquitectura/handoff; raiz limpia | `controles-ventana.js` | — |
| `54c8815ea0` | 2026-10-24 | Claude | Chip System prompt junto a IA y Agentes (antes quedaba deformado en la fila de acciones) | `maxbry-ui.js` | — |
| `70cc3661f4` | 2026-10-24 | Claude | Chat: botones del composer visibles como antes; el Router no se reinicia por cambios solo de pantalla o documentos | `maxbry-ui.js` | — |
| `8557028764` | 2026-10-24 | Claude | Selectores: ON/OFF, info, rapida y modelo por fila (RIU_SELECTORES) sin tocar el resto del frontend | `chat-maxbry.css`, `chat-selectores.js`, `shell.html` | +fila, +filas, +modelo, +refrescar |
| `3485f7ccc3` | 2026-10-24 | Claude | Frontend del chat: volver al estado anterior a los cambios de Claude (base 1b916a587c); se conserva vercel.json para que Vercel sirva /chat/ui. Los ca | `anclaje-destinos.js`, `power.js`, `chat-maxbry.css`, `chat-selectores.js`, `chat-ventanas.js`, `controles-ventana.js`, `maxbry-ui.js` … (+7) |  · −SVG, −ajustar, −aplicarFlags, −avisar, −avisos, −boton, −btn, −campo |
| `a2aff6e677` | 2026-10-24 | Claude | Cableado del selector: RIU_SELECTORES (el chat nunca recibia el selector encendido y mandaba siempre el modelo por defecto). Solo chat-selectores.js y | `chat-selectores.js`, `shell.html` | +fila, +filas, +modelo, +refrescar |
| `548c387b8e` | 2026-10-24 | Claude | Chat: reintegrar chips IA/Agentes/System prompt (estado del servidor), checklist de pendientes, boton Continuar, medios en la burbuja y texto yaiwes.m | `anclaje-destinos.js`, `chat-medios.css`, `chat-medios.js`, `chat-ventanas.js`, `panel-chat.html`, `panel-chat.js`, `pendientes-panel.js` … (+3) | +aplicarFlags, +avisar, +checklist, +chip, +llamar, +medios, +mover, +pintarLista |
| `c28df985d0` | 2026-10-24 | Claude | Chat: /memoria en el Router (historial y pestañas entre dispositivos), chips en píldora con punto de estado, diagrama ⓘ sin desbordar, icono de Pendie | `chat-pulido.css`, `pendientes-panel.js`, `shell.html` | — |
| `af633b9819` | 2026-10-24 | Claude | Chat móvil: el selector de workflows y los accesos que buscan controles movidos a la pestaña móvil vuelven a funcionar; los controles de otra vista ya | `chat-selectores.js`, `panel-chat.js`, `shell.js` | — |
| `a65c5b8380` | 2026-10-24 | Claude | Chat: el diagrama ⓘ de cada selector tiene el botón Recorrer (RUI 15); los 22 componentes RUI verificados en móvil y escritorio | `chat-selectores.js` | — |
| `f6af79b3fa` | 2026-10-24 | Claude | Paso 2.1: ventanas Conexiones, ROOM CONFERENCIAS (con turno de los agentes y lista de invitables) y Servidor (api/power en Vercel) en módulos propios  | `power.js`, `shell.html`, `shell.js`, `power.test.js`, `ventana-conexiones.js`, `ventana-room.js`, `ventana-servidor.js` … (+2) | +boton, +btn, +campo, +cargar, +dibujar, +el, +falla, +hf … |
| `cbd1647056` | 2026-10-24 | Claude | Conexiones: quitar una conexión (libera el tope de 10 y vacía su secreto); contraste WCAG AA en los 7 temas (texto encendido, respuestas de selectores | `chat-pulido.css`, `chat-riu2.js`, `selector-resp.css`, `ventana-conexiones.js`, `ventanas-control.css` | — |
| `9fd44c13e4` | 2026-10-24 | Claude | Chat escritorio: Enviar siempre a la vista (altura medida desde el inicio real del chat) y sin «Enviar Enviar»; chips sin disabled para no perder el f | `chat-pulido.css`, `panel-chat.js`, `tools-ventana.js` | — |
| `6b2a24036e` | 2026-10-24 | Claude | Selector NVIDIA/Groq: la hoja lista los modelos reales de Groq/NVIDIA del Router (las fichas viejas nv-* respondían con Qwen) y la fila muestra el mod | `chat-selectores.js`, `fichas-externas.js`, `panel-chat.js`, `shell.js` | +aplicar, +cargar, +cfg, +fichaEt, +leer |
| `8ffec72cd7` | 2026-10-24 | Claude | Chat: salida más grande (caja de escritura en filas, herramientas deslizables, ⤢ salida grande); LLM tool y Agente tool = mismos permisos del servidor | `api.js`, `chat-pulido.css`, `composer-filas.css`, `composer-filas.js`, `panel-chat.js`, `shell.html`, `shell.js` | +QUEDAN, +ampliar, +ordenar, +pintarTools, +pulsar, +revisar · −pintarLock, −refrescarLock |
| `5f7c08eacd` | 2026-10-24 | Claude | Chat: arreglo urgente de api.js (un comentario cortaba la línea y el chat no cargaba); LLM/Agente tool muestran el estado real al recargar | `api.js`, `panel-chat.js` | — |
| `f76858c6dd` | 2026-10-24 | Claude | Chat: al abrir vuelve a leer los permisos del servidor (y pide la clave si es incorrecta) | `panel-chat.js` | — |
| `a80f5bc400` | 2026-10-24 | Claude | Chat móvil: caja de escritura en rejilla (texto + Enviar en la misma fila, chips de estado siempre visibles, herramientas con botón propio que se abre | `composer-filas.css`, `composer-filas.js` | +abiertas, +pinta |
| `1d7b22c499` | 2026-10-24 | Claude | Chat escritorio: el botón de herramientas solo existe en móvil | `composer-filas.css` | — |
| `a34ccf2482` | 2026-10-25 | Claude | Chat: debajo del texto 3 selectores (Modelo · Permisos · Herramientas) con dibujo 2D y nombre que abren su ventana; los selectores de modelo se mudan  | `chat-selectores.js`, `composer-filas.css`, `composer-filas.js`, `fichas-externas.js`, `panel-chat.html`, `panel-chat.js`, `tools-ventana.js` | +SVG, +cerrar, +el, +hoja, +hojaGroq, +montar, +pintarModelo, +pintarPermisos … · −abiertas, −pinta |
| `f8a536e65a` | 2026-10-25 | Claude | Chat escritorio: Enviar compacto al lado del texto | `composer-filas.css` | — |
| `5fc6df588d` | 2026-10-25 | Claude | Chat: Detener aparece en cuanto se envía | `composer-filas.js` | — |
| `43c3163bb8` | 2026-10-25 | Claude | Frontend dividido en módulos: panel-chat.js 818→408 líneas (buzón, selects secundarios, sandbox, motor, selector de ancla, controles, envío, píldora d | `buzon-proceso.js`, `chat-riu2.js`, `controles-chat.js`, `enviar-mensaje.js`, `panel-chat.js`, `pildora-ficha.js`, `riu-campana.js` … (+10) | +montarBuzon, +montarControlesChat, +montarEnviar, +montarMotor, +montarPildoraFicha, +montarSandboxChat, +montarSelectorAncla, +montarSelectsSecundarios |
| `4d21350bff` | 2026-10-25 | Claude | Pruebas e2e del chat en el repo (plugins/chat-router/e2e): servidor local con modelos simulados y la batería completa, para que Grok y cualquiera las  | `README.md`, `axe.js`, `botones.js`, `composer3_e2e.js`, `dispositivos.js`, `eslint.config.mjs`, `inventario.js` … (+11) | +_sol_falso, +apagarTodo, +clic, +corre, +correr, +elegirQwen, +encender, +f … |
| `1aef5be56b` | 2026-10-25 | Claude | Bloques para Grok (revisión, instrucciones, build) y README de las pruebas e2e | `README.md` | — |
| `f147893bf5` | 2026-10-25 | Claude | Raices del chat (frontend y backend): indices con commits, cambios, handoff, instrucciones/danos/pendientes y auditor de cableado | `cableado.py`, `cambios.py`, `indice.py` | +escribir, +f, +git, +grupo, +info, +tabla |
| `9c4e58e1a3` | 2026-10-25 | Claude | Organizar el chat en dos raices: chat/frontend y chat/backend (mvp, harness, cliente) con enlaces de compatibilidad para el Space y los plugins | `README.md`, `axe.js`, `botones.js`, `composer3_e2e.js`, `dispositivos.js`, `eslint.config.mjs`, `inventario.js` … (+328) |  · −escribir, −f, −git, −grupo, −info, −tabla |
| `d932b7a88d` | 2026-10-25 | Claude | Frontend: revertir el rediseno del composer que dano cubo de pensamiento, Detener, controles y etiquetas de modo (vuelve la caja de escritura de la ba | `axe.js`, `composer3_e2e.js`, `modelos_e2e.js`, `original.js`, `paso2.js`, `paso21.js`, `teclado.js` … (+6) | +vis · −QUEDAN, −SVG, −ampliar, −cerrar, −el, −hoja, −montar, −ordenar |
| `bc015dd92a` | 2026-10-25 | Claude | Chat: un solo selector guarda todos los selectores de modelo (indicador fuera con el modelo que responde) y la salida mide 4 veces su alto con la caja | `selector_ventana.js`, `todo.sh`, `salida-ampliada.js`, `selector-modelos.css`, `selector-modelos.js`, `shell.html`, `shell.js` | +abrir, +bajar, +cerrar, +elegirQwen, +encender, +esperar, +iniciar, +medirYAplicar … |
| `0c25ab8d10` | 2026-10-25 | Claude | Chat: la lista de modelos de Team qwen sale siempre (ultima lista del Router o catalogo del plan) y se reintenta si el Router tarda; el corte por tiem | `catalogo_e2e.js`, `todo.sh`, `api.js`, `chat-selector-modelos.js` | +aplicarLista, +guardada, +ok |
| `dd4c63c8d5` | 2026-10-25 | Maxbry | Chat: deja de cargar la salida x4 que alargaba la pagina | `shell.js` | — |
| `cc8f3f8716` | 2026-10-25 | Maxbry | Chat: devuelve la lista cableada de Team qwen y Team 5 MVP | `chat-selector-modelos.js` |  · −aplicarLista, −guardada |
| `f5dc0206f1` | 2026-10-25 | Maxbry | Chat: en el celular Enviar queda fijo y la caja deja de partirse | `chat-espacio.css` | — |
| `6099026707` | 2026-10-25 | Maxbry | Chat: un 401 sin clave ya no deja pegado Acceso requerido | `api.js` | — |
| `6902f7d6b2` | 2026-10-25 | Maxbry | Chat: bloquear una herramienta ya no cambia el aviso de IA | `tools-ventana.js` | — |
| `804772030a` | 2026-10-25 | Maxbry | Chat: sin clave no consulta el catalogo de modelos | `chat-selector-modelos.js` | — |
| `8b1bee3afe` | 2026-10-25 | Maxbry | Chat: en el celular IA, Agentes y System prompt quedan a la vista | `chat-espacio.css` | — |
| `de01584759` | 2026-10-25 | Maxbry | Chat: en el celular los avisos dejan de tapar los iconos | `chat-espacio.css`, `chat-pulido.css`, `tools-ventana.js` | +meter |
| `0d049bf3ff` | 2026-10-25 | Maxbry | Chat: en el celular Copiar y Editar se pueden tocar | `chat-espacio.css` | — |
| `f27bba6bf8` | 2026-10-25 | Maxbry | Chat: en el celular Auto deja de quedar debajo de Enviar | `tools-ventana.js` | — |
| `a84bec1540` | 2026-10-25 | Maxbry | Chat: en el celular la fila de iconos ya no entra en Enviar | `chat-espacio.css` | — |
| `3a611a5972` | 2026-10-25 | Maxbry | Chat: en el celular los iconos del final dejan de cortarse | `chat-espacio.css` | — |
| `80cd721399` | 2026-10-25 | Maxbry | Chat: en el celular los iconos de la caja se pueden tocar | `chat-espacio.css` | — |
| `d60ce4c7cf` | 2026-10-25 | Maxbry | Chat: en el celular Servidor y Pendientes ya no entran en Enviar | `chat-espacio.css` | — |
| `c989e29468` | 2026-10-25 | Maxbry | Chat: en el celular los iconos de la segunda fila quedan juntos | `chat-espacio.css` | — |
| `6757b4b147` | 2026-10-25 | Maxbry | Chat: en el celular el nombre del modelo se lee mejor | `chat-espacio.css` | — |
| `50a22f04b8` | 2026-10-25 | Maxbry | Chat: en el celular Enviar queda alineado con la caja | `chat-espacio.css` | — |
| `f41b90b232` | 2026-10-25 | Maxbry | Chat: en el celular Auto queda a la altura de los avisos | `chat-espacio.css` | — |
| `67a6422e57` | 2026-10-25 | Maxbry | Chat: en el celular Auto queda en linea con System prompt | `chat-espacio.css` | — |
| `9c1ccf82ad` | 2026-10-25 | Maxbry | Chat: en el celular Enviar ya no queda pegado a los iconos | `chat-espacio.css` | — |
| `b37e6e6fc0` | 2026-10-25 | Maxbry | Chat: en el celular los atajos del saludo se pueden tocar | `chat-espacio.css` | — |
| `4ea0631293` | 2026-10-25 | Maxbry | Chat: LOOP con boton y ventana para encender y apagar | `loop.js`, `chat-espacio.css`, `shell.js`, `ventana-loop.js`, `ventanas-control.js` | +guardar, +latido, +marcarBoton, +montar, +pedir, +pintar, +pintarLoop, +sesion |
| `4619228534` | 2026-10-25 | Maxbry | Chat: el LOOP encendido sigue al recargar | `ventana-loop.js` | — |
| `c0e967be8b` | 2026-10-25 | Maxbry | Chat: el LOOP guarda objetivo, plan y tareas | `loop.js`, `chat-espacio.css`, `ventana-loop.js` | +base, +bloque, +conTexto, +corto, +enlazarProyecto, +guardarYaiwes, +leerCampos, +lineas … |
| `0e3ab08ddd` | 2026-10-25 | Maxbry | Chat: el LOOP dispara cada parte en vez de solo nombrarla | `loop.js`, `ventana-loop.js` | +disparar |
| `0e0b24324c` | 2026-10-25 | Maxbry | Chat: la ventana del LOOP muestra el avance | `chat-espacio.css`, `ventana-loop.js` | — |
| `43c7040ccb` | 2026-10-25 | Maxbry | Chat: guardar el LOOP lee yaiwes.md antes de escribir | `ventana-loop.js` | — |
| `8584bd29a1` | 2026-10-25 | Maxbry | Chat: ventana para probar el Router por HTTP y MCP | `chat-espacio.css`, `shell.js`, `ventana-mcp.js`, `ventanas-control.js` | +base, +clave, +correr, +montar, +pedir, +pintar |
| `2bc099b784` | 2026-10-25 | Maxbry | Chat: el panel del LOOP muestra recibo, bloqueo y siguiente paso | `chat-espacio.css`, `ventana-loop.js` | — |
| `85966efa02` | 2026-10-25 | Maxbry | Chat: el LOOP guarda la traza y se apaga en la vuelta 8 | `loop.js`, `chat-espacio.css`, `ventana-loop.js` | +anotar |
| `270d335418` | 2026-10-25 | Maxbry | Chat: el LOOP distingue armar, seguir y pausa | `ventana-loop.js` | — |
| `544d6b9e0d` | 2026-10-25 | Maxbry | Chat: una tarea no cuenta hasta que el LOOP la observa | `loop.js`, `chat-espacio.css`, `ventana-loop.js` | — |
| `f7893c7537` | 2026-10-25 | Maxbry | Chat: Reiniciar deja el LOOP en cero sin borrar el plan | `loop.js`, `ventana-loop.js` | — |
| `e6de7c1305` | 2026-10-25 | Maxbry | Chat: los controles del LOOP quedan a la vista | `chat-espacio.css`, `ventana-loop.js` | — |
| `7612d6255d` | 2026-10-25 | Maxbry | Chat: el LOOP ejecuta los componentes ECC en Python y JSON | `ecc-loop.json`, `ecc_motor.py`, `loop.js`, `ventana-loop.js` | +anotar, +eccPaso, +paso, +pasoMotor, +spec |
| `b3b0b714d1` | 2026-10-25 | Maxbry | Chat: el LOOP vive en LOOP-wachdog-cola y avisa al plugin | `LOOP-wachdog-cola.json`, `ecc-loop.json`, `ecc_motor.py`, `ventana-loop.js` | +etiqueta |
| `8f7c0ca8bf` | 2026-10-25 | Maxbry | Chat: el LOOP pregunta una vez al harness y dice dónde corre | `ventana-loop.js` | +avisarPlugin |
| `41388a94c3` | 2026-10-25 | Maxbry | Chat: el Watchdog tiene su botón y su ventana | `LOOP-wachdog-cola.json`, `chat-espacio.css`, `shell.js`, `ventana-watchdog.js`, `ventanas-control.js` | +guardar, +marcar, +montar, +pintar, +tomar, +ver |
| `bb7748837c` | 2026-10-25 | Maxbry | Chat: el panel del Watchdog dice minutos y separa el ciclo | `chat-espacio.css`, `ventana-watchdog.js` | — |
| `2b2cd89ae9` | 2026-10-25 | Maxbry | Chat: Activar en el Watchdog pregunta al Router | `ventana-watchdog.js` | +cable |
| `b01cf9b80a` | 2026-10-25 | Maxbry | Chat: la cola de trabajo tiene su botón y su ventana | `chat-espacio.css`, `shell.js`, `ventana-cola.js`, `ventanas-control.js` | +guardar, +montar, +pintar, +ver |
| `88f4e7d263` | 2026-10-25 | Maxbry | Chat: la ventana Cola usa el checklist del servidor | `ventana-cola.js` | +donde, +fallar, +guardarLocal, +locales, +mover, +refrescar, +sacar, +tomar · −guardar |
| `331cfc34bd` | 2026-10-25 | Maxbry | Chat: la cola muestra y marca lo hecho en el servidor | `chat-espacio.css`, `ventana-cola.js` | +marcar |
| `8d79977883` | 2026-10-25 | Maxbry | Chat: la cola muestra el nombre completo y marca con una casilla | `chat-espacio.css`, `ventana-cola.js` | — |
| `7f4e479745` | 2026-10-25 | Maxbry | Chat: la cola lista con el mismo verbo que MCP | `chat-espacio.css`, `ventana-cola.js` | — |
| `97880b8c56` | 2026-10-25 | Maxbry | Chat: la cola enciende la tool pendientes del agente | `chat-espacio.css`, `ventana-cola.js` | +leerAgente, +pintarAgente |
| `3eeb84ae2a` | 2026-10-25 | Maxbry | Chat: la cola dice si el modelo recibe la tool | `ventana-cola.js` | — |
| `6931f65cf3` | 2026-10-25 | Maxbry | Chat: la cola cabe en una línea y sigue diciendo si el modelo la recibe | `ventana-cola.js` | — |
| `077093cb8a` | 2026-10-25 | Maxbry | Chat: la cola queda en LOOP-wachdog-cola y solo usa puente_chat | `LOOP-wachdog-cola.json`, `ventana-cola.js` | — |
| `44b05ea686` | 2026-10-25 | Claude | Chat: la respuesta queda encima de la caja y los controles van en un boton | `barra-mas.js`, `chat-espacio.css`, `chat-riu2.css`, `salida-ampliada.js`, `shell.js`, `tools-ventana.js` | +alFinal, +armar, +colocar, +movil, +nombre, +soltar, +ver, +vigilar · −bajar, −medirYAplicar |
| `0f57e874e0` | 2026-10-25 | Claude | Chat: la salida ocupa la pantalla y Configuracion no se sale | `barra-mas.js`, `chat-espacio.css` | +ubicar · −ver |
| `e210f57024` | 2026-10-25 | Claude | Chat: el selector de modelo queda debajo de los botones | `barra-mas.js`, `chat-espacio.css` | — |
| `87a6986490` | 2026-10-25 | Claude | Chat: cargan las 22 animaciones Riu que el shell no aplicaba | `chat-riu2.css`, `shell.html` | — |
| `08d16e4e11` | 2026-10-25 | Claude | Chat: el modo queda en la barra, con aprobacion de tools y habilidades | `barra-mas.js`, `enviar-mensaje.js`, `mode_selector.js`, `tools-ventana.js` | +fila, +getApproval, +safeGetKey, +safeSetKey, +setApproval |
| `2efd9ba118` | 2026-10-25 | Claude | Chat: tareas programadas y artefactos reales, usables a mano y por el modelo. | `barra-mas.js`, `chat-espacio.css`, `contexto.js`, `shell.js`, `ventana-tareas.js`, `ventanas-control.js` | +avanzar, +avisarServidor, +caja, +crear, +filtra, +guardar, +instalarTool, +lanzar … |
| `760de5a930` | 2026-10-25 | Claude | Chat: los atajos Riu vuelven al chat vacío y / abre las ventanas y los comandos. | `barra-mas.js`, `chat-espacio.css`, `chat-riu2.css`, `contexto.js`, `menu-habilidades.js`, `shell.js`, `ventana-comandos.js` … (+1) | +guardarLista, +instalar, +listaComandos, +meter, +montar, +parsearBloquesComando, +pintar, +quitar … |
| `d2df9331da` | 2026-10-25 | Claude | Chat: la sesión guarda memoria, tope y revisión, y el permiso de tools es el del modo. | `barra-mas.js`, `chat-espacio.css`, `contexto.js`, `menu-habilidades.js`, `panel-chat.js`, `shell.js`, `ventana-sesion.js` … (+1) | +bloqueSesion, +estadoSesion, +guardar, +instalar, +montar, +parsearBloquesMemoria, +parsearBloquesRevision, +permiso … |
| `5b21b521b1` | 2026-10-25 | Claude | Chat: reglas e idioma viajan con el mensaje y el tope corta el envío. | `barra-mas.js`, `chat-espacio.css`, `contexto.js`, `menu-habilidades.js`, `shell.js`, `ventana-reglas.js`, `ventanas-control.js` | +bloqueReglas, +estadoReglas, +guardar, +instalar, +montar, +parsearBloquesRegla, +parsearIdioma, +pintar … |
| `75b2962aed` | 2026-10-25 | Claude | Chat: preguntar o agente usa el selector real, y las frases repetidas se guardan como comando. | `contexto.js`, `ventana-comandos.js`, `ventana-sesion.js` | +parsearModo, +ponerEnvio, +repetidos, +slug |
| `e2badbec80` | 2026-10-25 | Claude | Chat: el menú + no se sale de la pantalla y abre archivos, anclaje, claves y workflows. | `barra-mas.js`, `chat-espacio.css` | +atajos, +cuentaTareas |
| `80927439b9` | 2026-10-25 | Claude | Chat: la lista Hechas cuenta lo pendiente y el modelo puede marcarla. | `contexto.js`, `ventana-tareas.js` | +bloqueHechas, +guardarHechas, +hechas, +parsearBloquesHecho |
| `dfb0894df5` | 2026-10-25 | Claude | Chat: cuaderno guarda tareas, comandos, reglas, sesión y hechas en puente_chat. | `almacen.js`, `chat-espacio.css`, `ventana-comandos.js`, `ventana-reglas.js`, `ventana-sesion.js`, `ventana-tareas.js` | +cuadernoGuardar, +cuadernoTraer |
| `7613a5e4e8` | 2026-10-25 | Claude | Chat: botones de ventana a 40 px, selector a todo el ancho y watchdog en el cuaderno. | `barra-mas.js`, `chat-espacio.css`, `shell.css`, `ventana-watchdog.js` | — |
| `d3bad19da3` | 2026-10-25 | Claude | Chat: el cuaderno vive en el estado del MVP, la misma puerta que la cola. | `chat-espacio.css` | — |
| `ddadb246f6` | 2026-10-25 | Claude | Chat: la respuesta queda pegada a la caja y se ve si hay una tarea en curso. | `chat-espacio.css`, `chat-riu.js`, `chat-riu2.css` | — |
| `e2c088c0d2` | 2026-10-25 | Claude | Prueba e2e de LOOP, Cola y Watchdog en el panel del chat | `loop_cola_watchdog.js` | +abrir, +boton, +cerrar, +esperar, +estado, +filas, +limpiarCola, +menuMas … |
| `9d8ab5feac` | 2026-10-25 | Claude | Ventanas del composer: aria-modal, foco contenido y regiones vivas | `ventanas-control.js` | +vivo |
| `568b3b905f` | 2026-10-25 | Claude | LOOP: un paso a la vez, intervalo y tope del JSON, SIN_BACKEND y ARIA | `ventana-loop.js` | +intervalo, +parar, +pausaPor, +pedirReal, +tic, +tope |
| `5aafde38cb` | 2026-10-25 | Claude | Watchdog: vencimiento, revalidar al editar, SIN_BACKEND y ARIA | `ventana-watchdog.js` | +fin, +invalidar, +revisar, +vencer |
| `14cdd44830` | 2026-10-25 | Claude | Cola: SIN_BACKEND visible, lo hecho sobrevive sin servidor y ARIA | `ventana-cola.js` | — |
| `f56bc031df` | 2026-10-25 | Claude | El chat en el celular deja de congelarse: el rotulo de Tareas ya no reescribe el mismo texto en cada mutacion. | `barra-mas.js`, `ventana-tareas.js` |  · −cuentaTareas |
| `5477eafe82` | 2026-10-25 | Claude | Chat: en el celular Enviar es solo la flecha y queda dentro de la caja. | `barra-mas.js` | — |
| `ff1f0a6d84` | 2026-10-25 | Claude | Chat: el selector de modelo queda debajo de la caja. | `chat-espacio.css` | — |
| `26bc084bb7` | 2026-10-25 | Claude | Chat: el Router se marca al abrir y los botones vuelven en escritorio. | `api.js`, `barra-mas.js` | +anunciarRouter, +devolver |
| `f1ca591266` | 2026-10-26 | Claude | Chat: no marcar Sin conexión al abrir. | `api.js` |  · −anunciarRouter |
| `b4a0a1b178` | 2026-10-26 | Claude | Chat: tres grupos fijos; Detener y Enviar quedan fuera del carrusel. | `barra-mas.js` | +abrir, +bar, +devolverAuto, +grupo, +meter, +panel, +parqueAuto, +quitarRotulo … · −armar, −nombre |
| `f75e5fb8f7` | 2026-10-26 | Claude | Chat: Detener queda junto a Enviar; Cuaderno separa interruptores y ventanas. | `barra-mas.js` | +firma, +ids, +poner, +sec |
| `cd928309b7` | 2026-10-26 | Claude | Chat: la caja del celular deja de ocupar media pantalla. | `barra-mas.js` | — |
| `a60d691c42` | 2026-10-26 | Claude | Chat: LOOP, Cola y Watchdog llaman a nct_loop, cola50 y watchdog48. | `api.js`, `ventana-cola.js`, `ventana-loop.js`, `ventana-watchdog.js` | +accW, +ctrl, +decir, +leerEstado, +llamar, +modeloChat, +pararPoll, +plugin … |
| `1e70247ef6` | 2026-10-26 | Claude | Chat: almacenamiento local en Configuración y tool memoria junto a almacen. | `almacen-ui.js`, `shell.js`, `vercel.json` | +btn, +caja, +campo, +decir, +el, +hf, +http, +instalar … |
| `b2a696df78` | 2026-10-26 | Claude | Chat: tres selectores que abren hoja, y LOOP con Yaiwes.md por sección. | `barra-mas.js`, `ventana-loop.js` | +listaDe, +modelos · −ubicar |
| `c574c4c79f` | 2026-10-26 | Claude | Chat: los tres selectores caben en su fila y el LOOP etiqueta el modelo. | `anclaje-propuestas.js`, `barra-mas.js`, `enviar-mensaje.js`, `ventana-loop.js` | — |
| `e4fe642294` | 2026-10-26 | Claude | Chat: los tres selectores son iconos, sin los nombres inventados. | `barra-mas.js` | +svg · −sec |
| `f978be3f33` | 2026-10-26 | Claude | Chat: la fila vuelve a los iconos y Enviar queda ancho. | `barra-mas.js` |  · −ids, −poner |
| `5df85ab9a4` | 2026-10-26 | Claude | Chat: el menú extra abre encima y la caja no crece. | `barra-mas.js` | +menu |
| `6d1bc7afbf` | 2026-10-26 | Claude | LOOP: anclar Yaiwes.md llama a gobernar y pinta C0-C7. | `ventana-loop.js` | +leerGob, +pararGob, +pintarGob |
| `a07829d63a` | 2026-10-26 | Claude | Chat: la cola de mensajes se ve encima de la caja. | `enviar-mensaje.js` | +pintarCola |
| `04ad9caab8` | 2026-10-26 | Claude | LOOP: ejecutar manda skills y el sondeo muestra el resultado. | `ventana-loop.js` | — |
| `dfc8214bab` | 2026-10-26 | Claude | Chat: el campo y el modelo ocupan menos alto en el móvil. | `chat-riu2.css` | — |
| `282a52cb4f` | 2026-10-26 | Claude | Agregar al chat: filas planas como la hoja de referencia. | `agregar-al-chat.css` | — |
| `7a67e68441` | 2026-10-26 | Claude | LOOP: los ciclos usan la lista de tareas RUI que ya existe. | `ventana-loop.js` | — |
| `d9f0f620c0` | 2026-10-26 | Claude | Chat: la tarea en curso queda en una pastilla con el número. | `chat-riu.js`, `chat-riu2.css` | — |
| `75d74a2093` | 2026-10-26 | Claude | Chat: la cola de mensajes queda cerrada en una pastilla. | `enviar-mensaje.js` | — |
| `d1a785f07d` | 2026-10-26 | Claude | Chat: los botones de las ventanas dejan de ser altos. | `chat-riu2.css` | — |
| `544afe597e` | 2026-10-26 | Claude | LOOP: si gobernar falla, el aviso queda en la ventana. | `ventana-loop.js` | — |
| `ef6cfeb657` | 2026-10-26 | Claude | Chat: en el celular la barra queda en tres iconos. | `barra-mas.js` | +tres |
| `7c35c4c40a` | 2026-10-26 | Claude | LOOP: el estado ya no escribe skills. | `ventana-loop.js` | — |
| `2cc592c346` | 2026-10-26 | Claude | LOOP: el estado dice motor code, no skill. | `ventana-loop.js` | — |
| `4c7ad389bb` | 2026-10-26 | Claude | Chat: los selectores de modelo vuelven a esconderse al cambiar de vista. | `selector-modelos.js` | +asegurarHoja · −abrir, −pintar |
| `3f0806a69f` | 2026-10-26 | Claude | Chat: la ventana de arriba deja el carrusel y no acumula títulos. | `chat-riu2.css`, `shell.js` | — |
| `ed97125532` | 2026-10-26 | Claude | Chat: Anclar abre el panel completo, no la hoja que lo tapaba. | `anclaje-propuestas.js` | — |
| `1d896b26ba` | 2026-10-26 | Claude | Chat: Yaiwes.md y Tools quedan en el panel de Anclaje, sin partir el texto. | `anclaje-destinos.js`, `anclaje-propuestas.css` | — |
| `7fb36609a3` | 2026-10-26 | Claude | Chat: Paralelo queda junto a Enviar y ya no tapa el chat. | `chat-riu2.css`, `controles-chat.js` | — |
| `5174c3dd19` | 2026-10-26 | Claude | Chat: un solo Modo. Rápido, equilibrado y pensar quedan en su hoja. | `mode_selector.js`, `panel-chat.js` | — |
| `154eb36a45` | 2026-10-26 | Claude | Chat: al cambiar de vista queda un solo Auto y un solo título. | `mode_selector.js`, `shell.js` | — |
| `2bc33564aa` | 2026-10-26 | Claude | Chat: la ventana de arriba envuelve, Paralelo queda junto a Enviar y los selectores no se ven hasta abrirlos. | `anclaje-propuestas.css`, `chat-riu2.css`, `panel-chat.html`, `selector-modelos.css` | — |
| `ab46f86e87` | 2026-10-26 | Claude | Chat: las pastillas de arriba entran en los 3 selectores. Paralelo queda en la fila de Enviar. | `barra-mas.js` | +devolverPills, +meterPill · −atajos |
| `effa24f4cf` | 2026-10-26 | Claude | Chat: Paralelo queda pegado a Enviar y las filas del selector ocupan el ancho. | `anclaje-destinos.js`, `barra-mas.js` | — |
| `78ff1e99ee` | 2026-10-26 | Claude | Chat: los modelos del LOOP quedan a 36 px. Yaiwes.md y Tools abren su ventana. | `anclaje-destinos.js`, `barra-mas.js`, `chat-espacio.css`, `ventana-loop.js` | +abrirTools, +filaUna |
| `9539619444` | 2026-10-26 | Claude | Chat: Yaiwes.md abre el archivo arriba, no las notas. | `anclaje-destinos.js` | — |
| `42ea709901` | 2026-10-26 | Claude | Chat: Yaiwes.md deja un solo campo de enlace. | `anclaje-destinos.js` | — |
| `6982ece326` | 2026-10-26 | Claude | Chat: el selector de modelo queda en un icono. La lista solo sale al tocarlo. | `barra-mas.js` | +devolverModelo, +modeloChip |
| `b7c0e4cf2b` | 2026-10-26 | Claude | Chat: Paralelo queda en un icono de 34 px, junto a Enviar. | `barra-mas.js` | — |
| `90bae58e6c` | 2026-10-26 | Claude | Chat: la franja Proceso ya no aparece debajo del mensaje. | `buzon-proceso.js` | — |
| `3e58a29bec` | 2026-10-26 | Claude | Chat: la franja Proceso no puede volver a pintarse debajo del chat. | `buzon-proceso.js` | — |
| `628bdce1a6` | 2026-10-26 | Claude | Chat: pastilla para reactivar la tarea detenida. | `enviar-mensaje.js` | +envuelto, +pintarReactivar |
| `220d28d4ad` | 2026-10-26 | Claude | Chat: el sondeo de un proceso espera 48 h, no 9 min. | `api.js`, `enviar-mensaje.js` | +avisoProceso, +esTope48, +fmtReloj, +fmtTools |
| `3db6589745` | 2026-10-26 | Claude | Chat: Apagar y Reiniciar no cortan tareas en curso. | `power.js`, `power.test.js`, `ventana-servidor.js` | +haceMin, +health, +hfOk, +pedir, +resetF, +salud, +tareasEnCurso, +urlRouter |
| `798dd44b6f` | 2026-10-26 | Claude | Chat: interruptor para dejar el servidor encendido. | `ventana-servidor.test.mjs`, `ventana-servidor.js` | +buscar, +est, +json, +mantener, +match, +nodo, +pintarSw, +posts … |
| `e625c5a5ab` | 2026-10-26 | Claude | Chat: el interruptor de servidor encendido pasa a Configuración. | `panel-apariencia.html`, `panel-apariencia.js`, `ventana-servidor.test.mjs`, `ventana-servidor.js` | +pintar · −est, −mantener, −pintarSw, −posts |
| `bb34c4b31f` | 2026-10-26 | Claude | Chat: el selector de modelo vuelve a mostrar el nombre. | `barra-mas.js` | — |
| `fd6ab04f85` | 2026-10-26 | Claude | Chat: los botones de la caja quedan en dos filas alineadas. | `barra-mas.js` | — |
| `461d062959` | 2026-10-26 | Claude | Sin restricciones de tiempo: solo cuenta el del modelo (sin limite de 48 h ni timeouts del Router/Harness; el chat reintenta el envio sin tope) | `api.js` | — |
| `c3561bc9e1` | 2026-10-26 | Claude | Chat: el cubo de pensamiento queda sin fondo y cambia de escenario. | `barra-mas.js`, `enviar-mensaje.js`, `pensando-3d.css`, `pensando-3d.js` | — |
| `b49ff68aca` | 2026-10-26 | Claude | El chat nunca se rinde al perder el Router: sigue consultando el mismo proceso; tras un reinicio el Router responde 'reanudando' en vez de 404 | `api.js` | — |
| `ab4fe12cfa` | 2026-10-26 | Claude | Merge main | — | — |
| `3f43942419` | 2026-10-26 | Claude | Chat: el pensamiento usa el holograma de los videos y no tapa la píldora. | `pensando-3d.css`, `pensando-3d.js` | — |
| `98d75e8281` | 2026-10-26 | Claude | Chat: el holograma recorre los 22 componentes RUI mientras piensa. | `pensando-3d.css`, `pensando-3d.js` | — |
| `4ddbf23eaa` | 2026-10-26 | Claude | Sin mensajes extra en la salida; rama por defecto de GitHub = main; reintentos de falla pasajera, ajuste de contexto y herramienta mala sin cortar la  | `enviar-mensaje.js` | — |
| `a479af8e53` | 2026-10-26 | Claude | Chat: el holograma deja de tapar el botón y ya no muestra el rótulo RUI. | `barra-mas.js`, `pensando-3d.css`, `pensando-3d.js` | — |
| `d1d7716e1b` | 2026-10-26 | Claude | Chat: el selector encendido envía su modelo, no el Qwen 3.8 Max por defecto. | `chat-selectores.js`, `enviar-mensaje.js`, `selector-modelos.js`, `selector-resp.css` | — |
| `ea09f813ee` | 2026-10-26 | Claude | Chat: el cubo vuelve encima de la caja y dice Pensando, no cola. | `barra-mas.js`, `pensando-3d.css`, `pensando-3d.js` | — |
| `cd86794bf6` | 2026-10-26 | Claude | Chat: la burbuja dice Pensando, no En cola. | `api.js` | — |
| `3f38a025d9` | 2026-10-26 | Claude | Chat: el cubo queda en la fila cubo, borrar, detener, inicio. | `barra-mas.js`, `enviar-mensaje.js`, `pensando-3d.css`, `pensando-3d.js` | +borrar, +fila, +ordenar |
| `fb7c331b68` | 2026-10-26 | Claude | Chat: Tareas sale en la ventana LOOP, no en Ventanas. | `barra-mas.js` | — |
| `29fdec977d` | 2026-10-26 | Claude | Chat: la fila cubo, borrar, detener e inicio queda dentro de la caja. | `pensando-3d.css`, `pensando-3d.js` | — |
| `8d858f896c` | 2026-10-26 | Claude | Chat: el aviso queda bajo la barra y no tapa Enviar. | `shell-riu.css` | — |
| `58179ff9c2` | 2026-10-26 | Claude | Chat: la lista de tareas se ve dentro de la ventana LOOP. | `ventana-loop.js` | — |
| `5221f45841` | 2026-10-26 | Claude | Chat: cubo, borrar, detener e inicio quedan en la fila de Enviar. | `pensando-3d.css` | — |
| `1bbac00d62` | 2026-10-26 | Claude | Chat: Tareas abre su fuente dentro de la ventana LOOP. | `ventana-loop.js`, `ventana-tareas.js` | — |
| `7b9e21f2ba` | 2026-10-26 | Claude | Chat: el cubo vuelve encima de la caja, como antes de la fila. | `barra-mas.js`, `enviar-mensaje.js`, `pensando-3d.css`, `pensando-3d.js` |  · −borrar, −fila, −ordenar |
| `eff1aa704b` | 2026-10-26 | Claude | Chat: el historial vuelve a ser su sección y cada pestaña guarda su texto. | `panel-chat.js`, `shell.css` | — |
| `234c25e183` | 2026-10-26 | Claude | Chat: Team qwen sin modelo elegido responde el defecto del Router en vez de bloquear | `enviar-mensaje.js` | — |
| `cc7a2ed193` | 2026-10-26 | Claude | Chat: Detener queda pegado a Enviar, no suelto a la izquierda. | `barra-mas.js` | — |
| `1a426fd17c` | 2026-10-26 | Claude | Merge main | `enviar-mensaje.js` | — |
| `60eb716041` | 2026-10-26 | Claude | Merge main | — | — |
| `d536f10f64` | 2026-10-26 | Claude | Chat: el modelo que muestra la píldora es el que se envía (el chat podía traer uno viejo guardado) | `enviar-mensaje.js` | — |
| `70c9049b28` | 2026-10-26 | Claude | Chat: el cubo original vuelve a la fila de Enviar y deja de tapar el mensaje. | `barra-mas.js`, `pensando-3d.css`, `pensando-3d.js` | — |
| `02ee5717ca` | 2026-10-26 | Claude | Chat: la barra Pensando no tapa la salida y el cubo no mueve Enviar. | `barra-mas.js`, `shell.css` | — |
| `94ae9976f7` | 2026-10-26 | Claude | Chat: la píldora y el envío leen el mismo modelo (el marcado en la hoja del chat); vuelve GLM 5.3 a la lista | `chat-selector-modelos.js`, `chat-selectores.js`, `enviar-mensaje.js` | — |
| `b3e916a13e` | 2026-10-26 | Claude | Merge main | — | — |
| `4e028d545e` | 2026-10-26 | Claude | Chat: Objetivo deja de ocupar una fila y queda como icono. | `barra-mas.js` | — |
| `7a42d09ed6` | 2026-10-26 | Claude | Chat: los iconos caben en una fila y el cubo no tapa Detener. | `barra-mas.js` | — |
| `53ac8d6af5` | 2026-10-26 | Claude | Chat: Pensando vuelve al mensaje de ea09, fuera de la fila de botones. | `pensando-3d.css`, `pensando-3d.js` | — |
| `2fdd16f9cc` | 2026-10-26 | Claude | Chat: el pensamiento vuelve al cubo de hace 24 h y deja de tapar Detener. | `barra-mas.js`, `pensando-3d.css`, `pensando-3d.js` | — |
| `4204d1f9ae` | 2026-10-26 | Claude | Chat: el cubo no mueve Enviar y la barra ya no tapa el mensaje. | `barra-mas.js` | — |
| `710a4bfa66` | 2026-10-26 | Claude | Chat: el cubo de pensamiento gira otra vez y no entra en la fila de botones. | `barra-mas.js`, `pensando-3d.css` | — |
| `87311b872c` | 2026-10-26 | Claude | Chat: el pensamiento vuelve a la tarjeta de antes, encima de la caja. | `barra-mas.js`, `pensando-3d.css`, `pensando-3d.js` | — |
| `676bf8d25e` | 2026-10-26 | Claude | Chat: el cubo sale de la fila y queda en la tarjeta de encima. | `pensando-3d.css`, `pensando-3d.js`, `shell.html` | — |
| `ed64d5fa2d` | 2026-10-26 | Claude | Chat: el cubo no puede quedarse en la fila y los archivos bajan de Enviar. | `barra-mas.js`, `panel-chat.js`, `pensando-3d.js`, `shell.html`, `shell.js`, `ventanas-nuevas.js` | — |
| `fe8462d2e7` | 2026-10-26 | Claude | Chat: vuelve el selector de modelos y su envío al estado de hace 24 h (antes de d1d7716e1b) | `chat-selector-modelos.js`, `chat-selectores.js`, `enviar-mensaje.js`, `selector-modelos.js` | — |
| `62641645cb` | 2026-10-26 | Claude | Merge main | — | — |
| `2a9ee69864` | 2026-10-26 | Antonio | Fix shared model selectors and stale outgoing model identity | `chat-contexto.js`, `chat-selector-modelos.js`, `contexto.js`, `enviar-mensaje.js`, `contexto-modelo.test.mjs`, `enviar-modelo.test.mjs`, `selector-modelos.test.mjs` | +abrir, +catalogo, +enviar, +etiqueta, +filas, +gruposModelos, +ids, +label … |
| `c0178f8293` | 2026-10-26 | Antonio | Render provider audio URLs securely with usable native controls | `chat-medios.css`, `chat-medios.js`, `medios.test.mjs` | — |
| `3a389d9132` | 2026-10-26 | Antonio | Pin Pensando cube beside send button, pass anchored images to the model, name the real repo in GitHub errors | `pensando-3d.css`, `pensando-3d.js` | — |
| `0ffa146dd1` | 2026-10-26 | Antonio | Serve e2e UI before the app static route; seat the Pensando cube left of Enviar | `servidor.py`, `pensando-3d.css`, `pensando-3d.js` | — |
| `186a601ea2` | 2026-10-26 | Antonio | One click moves a selected model between Team qwen and Team 5 MVP | `chat-selector-modelos.js` | — |
| `ebb21c88cd` | 2026-10-26 | Claude | Repo en 2 raíces: router-mvp/ (mvp, router, fichas, raiz_*, componentes) y chat-router/ (chat, plugins, LOOP, harness); rutas del código ajustadas; so | `README.md`, `axe.js`, `botones.js`, `catalogo_e2e.js`, `dispositivos.js`, `eslint.config.mjs`, `inventario.js` … (+343) | — |
| `e2a20fcc96` | 2026-10-26 | Claude | Merge main en la estructura de 2 raíces | `servidor.py`, `chat-contexto.js`, `chat-medios.css`, `chat-medios.js`, `chat-selector-modelos.js`, `contexto.js`, `enviar-mensaje.js` … (+6) | — |
