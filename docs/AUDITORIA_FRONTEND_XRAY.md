# Auditoría forense (X-Ray) del frontend del chat — trazabilidad

Generada el 2026-10-25 con `git log`, `git diff 1b916a587c HEAD` y un inventario de controles en navegador (Chromium, 345×700, base vs. actual). Alcance: `plugins/chat-router/frontend/`. Los datos salen de comandos reales, no de memoria.

## 1. Resumen
- **Base de comparación:** `1b916a587c`, el último estado anterior al primer cambio de Claude al frontend (23-oct). Es la «pantalla vieja» de Antonio.
- **Commits que tocaron el frontend desde el 20-oct:** 40 (10 de Maxbry, 30 de Claude). Lista completa en el Anexo A.
- **Diferencia neta base → hoy:** 26 archivos (14 nuevos, 12 modificados), +604/−63 líneas antes de dividir el código (ver §5).
- **Primera ola de Claude (23–24 oct, 12 commits `62fbb681c4`…`8557028764`):** se REVIRTIÓ entera con `3485f7ccc3` porque rompió la pantalla (Maxbry UI re-maquetó el composer y escondió botones). Copia completa en `docs/legado/frontend_cambios_claude/`.
- **Segunda ola (24–25 oct):** reintegración quirúrgica; en ella están los daños de §3.

## 2. Qué cambió Claude respecto a la base (lo que está vivo hoy)
| Archivo | Cambio | Pedido por Antonio |
|---|---|---|
| `chat-selectores.js` | filas con ⓘ, ⚡, ON/OFF, «Modelo: …»; fila Groq; ON/OFF ya no bloquea a los demás | sí (selectores) |
| `tools-ventana.js` | chips IA / Agentes / System prompt con estado del servidor | sí |
| `pendientes-panel.js` | checklist + «Organizar con IA»; icono de línea | sí |
| `panel-chat.js` (+ módulos nuevos) | botón Continuar, aviso de modo, modelo Groq, LLM/Agente tool = chips | sí / parcial |
| `panel-chat.html`, `chat-ventanas.js`, `anclaje-destinos.js` | texto «yaiwes.md» en lugar de «Mi handoff» | sí |
| `api.js` | `herramientas_usadas` y `aviso` del Router MVP | no pedido (compatibilidad) |
| `chat-medios.js/.css` | `[[imagen:]] [[video:]] [[audio:]]` dentro de la burbuja | sí |
| `fichas-externas.js` | modelos reales de Groq/NVIDIA | sí |
| `composer-filas.js/.css`, `chat-pulido.css` | caja nueva: texto+Enviar y 3 selectores (Modelo · Permisos · Herramientas), ⤢ salida grande | sí, **con daños (§3)** |
| `ventana-conexiones.js`, `ventana-room.js`, `ventana-servidor.js`, `ventanas-control.js/.css`, `api/power.js` | Conexiones, ROOM CONFERENCIAS, Servidor | sí (Paso 2.1) |
| `shell.js`, `shell.html`, `vercel.json` | enlaces de los módulos/CSS nuevos; reescrituras de Vercel | necesario |
| `selector-resp.css`, `chat-riu2.js` | contraste AA; título de bienvenida como encabezado | accesibilidad |

