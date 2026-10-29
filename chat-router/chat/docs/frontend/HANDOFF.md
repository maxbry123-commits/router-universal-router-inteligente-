# HANDOFF — Raíz FRONTEND del chat

**Carpeta:** `chat/frontend/` (70 módulos `.js`, ES modules sin build; Vercel añade `?v=<sha>` en `build.sh`).
**Índice con commits por archivo:** `chat/docs/frontend/INDICE.md` · **Todos los cambios:** `chat/docs/frontend/CAMBIOS.md`
**Instrucciones · daños · pendientes:** `docs/INSTRUCCIONES_DANOS_PENDIENTES.md` · **Auditoría forense:** `docs/AUDITORIA_FRONTEND_XRAY.md`

## Cómo está cableado
- Entrada: `shell.html` → `shell.js` → paneles; el chat: `panel-chat.html` → `api.js` + `panel-chat.js` (`mount`).
- `panel-chat.js` (núcleo) delega en: `enviar-mensaje.js`, `controles-chat.js`, `buzon-proceso.js`, `pildora-ficha.js`, `selector-ancla.js`, `selects-secundarios.js`, `ventana-sandbox-chat.js`, `ventana-motor.js`.
- Caja de escritura: como en la base (todos los controles a la vista; `composer-filas.js/css` se eliminó el 25-oct por dañar cubo, Detener y etiquetas) + `tools-ventana.js` (chips, evento `riu:ia`).
- Selectores de modelo: `chat-selectores.js` (`RIU_SELECTORES`), `fichas-externas.js` (Groq/NVIDIA), `agentes-mirror.js`.
- Ventanas: `ventana-conexiones.js`, `ventana-room.js`, `ventana-servidor.js` (`/api/power` en Vercel), `pendientes-panel.js`.
- RIU/RUI (22 componentes): `chat-riu.js`, `chat-riu2.js` → `riu-*.js`.
- HTTP: `api.js` es el cliente principal del Router (`/chat/send`, `/chat`, `/almacen`, `/memoria/*`, `/chat/providers`, `/plugins/*`). También hacen `fetch` directo: `buzon-proceso.js`, `mode_selector.js`, `panel-apariencia.js`, `seguimiento-real.js`, `shell.js`, `ventana-claves.js`, `ventana-constitucion.js`, `ventana-servidor.js` (`/api/power`), `ventana-workflows.js`.

## Verificación (todo real, repetible)
```
python3 chat/e2e/cableado.py     # imports, huérfanos, sintaxis, endpoints FE→BE, ids del DOM
bash chat/e2e/todo.sh            # batería Playwright móvil+escritorio, axe, teclado, eslint, node --test, pytest
```
Regla: nada de comentarios `//` a mitad de línea (rompió `api.js`, `5f7c08eacd`). Antes de subir: `node --check` y `eslint no-undef`.

## Lo que NO funciona o está dañado
D8 Nuevo proyecto · D13 paneles con endpoints inexistentes. (D1 cubo, D2 Detener, D3 controles y D5 etiquetas: arreglados; prueba `chat/e2e/original.js`.) Detalle y commits: `docs/INSTRUCCIONES_DANOS_PENDIENTES.md` §B y §C.
