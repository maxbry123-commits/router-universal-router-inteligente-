# Instrucciones de Antonio · daños · pendientes (con referencia para auditar)

Cómo auditar cualquier fila: `git show <commit> -- <archivo>` · ver el estado actual: `git blame -L <ini>,<fin> <archivo>`.
Base de comparación (antes de los cambios de Claude): `1b916a587c`. Revisión de cableado: `python3 chat/e2e/cableado.py`.

## A. Instrucciones de Antonio y su estado

| # | Instrucción | Estado | Referencia |
|---|---|---|---|
| I1 | Pasos 2 y 2.1: revisar cada botón y selector, los 22 RIU/RUI, 4 revisiones | Hecho (22 verificados) · «más de 22» no existe en el skill | `a65c5b8380`, `f6af79b3fa`, `4d21350bff` (e2e `rui.js`, `paso21.js`) |
| I2 | HTTP y MCP funcionando para Grok y Sol | Hecho en código y 221 pruebas · sin verificación viva del Space desde aquí | `b91fe2b572`, `893b45736c`, `ebdeb5505c`, `8923a7fd36`, `584bca1071` |
| I3 | Aparecen los modelos de Groq | Hecho en código · claves del Space sin confirmar | `6b2a24036e` (FE), `6d79e78b25`, `7b2430c8e8` (BE) |
| I4 | El modelo que responde = el del selector | Hecho | `a2aff6e677` (FE `chat-selectores.js`), `6d79e78b25` (BE identidad) |
| I5 | Ventana de salida 3–5 veces más amplia | Hecho · sin confirmación visual de Antonio | `8ffec72cd7`, `a80f5bc400`, `f8a536e65a`, `9fd44c13e4` |
| I6 | Botones LLM tool y Agente tool (ON/OFF reales) | Hecho (estado del servidor) · t4 necesita IA ON | `8ffec72cd7`, `5f7c08eacd`, `f76858c6dd`, `548c387b8e`, `1b916a587c` (BE `control.py`) |
| I7 | Botón «Nuevo proyecto» | **PENDIENTE** (solo existe en el panel superior) | D8 abajo |
| I8 | 3 selectores Modelo · Permisos · Herramientas con dibujo 2D | Hecho pero Antonio dice «amorfos» → **rediseñar** | `a34ccf2482` |
| I9 | Selector superior como ventana (no carrusel) y modelos dentro de un selector | Hecho en `a34ccf2482` · sin confirmación de Antonio | `a34ccf2482` |
| I10 | Revisar que el banco tiene claves de Groq | Hecho en código (el banco guarda GROQ_* y NVIDIA_*) | `7b2430c8e8` |
| I11 | Botón Detener visible | **PENDIENTE** (aparece solo al enviar) | `5fc6df588d`, D2 |
| I12 | Simulador de pensamiento (cubo + segundos) | **PENDIENTE** | D1 |
| I13 | «Antes el modelo iba diciendo lo que hacía» | **PENDIENTE** (backend) | D4 |
| I14 | Más de 22 componentes RIU/RUI visibles | **PENDIENTE** (22 instalados; 23–25 no existen en el skill) | D9 |
| I15 | Trazabilidad forense X-Ray | Hecho | `docs/AUDITORIA_FRONTEND_XRAY.md`, `docs/TRAZABILIDAD_CHAT.md` |
| I16 | Bloques para Grok (revisión, instrucciones, build) | Hecho | `docs/GROK_BLOQUES.md`, `1aef5be56b` |
| I17 | Código del frontend dividido, no monolítico | Hecho en `panel-chat.js` y `chat-riu2.js` · quedan 6 archivos >150 líneas | `43c3163bb8` |
| I18 | Todo a `main` siempre | Hecho | cada commit está en `main` |
| I19 | Dos raíces (backend y frontend) con índice y handoff | Hecho (índices y handoff; los archivos NO se movieron, ver §D) | `chat/docs/backend/`, `chat/docs/frontend/` |
| I20 | Reglas del repo (`CLAUDE.md`): inspeccionar, no romper, modificar solo lo autorizado | Incumplido en D1, D2, D5 (ver B) | `CLAUDE.md` |

## B. Lo que se dañó o cambió sin pedirlo (código y commit)

### Frontend
| # | Daño | Dónde | Commit | Estado |
|---|---|---|---|---|
| D1 | Desapareció el cubo 3D y los segundos del pensamiento | `composer-filas.js`: `QUEDAN` no incluye `.p3d`; `ordenar()` lo manda a la hoja oculta Herramientas | `a34ccf2482` | PENDIENTE |
| D2 | Detener oculto en reposo | `composer-filas.js` / `panel-chat.js` | `a34ccf2482`, `5fc6df588d` | PENDIENTE |
| D3 | 17 controles movidos de la pantalla a hojas (lista en `docs/AUDITORIA_FRONTEND_XRAY.md` §4) | `composer-filas.js` | `a34ccf2482` | Intencional, rechazado por Antonio |
| D5 | Etiquetas de modo cambiadas sin pedirlo («Rápido — 512 tok» → «Responde directo», etc.) | `panel-chat.js` | `548c387b8e` | PENDIENTE |
| D6 | Etiqueta NVIDIA con sufijo «(sin NVIDIA en el Router: responde Qwen)» | `chat-selectores.js` / `fichas-externas.js` | `6b2a24036e` | Revisar |
| D7 | El chat no cargó ~10 min: un comentario `//` se tragó el resto de la línea | `api.js` | `8ffec72cd7` → arreglo `5f7c08eacd` | Arreglado + chequeo de sintaxis y eslint antes de subir |
| D8 | Sin botón de proyecto en caja/Herramientas | — | decisión de base | PENDIENTE |
| D10 | `actualizarMIA` sin definir (inofensivo, protegido por `typeof`) | `chat-selector-modelos.js:66` | `11eb8842e8` (Maxbry) | Latente |
| D11 | Un revert completo del frontend (`3485f7ccc3`) y reintegración posterior (`548c387b8e`) mezcló versiones: de ahí D5 | todo el frontend | `3485f7ccc3`, `548c387b8e` | Copias en `docs/legado/frontend_cambios_claude/` |
| D12 | `selector-diagrama` / `selectores-panel`: ids pedidos y nunca creados (rama muerta) | `chat-selectores.js:126,157,194` | `a2aff6e677` | Código muerto, sin efecto |
| D13 | Paneles Archivos, Canvas, Organización y Seguimiento llaman a `/chat/documents` y `/chat/org/*`, que el Router MVP no sirve (solo el router viejo `router/integration/chat_mvp/router.py`) | `panel-archivos.js`, `panel-canvas.js`, `panel-org.js`, `panel-seguimiento.js` | de la base | Fuera de alcance del chat; ver pendientes |