## 3. Qué se dañó o cambió sin pedirlo (con evidencia)
| # | Daño | Evidencia | Causa (commit) | Estado |
|---|---|---|---|---|
| D1 | **Desapareció el simulador de pensamiento (cubo 3D + segundos)** | prueba `narracion.js`: base → cubo `visible`; actual → `nunca` | `a34ccf2482` (`composer-filas.js`): al ordenar la barra movió `.p3d` dentro de la ventana Herramientas (oculta) | **PENDIENTE (Salida 2)** |
| D2 | **Botón Detener ya no está a la vista en reposo** | inventario: `btn-detener` visible en la base, «oculto» hoy; solo aparece mientras trabaja | `a34ccf2482` / `5fc6df588d` | PENDIENTE: decidir visible siempre (como la base) |
| D3 | **17 controles pasaron de la pantalla a ventanas** (lista en §4) | inventario base vs. actual | `a34ccf2482` | Intencional (pedido de ganar espacio), pero Antonio dice que no cumple el diseño |
| D4 | **«Antes el modelo iba diciendo lo que hacía»** | misma prueba: los textos de espera son `Enviando…` y `En cola…` en base y hoy; el MVP no manda pasos de herramientas | **no es regresión del frontend**: el Router MVP no emite `progreso` en chats de texto (solo en medios) | PENDIENTE backend |
| D5 | **Etiquetas de modo cambiadas sin que se pidiera** («Rápido — 512 tok» → «Responde directo», «Equilibrado — 1024 tok» → «Por defecto», «Pensar — 2048 tok» → «Razona antes de responder») | `git diff 1b916a587c HEAD -- panel-chat.js` | `548c387b8e` (reintegración del legado) | PENDIENTE: devolver las etiquetas originales |
| D6 | Etiquetas de fichas NVIDIA («NV Muse Glimmer 30B») ahora llevan sufijo «(sin NVIDIA en el Router: responde Qwen)» | inventario | `6b2a24036e` | Intencional (evita engañar), revisar con Antonio |
| D7 | El chat dejó de cargar ~10 min por un comentario `//` que se tragó el resto de una línea en `api.js` | commit `5f7c08eacd` | `8ffec72cd7` | Corregido; ahora hay chequeo de sintaxis y `no-undef` antes de cada subida |
| D8 | «Botón para crear proyecto no existe» | el botón `Proyectos` existe solo en el panel superior (Chat ▾); no está en la caja ni en Herramientas | decisión de diseño de la base | PENDIENTE (Salida 2): ponerlo en Herramientas |
| D9 | «Más de 22 componentes RIU no existen» | el skill Maxbry UI define **22** (`RARE` en `FROMTED-YAIWES-PRUEBA-PALETA-V07.html`); están instalados y una prueba revisa cada uno (23 PASS), pero casi todos son sutiles | no hay 23–25 en el skill | PENDIENTE: hacerlos visibles (Salida 2) y confirmar con Antonio dónde están el 23–25 |
| D10 | Latente: `actualizarMIA` no definida en `chat-selector-modelos.js:66` | `eslint no-undef` | `11eb8842e8` (Maxbry), protegida por `typeof` | Inofensiva |

## 4. Controles que estaban a la vista en la base y hoy están dentro de una ventana
`btn-adjunto`, `btn-archivos`, `btn-ancla`, `btn-sandbox`, `btn-microfono`, `btn-copiar-input`, `Modo: Auto`, `btn-detener`, `btn-tools`, `btn-pendientes`, `sel-ngt`, `sel-nuevo`, `sel-mvp`, `sel-cc`, `sel-cf`, `sel-workflows`, `ON/OFF workflow Loops code Yaiwes`.
Entre ellos están TODOS los selectores de modelo (`sel-ngt`, `sel-nuevo`, `sel-mvp`, `sel-cc`, `sel-cf`, `sel-workflows`), que ahora se abren desde el selector **Modelo**.

## 5. División del código en archivos (no monolítico)
Hecha el 25-oct con herramienta automática (acorn) que mueve el bloque sin cambiar la lógica y pasa lo que usa por `ctx`:
| Antes | Ahora |
|---|---|
| `panel-chat.js` 818 líneas | **408** + `buzon-proceso.js`, `selects-secundarios.js`, `ventana-sandbox-chat.js`, `ventana-motor.js`, `selector-ancla.js`, `controles-chat.js`, `enviar-mensaje.js`, `pildora-ficha.js` |
| `chat-riu2.js` 307 líneas | **15** + `riu-util.js`, `riu-campana.js`, `riu-navegacion.js`, `riu-chats.js`, `riu-reacciones.js`, `riu-paneles.js`, `riu-entrada.js` |
Quedan sin dividir (>100 líneas): `panel-chat.js` (núcleo multi-chat y hojas, usan variables `let` compartidas), `api.js` 278, `chat-ancla.js` 247, `anclaje-propuestas.js` 209, `chat-selectores.js` 208, `agentes-mirror.js` 192, `panel-apariencia.js` 171, `tools-ventana.js` 163, `almacen-archivos.js` 149.
Verificación tras dividir: 221 pruebas del Router, 10+10 escenarios de modelos, 32 del chat, 60 de la caja de escritura, 23+23 RUI, 23+23 Paso 2.1, 18 de teclado, 0 fallos de accesibilidad, auditoría de clic en cada ventana, `node --check` de todos los `.js` y `eslint no-undef` (1 aviso inofensivo, D10).

