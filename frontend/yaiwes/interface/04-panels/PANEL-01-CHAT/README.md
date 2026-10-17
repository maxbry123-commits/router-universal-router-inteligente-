# PANEL-01 — Chat operativo v0.2.0

## Estado

`PROTOTYPE / FRONTEND FUNCTIONAL / BACKEND BOUNDARY / REVIEW`

## Fuentes aplicadas

- arquitectura: `ARQUITECTURA-FRONTEND-UI-YAIWES-V1.md` + `PLAN-DE-TRABAJO-UI-YAIWES.md`;
- skills: `frontend-design.SKILL.md` + `Image-to-Code/skills/image-to-code-skill/SKILL.md`;
- referencias: lote `01-original/FOTOS-REF/`, con foco en Manus, Grok Bot, chat, tool sheet, sidebar y mode dropdown;
- originales: `LOCKED`, no modificados.

## Salida FIFA

1. `index.html`: snapshot autocontenido y ejecutable sin build.
2. `src/`: HTML/CSS/JS modular editable.
3. `src/panel-01-chat.manifest.json`: contrato de ventana y acciones.
4. `ACCEPTANCE.md`: criterios técnicos PASS/FAIL.
5. `tests/panel-01-chat.spec.js`: prueba Playwright.

## Funcionalidad real

- nuevo chat, selección y persistencia local;
- renombrar, exportar JSON y eliminar mensajes;
- selector Heavy/Expert/Fast/Auto;
- sheet `Añadir al chat` con cámara, fotos, audio y archivos;
- toggles de herramientas con estado visual y `aria-pressed`;
- previsualización y retiro de adjuntos;
- grabación real con `MediaRecorder` cuando el navegador concede permiso;
- enviar por botón o Enter; Shift+Enter crea nueva línea;
- estado QUEUED/RUNNING/BRIDGE_REQUIRED y cancelación local;
- rail responsive y navegación por teclado;
- localStorage para chats, modo y tools;
- inspector local solo en escritorio.

## Frontera backend

La UI emite `yaiwes:ui-action`. Si existe `window.YAIWES_BRIDGE.dispatch`, lo usa. Si no existe, falla cerrado y muestra `BRIDGE_REQUIRED`; nunca fabrica una respuesta del modelo.

## Paleta

Matte fijado por arquitectura: `#0a0a0d`, superficies grises, texto blanco, Little `#2563eb` para selección/foco. Naranja queda reservado a cargar/descargar y no se usa como marca del chat.

## Cierre

Este prototipo permanece en `REVIEW`. No integra HostShell/WindowRegistry/Action Bus reales hasta recibir `OK PANEL-01-CHAT`.