### Backend
| # | Daño | Dónde | Commit que lo causó → arreglo |
|---|---|---|---|
| B1 | Identidad del modelo tapada por el historial («Soy deepseek…») | `mvp/app.py` `_chat_ficha` | capas `748db5a6e5` → `6d79e78b25` |
| B2 | Harness 500 con argumento inválido de herramienta | `plugins/deepseek_harness/server.py` | base → `8ffec72cd7` |
| B3 | 403 sin causa | `plugins/router_api_cliente.py` | base → `893b45736c` |
| B4 | Alias `ficha-qwen38max` rechazado | `mvp/modelos.py` | base → `b91fe2b572` |
| B5 | Lectura de HF devolvía datos viejos tras guardar | `mvp/hf_store.py` | base → `b91fe2b572` |
| B6 | `/memoria` podía pisar el historial si la lectura fallaba | `mvp/memoria.py` | `c28df985d0` → `b91fe2b572` |
| B7 | Ejecutor de pruebas truncado (`correr.py`) | `mvp/pruebas_vivo/correr.py` | `6eea412749` → `9befcbba75` |
| B8 | Falsos FAIL por `request_id` repetido | `mvp/pruebas_vivo` | `2ee2f1ff3a` → `65ca65ef78` |
| B9 | Clave de acceso `RIU_MCP_KEY` tapada por `RIU_API_KEY` | `mvp/app.py` `verificar` | base → `584bca1071` |
| B10 | El Router se reiniciaba por cambios solo de pantalla/documentos | `mvp/run.py` autopull | base (autopull) → `70cc3661f4` |
| B11 | t6 caía con KeyError | `mvp/pruebas_vivo/pruebas.py` | `e960e04110` → `b91fe2b572` |

## C. Pendientes disponibles (ordenados)

### Frontend (Salida 2, esperan tu orden)
1. D1 cubo + segundos junto a Enviar, visible mientras trabaja: añadir `.p3d` a `QUEDAN` en `composer-filas.js`.
2. D2 Detener siempre visible como en la base.
3. D5 devolver las etiquetas de modo originales (`panel-chat.js`, lista `[["fast",…],…]`).
4. D8 «Nuevo proyecto» en Herramientas (`RIU_ANCLA_ABRIR("proyecto")`).
5. Rediseñar los 3 selectores y sus hojas (necesito ejemplo o referencia visual tuya).
6. D9 hacer visibles los 22 RIU; tú confirmas qué son el 23–25.
7. D6 decidir el sufijo de las fichas NVIDIA.
8. D13 decidir qué hacer con los 4 paneles que llaman a `/chat/documents` y `/chat/org/*`.
9. Seguir dividiendo: `api.js` 278, `chat-ancla.js` 247, `anclaje-propuestas.js` 209, `chat-selectores.js` 208, `agentes-mirror.js` 192, `panel-apariencia.js` 171, `tools-ventana.js` 163, `almacen-archivos.js` 149, núcleo de `panel-chat.js`.
10. Limpiar D12 (código muerto) y D10.
11. Comprobar en el móvil real que Vercel sirve el último commit (recargar dos veces).

### Backend
1. D4 pasos en vivo («iba diciendo lo que hacía»): emitir progreso de herramientas desde el Harness / `_llamar_modelo` en el chat de texto.
2. Confirmar que el Space tiene `GROQ_API_KEY*` y `NVIDIA_API_KEY*` (`salud` cuenta las claves).
3. t4 (delegación LLM): tú enciendes IA en el chat; luego Sol/Grok repiten.
4. Probar en vivo los modelos de texto restantes y los medios (Sol, GPT, Grok): `python3 -m mvp.pruebas_vivo.guion`.
5. Pruebas para `/chat/agents`, `/chat/github/accounts`, `mcp_cliente.py`, `sala_turno.py` (el auditor de cableado los marca).
6. Cambiar la rama por defecto de GitHub (hoy `reorganizacion`).
7. Revocar el token HF expuesto (acción tuya).

## D. Por qué las dos raíces no movieron archivos
Mover `chat/frontend/` rompe el despliegue de Vercel (`vercel.json`, `build.sh`, imports `/chat/ui/…`) y mover `mvp/` rompe el arranque del Space (`mvp.run`, autopull). `CLAUDE.md` prohíbe cambiar la arquitectura sin autorización. Las raíces son por tanto **índices verificados** (`chat/docs/frontend/`, `chat/docs/backend/`). Si quieres moverlas de verdad, dime y lo hago con prueba de despliegue.