## 6. Pendiente de la Salida 2 (arreglos del frontend)
1. D1 devolver el simulador de pensamiento junto a Enviar, visible mientras trabaja.
2. D2 botón Detener visible como en la base.
3. D5 devolver las etiquetas de modo originales.
4. D8 botón Proyectos en Herramientas.
5. Rediseñar los selectores (aspecto «amorfo») con ejemplos de Antonio.
6. D9 componentes RIU visibles; confirmar 23–25.
7. D4 (backend): pasos de herramientas en vivo para el chat de texto.

## Anexo A — los 40 commits que tocaron el frontend (git log real)
| # | commit | autor | fecha | qué cambió (resumen del commit) | archivos del frontend tocados (+/-) |
|---|---|---|---|---|---|
| 1 | `11eb8842e8` | Maxbry | 2026-10-21 | fix(public_chat_app): excepts de anyio y autopull loguean type(exc).__name__ sin cambiar flujo | .gitignore (+1/-0), acceso-clave.css (+7/-0), acceso-clave.js (+64/-0), agentes-mirror.js (+192/-0), agregar-al-chat.css (+15/-0), agregar-al-chat.js (+60/-0), almacen-archivos.css (+18/-0), almacen-archivos.js (+149/-0), almacen.js (+6/-0), anclaje-destinos.js (+102/-0), anclaje-mejoras.css (+19/-0), anclaje-mejoras.js (+135/-0) …+484 más |
| 2 | `6208f52bf7` | Maxbry | 2026-10-22 | chat: cerrar selector y controles | api.js (+7/-7), panel-chat.html (+1/-0), panel-chat.js (+14/-8), tools-ventana.js (+2/-2) |
| 3 | `fb653e8d46` | Maxbry | 2026-10-22 | chat: enrutar el selector Qwen y ampliar la espera de respuesta | api.js (+2/-2) |
| 4 | `93be675bfe` | Maxbry | 2026-10-22 | fix(chat-ui): compactar editor autoajustable y ampliar salida del modelo | chat-espacio.css (+7/-11), panel-chat.js (+11/-2) |
| 5 | `be896f6774` | Maxbry | 2026-10-22 | chat: validar modelos del catalogo y ejecutar herramientas GitHub y HF desde el banco | api.js (+1/-1), chat-selector-modelos.js (+13/-25), panel-chat.js (+5/-4), tools-ventana.js (+3/-1) |
| 6 | `71664b7640` | Maxbry | 2026-10-23 | chat: limitar interruptores a IA delegada, conservar contexto y continuar respuestas truncadas | panel-chat.js (+5/-4), tools-ventana.js (+4/-4) |
| 7 | `1ca3f8af2c` | Maxbry | 2026-10-23 | fix(frontend): exportar conectarSelectores para cargar la interfaz del chat | chat-selectores.js (+3/-1) |
| 8 | `c456907f71` | Maxbry | 2026-10-23 | fix(chat): restaurar HTML truncado de ventanas y selectores sin perder controles nuevos | panel-chat.html (+18/-1) |
| 9 | `57931a7f58` | Maxbry | 2026-10-23 | chat: corregir ancho movil de IA, reintentar catalogo y omitir LIVE_URL inexistente | api.js (+1/-0), chat-movil.css (+1/-0), chat-selector-modelos.js (+10/-3), config.js (+3/-3) |
| 10 | `85eb29f018` | Maxbry | 2026-10-23 | chat: cargar dimensiones del editor antes de calcular su altura inicial | shell.html (+1/-0) |
| 11 | `62fbb681c4` | Claude | 2026-10-23 | chat: IA/agentes ON/OFF desde el servidor, ventanas de Conexiones y ROOM, checklist de pendientes | controles-ventana.js (+115/-0), panel-chat.js (+2/-1), pendientes-panel.js (+30/-1), shell.js (+1/-0), tools-ventana.js (+22/-5) |
| 12 | `59f811887e` | Claude | 2026-10-23 | chat: Maxbry UI (composer ordenado, ＋ Agregar al chat, chips, toast), salida ancha y backend de archivos/sandbox/proyectos/pensamiento | chat-maxbry.css (+90/-0), controles-ventana.js (+1/-1), maxbry-ui.js (+87/-0), panel-chat.html (+1/-0), panel-chat.js (+2/-2), pendientes-panel.js (+1/-1), shell.html (+1/-0), shell.js (+1/-0), tools-ventana.js (+3/-3) |
| 13 | `28bcf2b6f3` | Claude | 2026-10-23 | chat: handoff_texto, filas de selector como mode-option y documentacion Maxbry UI + verificacion cruzada | chat-maxbry.css (+8/-0) |
| 14 | `9607eb66ad` | Claude | 2026-10-23 | chat: boton Servidor (encender/apagar/reiniciar) via /api/power en Vercel, vercel.json y CORS del Router | api/power.js (+26/-0), controles-ventana.js (+22/-1), maxbry-ui.js (+5/-4), test/power.test.js (+43/-0), vercel.json (+11/-0) |
| 15 | `62c3e0d1ee` | Claude | 2026-10-23 | mvp: los 23 modelos del plan Standard (13 texto, 3 imagen, 3 audio, 4 video) con generacion multimedia y medios en el chat | chat-maxbry.css (+5/-0), maxbry-ui.js (+15/-1) |
| 16 | `7548c2cc87` | Claude | 2026-10-23 | chat: agentes conectables (1 a 50, cada uno con su modelo) y dos botones separados IA / Agentes | chat-maxbry.css (+6/-6), maxbry-ui.js (+2/-2), tools-ventana.js (+21/-18) |
| 17 | `748db5a6e5` | Claude | 2026-10-24 | Chat: capa de formato, system prompt ON/OFF, yaiwes.md global, organizador de pendientes, constitucion y pendientes al modelo | anclaje-destinos.js (+3/-3), chat-maxbry.css (+5/-5), chat-ventanas.js (+3/-3), maxbry-ui.js (+1/-1), panel-chat.html (+1/-1), panel-chat.js (+2/-2), pendientes-panel.js (+3/-1), tools-ventana.js (+6/-3) |
| 18 | `24b26c7735` | Claude | 2026-10-24 | Boton Servidor: usa HF_TOKEN_1 del entorno de Vercel | api/power.js (+1/-1) |
| 19 | `5be2929688` | Claude | 2026-10-24 | ROOM: turno de agentes y modelos; READMEs de arquitectura/handoff; raiz limpia | controles-ventana.js (+3/-1) |
| 20 | `54c8815ea0` | Claude | 2026-10-24 | Chip System prompt junto a IA y Agentes (antes quedaba deformado en la fila de acciones) | maxbry-ui.js (+1/-1) |
| 21 | `70cc3661f4` | Claude | 2026-10-24 | Chat: botones del composer visibles como antes; el Router no se reinicia por cambios solo de pantalla o documentos | maxbry-ui.js (+3/-1) |
| 22 | `8557028764` | Claude | 2026-10-24 | Selectores: ON/OFF, info, rapida y modelo por fila (RIU_SELECTORES) sin tocar el resto del frontend | chat-maxbry.css (+3/-0), chat-selectores.js (+40/-0), shell.html (+1/-0) |
| 23 | `3485f7ccc3` | Claude | 2026-10-24 | Frontend del chat: volver al estado anterior a los cambios de Claude (base 1b916a587c); se conserva vercel.json para que Vercel sirva /chat/ | anclaje-destinos.js (+3/-3), api/power.js (+0/-26), chat-maxbry.css (+0/-106), chat-selectores.js (+0/-40), chat-ventanas.js (+3/-3), controles-ventana.js (+0/-138), maxbry-ui.js (+0/-104), panel-chat.html (+1/-2), panel-chat.js (+5/-6), pendientes-panel.js (+2/-33), shell.html (+0/-2), shell.js (+0/-2) …+2 más |
| 24 | `a2aff6e677` | Claude | 2026-10-24 | Cableado del selector: RIU_SELECTORES (el chat nunca recibia el selector encendido y mandaba siempre el modelo por defecto). Solo chat-selec | chat-selectores.js (+40/-0), shell.html (+1/-0) |
| 25 | `548c387b8e` | Claude | 2026-10-24 | Chat: reintegrar chips IA/Agentes/System prompt (estado del servidor), checklist de pendientes, boton Continuar, medios en la burbuja y text | anclaje-destinos.js (+3/-3), chat-medios.css (+5/-0), chat-medios.js (+17/-0), chat-ventanas.js (+3/-3), panel-chat.html (+1/-1), panel-chat.js (+6/-5), pendientes-panel.js (+33/-2), shell.html (+1/-0), shell.js (+1/-0), tools-ventana.js (+34/-11) |
| 26 | `c28df985d0` | Claude | 2026-10-24 | Chat: /memoria en el Router (historial y pestañas entre dispositivos), chips en píldora con punto de estado, diagrama ⓘ sin desbordar, icono | chat-pulido.css (+15/-0), pendientes-panel.js (+1/-1), shell.html (+1/-0) |
| 27 | `af633b9819` | Claude | 2026-10-24 | Chat móvil: el selector de workflows y los accesos que buscan controles movidos a la pestaña móvil vuelven a funcionar; los controles de otr | chat-selectores.js (+1/-1), panel-chat.js (+1/-1), shell.js (+1/-0) |
| 28 | `a65c5b8380` | Claude | 2026-10-24 | Chat: el diagrama ⓘ de cada selector tiene el botón Recorrer (RUI 15); los 22 componentes RUI verificados en móvil y escritorio | chat-selectores.js (+1/-1) |
| 29 | `f6af79b3fa` | Claude | 2026-10-24 | Paso 2.1: ventanas Conexiones, ROOM CONFERENCIAS (con turno de los agentes y lista de invitables) y Servidor (api/power en Vercel) en módulo | api/power.js (+26/-0), shell.html (+1/-0), shell.js (+3/-0), test/power.test.js (+43/-0), ventana-conexiones.js (+48/-0), ventana-room.js (+50/-0), ventana-servidor.js (+24/-0), ventanas-control.css (+6/-0), ventanas-control.js (+25/-0) |
| 30 | `cbd1647056` | Claude | 2026-10-24 | Conexiones: quitar una conexión (libera el tope de 10 y vacía su secreto); contraste WCAG AA en los 7 temas (texto encendido, respuestas de  | chat-pulido.css (+3/-0), chat-riu2.js (+1/-1), selector-resp.css (+2/-2), ventana-conexiones.js (+1/-0), ventanas-control.css (+4/-1) |
| 31 | `9fd44c13e4` | Claude | 2026-10-24 | Chat escritorio: Enviar siempre a la vista (altura medida desde el inicio real del chat) y sin «Enviar Enviar»; chips sin disabled para no p | chat-pulido.css (+5/-1), panel-chat.js (+2/-2), tools-ventana.js (+2/-2) |
| 32 | `6b2a24036e` | Claude | 2026-10-24 | Selector NVIDIA/Groq: la hoja lista los modelos reales de Groq/NVIDIA del Router (las fichas viejas nv-* respondían con Qwen) y la fila mues | chat-selectores.js (+2/-1), fichas-externas.js (+28/-0), panel-chat.js (+2/-0), shell.js (+1/-0) |
| 33 | `8ffec72cd7` | Claude | 2026-10-24 | Chat: salida más grande (caja de escritura en filas, herramientas deslizables, ⤢ salida grande); LLM tool y Agente tool = mismos permisos de | api.js (+1/-1), chat-pulido.css (+0/-2), composer-filas.css (+23/-0), composer-filas.js (+27/-0), panel-chat.js (+12/-27), shell.html (+1/-0), shell.js (+1/-0) |
| 34 | `5f7c08eacd` | Claude | 2026-10-24 | Chat: arreglo urgente de api.js (un comentario cortaba la línea y el chat no cargaba); LLM/Agente tool muestran el estado real al recargar | api.js (+2/-1), panel-chat.js (+1/-1) |
| 35 | `f76858c6dd` | Claude | 2026-10-24 | Chat: al abrir vuelve a leer los permisos del servidor (y pide la clave si es incorrecta) | panel-chat.js (+1/-0) |
| 36 | `a80f5bc400` | Claude | 2026-10-24 | Chat móvil: caja de escritura en rejilla (texto + Enviar en la misma fila, chips de estado siempre visibles, herramientas con botón propio q | composer-filas.css (+23/-0), composer-filas.js (+13/-4) |
| 37 | `1d7b22c499` | Claude | 2026-10-24 | Chat escritorio: el botón de herramientas solo existe en móvil | composer-filas.css (+1/-1) |
| 38 | `a34ccf2482` | Claude | 2026-10-25 | Chat: debajo del texto 3 selectores (Modelo · Permisos · Herramientas) con dibujo 2D y nombre que abren su ventana; los selectores de modelo | chat-selectores.js (+6/-5), composer-filas.css (+38/-40), composer-filas.js (+48/-25), fichas-externas.js (+48/-20), panel-chat.html (+1/-0), panel-chat.js (+5/-3), tools-ventana.js (+1/-1) |
| 39 | `f8a536e65a` | Claude | 2026-10-25 | Chat escritorio: Enviar compacto al lado del texto | composer-filas.css (+1/-0) |
| 40 | `5fc6df588d` | Claude | 2026-10-25 | Chat: Detener aparece en cuanto se envía | composer-filas.js (+2/-1) |
