# Inventario de componentes

Líneas de `index.html` (upload `064f4a74`), `app.js` (`c8312e59`) y `styles.css` (`dff2f49e`). Son los archivos del chat-referencia, no el repo. Los slots del manifest son `mainContent`, `inspector`, `sideNav`, `bottomNav`, `sheetInner`, `chatMessages`, `fileRows`, `wallGrid`.

## Estructura de la app

| Componente | Dónde se define | Notas |
|---|---|---|
| Sidebar + logo + mini preview | `index.html:41-48`; estilos `.sidebar`, `.mini-preview` | Oculta bajo 770 px. Muestra el tema activo (`#sidebarThemeName`) |
| Navegación lateral | `nav()` en `app.js:59-64` → `#sideNav` (slot `sideNav`) | Cuatro entradas: chat, files, wall, settings. `data-nav` |
| Navegación inferior (móvil) | `index.html:64` `#bottomNav`; mismo markup de `nav()` | Visible solo bajo 770 px (`.bottom-nav`) |
| Topbar | `index.html:50-58`; estilos `.topbar` | Estado de bridge `#topBridgeStatus`, exportar rápido (`index.html:55`) |
| Área principal | `index.html:60` `#mainContent` (slot `mainContent`); `refresh()` en `app.js:96-109` | Se reemplaza entera en cada refresh (hallazgo 5) |
| Inspector | `index.html:61` `#inspector`; `drawInspector()` en `app.js:65-68` | Oculto bajo 1160 px. Muestra tema, modelo, modo y bridge |
| Cabecera de página | `intro()` en `app.js:70` | Kicker, título y descripción |
| Sheet (modal) | `index.html:66` `<dialog id="sheet">`; `openSheet()` `app.js:165-182`; `closeSheet()` `:183` | Cuatro tipos: `mode`, `root`, `new-root`, `reset`. Se cierra con clic en el velo |
| Toast | `index.html:69` `#toastArea`; `toast()` `app.js:112-116` | Máximo 3. Se borra a los 4 s. Variantes `success` y `error` |

## Chat

| Componente | Dónde | Notas |
|---|---|---|
| Cabecera del chat | `chatPage()` `app.js:73-74` | Hero con overline y frase |
| Botón nuevo chat | `app.js:75` (`chat.close`) | |
| Lista de mensajes | `app.js:72`, `76` (`#chatMessages`, slot `chatMessages`) | Burbujas `.chat-bubble`, usuario a la derecha |
| Selector de modelo | `app.js:77` (`#modelSelect`) | La lista de modelos está en `app.js:39`, no se copia aquí |
| Botón de modo | `app.js:77` (`data-action="mode.open"`) | Abre el sheet `mode` |
| Composer | `app.js:78` (`#chatForm`, `#composeText`) | Textarea con `maxlength` 20000. Enviar: botón o Ctrl/Cmd+Enter (`app.js:239`) |
| Adjuntos (chips) | `app.js:79` | Se quitan con `data-remove-attach` |
| Herramientas | `app.js:80` (`data-tool` document, website, image) | Toggle con `aria-pressed` |
| Botón enviar | `app.js:80` (`#sendButton`) | Deshabilitado mientras `sending` |
| Aviso de bridge | `app.js:81`; estilos `.chat-notice` | Texto `connected` u `offline_note` |
| Envío | `send()` `app.js:148-164` | Ver `actions-contract.md`, hallazgo 1 |

## Archivos

| Componente | Dónde | Notas |
|---|---|---|
| Barra de búsqueda | `app.js:84`, `229-230` (`#fileSearch`) | Actualiza solo `#fileRows`, no todo el DOM |
| Pestañas Local / Anclados | `app.js:86` (`role="tab"`, `aria-selected`) | El `aria-selected` está presente |
| Filas de archivo | `app.js:85` (`#fileRows`, `.file-row`) | Nombre con `esc()`, tamaño y estado |
| Acciones de fila | `app.js:85` (pin, descargar, borrar) | Descargar: `download()` `:135-139`. Borrar: `:209` (sin evento) |
| Añadir archivos | `app.js:86, 118-133` (`addFiles`) | Máximo 20 por vez. Límite 1 MB por archivo para guardar |

