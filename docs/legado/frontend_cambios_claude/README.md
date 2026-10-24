# Cambios de Claude en el frontend del chat (guardados antes de revertir)

Base restaurada: commit `1b916a587c` (último antes del primer cambio de Claude al frontend, 23-oct-2026). Desde esa base solo Claude tocó `plugins/chat-router/frontend/`.

| Commit | Qué cambió en el frontend |
|---|---|
| 62fbb681c4 | `tools-ventana.js` (IA/agentes ON/OFF desde el servidor), `controles-ventana.js` NUEVO (ventanas Conexiones y ROOM), `pendientes-panel.js` (checklist), `shell.js` |
| 59f811887e | `maxbry-ui.js` NUEVO + `chat-maxbry.css` NUEVO (composer ordenado, ＋ bandeja, chips, toast), `panel-chat.html`/`shell.html` (enlace al css), `panel-chat.js` |
| 28bcf2b6f3 | `chat-maxbry.css`: filas de selector como mode-option |
| 9607eb66ad | `api/power.js` NUEVO (botón Servidor), `test/power.test.js` NUEVO, `vercel.json` NUEVO, `controles-ventana.js` (ventana Servidor) |
| 62c3e0d1ee | `maxbry-ui.js`/css: medios `[[imagen:]]`, `[[video:]]`, `[[audio:]]` |
| 7548c2cc87 | `tools-ventana.js`: chip Agentes y panel de agentes; css |
| 748db5a6e5 | chip System prompt, organizador de pendientes, `panel-chat.html` (yaiwes.md), `panel-chat.js`/`anclaje-destinos.js`/`chat-ventanas.js` (texto "yaiwes.md") |
| 5be2929688 | `controles-ventana.js`: botón «Turno de los agentes» |
| 24b26c7735 | `api/power.js`: usa HF_TOKEN_1 |
| 54c8815ea0, 70cc3661f4 | chip System prompt en la fila de chips; botones del composer visibles (`BANDEJA=false`) |
| 8557028764 | `chat-selectores.js`: filas con ⓘ, ⚡, ON/OFF y «Modelo: …»; `shell.html`: enlace a `selector-resp.css` |

Archivos: `TODOS_LOS_CAMBIOS.patch` (todo junto), `commits/<sha>.patch` (uno por commit), `archivos/` (copia completa de cada archivo cambiado, tal como estaba en `main` antes de revertir).
Para reaplicar todo: `git apply TODOS_LOS_CAMBIOS.patch` sobre `plugins/chat-router/frontend/` (rutas del patch ya incluyen `plugins/chat-router/frontend/`).