## Crazy Wall

| Componente | Dónde | Notas |
|---|---|---|
| Flujo | `app.js:90` (`.flow-track`) | Etiquetas fijas en español (hallazgo 9) |
| Tarjetas de raíz | `wallPage()` `app.js:88-91` (slot `wallGrid`); `.root-card` | Seis raíces de referencia, marcadas como LOCALES |
| Editar raíz | `openSheet('root')` `app.js:172-175` | Estado (pending, progress, enabled, warning) y nota (5000 caracteres máx.) |
| Nueva raíz | `openSheet('new-root')` `app.js:176`; `data-add-root` `:220-223` | Nombre máx. 150, descripción máx. 300 |

## Configuración

| Componente | Dónde | Notas |
|---|---|---|
| Selector de tema | `settingsPage()` `app.js:93` (`#themeGrid`); `theme()` `:111` | Miniaturas con `THEMES` (`app.js:8-14`), que no coinciden con el CSS (hallazgo 11 y `tokens.md`) |
| Leyenda de estados | `app.js:94`; `statusBadge()` `:58` | Indicadores `progress`, `enabled`, `warning`, `pending` |
| Interruptores | `app.js:211`; estilos `.switch` | Movimiento y ayudas |
| Idioma | `app.js:234` (`localeSelect`) | es, en, fr, pt |
| Exportar, importar, reiniciar | `app.js:145`, `:238`, `:203-224` | Import: 3 MB máx., validación con `validImport()` `:48-55` |

## Iconos

`index.html:14-39` define 24 `<symbol>` con `id="i-<nombre>"`. `ic(name)` en `app.js:22` los referencia. Todos los nombres usados por el código existen. No hay CDN ni fuentes externas.

## Adaptaciones Rare UI

Upload `2ca57186`, `fa5e2002`, `4d29f625`, `b912b246`. **No se copiaron al repo. No se descargó nada de Rare UI. La licencia no está revisada.**

| Componente | Import externo | Colores fijos | Problemas | Estado |
|---|---|---|---|---|
| `bounce-sidebar` | `@/components/ui/bounce-sidebar` | `#202020`, `#3A3A3A`, `#EDEDED`, dot `#0848F7` | Colores fuera de tokens. Sin `data-theme` | Sin verificar. Licencia pendiente. Depende de `@/components/ui/*` |
| `hook-sidebar` | `@/components/ui/hook-sidebar` | `#202020`, `#3A3A3A`, `#EDEDED`, color `#0848F7` | Igual. `dashed` no existe en tokens | Sin verificar. Licencia pendiente. Depende de `@/components/ui/*` |
| `folder` | `@/components/ui/folder-component` | `#1B1B1B`; `color="black"` | `black` es `#000`, prohibido como fondo en gris | Sin verificar. Licencia pendiente. Depende de `@/components/ui/*` |
| `family-drawer` | `@/components/ui/family-drawer` | `#1B1B1B`, `#3A3A3A`, `borderRadius` 24 | Colores fuera de tokens. Clases Tailwind (`relative overflow-hidden`) | Sin verificar. Licencia pendiente. Depende de `@/components/ui/*` |

Todos usan `"use client"`, una directiva de frameworks con RSC. Un proyecto Vite no la necesita. Su alias `@/` no existe en las fuentes: UNKNOWN si el repo lo define.

Antes de usar cualquiera: revisar licencia, reemplazar colores por tokens, quitar `"use client"`, confirmar los módulos `@/components/ui/*`, y verificar en navegador (ver `verification.md`).

## Referencia visual, no chat

`d8dccc48-_Run_UI_YAIWES.html` es una pantalla de Run con pestañas CASCADE, TREN, AUDITOR, VENTANAS y ORQUESTA. Sirve de referencia visual y no es el chat. No tiene bridge ni se verificó aquí.
