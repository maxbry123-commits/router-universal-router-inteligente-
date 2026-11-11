# Handoff: skill unificado fromted-yaiwes-frontend

Estado: **REVIEW**. Pendiente de aprobación visual del propietario. Rama `ccr-f01c3de9-bmry0s`. No hay push. No se desplegó nada.

## Rutas del skill

| Ruta | Contenido |
|---|---|
| `Skills/fromted-yaiwes-frontend/SKILL.md` | Skill: propósito, precedencia, no-mock, fases, 11 criterios |
| `Skills/fromted-yaiwes-frontend/references/tokens.md` | HEX de los 7 temas y estados, con contraste medido |
| `Skills/fromted-yaiwes-frontend/references/actions-contract.md` | 23 acciones, eventos, respuestas del bus y formato del bridge |
| `Skills/fromted-yaiwes-frontend/references/verification.md` | Playwright, entorno y matriz de 11 comprobaciones |
| `Skills/fromted-yaiwes-frontend/references/components.md` | Inventario de componentes y estado de Rare UI |
| `Skills/fromted-yaiwes-frontend/references/hallazgos-revision.md` | Revisión del chat: hallazgos con archivo y línea |

## Fuente de cada archivo (nombre original del upload)

| Archivo del skill | Fuentes |
|---|---|
| `SKILL.md` | `53ac2083-SKILL.md` (SKILL MAESTRO 0.2.0-review); contrastado con `f039a62f-README_5.md`, `a1c4fd37-AGENTS.md`, `21ccaae5-ACCEPTANCE.md`, `86679080-VERSION.md` |
| `references/tokens.md` | `dff2f49e-_styles.css` (fuente principal); tabla de `53ac2083-SKILL.md` §2; `c8312e59-app.js` (THEMES) |
| `references/actions-contract.md` | `093b534c-__manifest_3.json`; `c8312e59-app.js`; `47b98c1c-index-standalone.html` (copia inline de actionBus) |
| `references/verification.md` | `7d07c1e3-playwright.config.js`, `4c94689e-package.json`, `dc187cd3-vite.config.js`, `21ccaae5-ACCEPTANCE.md` |
| `references/components.md` | `064f4a74-__index.html`, `c8312e59-app.js`, `dff2f49e-_styles.css`, `2ca57186-02-bounce-sidebar-yaiwes.tsx`, `fa5e2002-03-hook-sidebar-yaiwes.tsx`, `4d29f625-01-folder-yaiwes.tsx`, `b912b246-04-family-drawer-yaiwes.tsx`, `d8dccc48-_Run_UI_YAIWES.html` (solo referencia) |
| `references/hallazgos-revision.md` | `064f4a74-__index.html`, `dff2f49e-_styles.css`, `c8312e59-app.js`, `093b534c-__manifest_3.json`, `47b98c1c-index-standalone.html` |

## Hallazgos principales (detalle en `hallazgos-revision.md`)

1. `app.js:5`: `makeId` llama `window.makeId()` inexistente. Sonda: no se añaden archivos y el envío confirmado no muestra respuesta. Mismo código en el snapshot (`47b98c1c-index-standalone.html:153`).
2. `app.js:41,57,110,111`: `bus()` no comprueba `actionBus`. Sin ese archivo, navegación y tema fallan a medias.
3. `app.js:42-46,128-132`: fallo de cuota en `localStorage` silencioso. Se pierden archivos y borrador al recargar.
4. `app.js:157` y `actionBus`: el bridge se aparta del contrato `{ok, reply}`. Se pierde `error`.
5. `app.js:107` + `index.html:60`: `refresh()` reinyecta todo el DOM y el `aria-live` re-anuncia la página.

## Estado de la verificación

- Ningún `PASS` nuevo. La sonda ad hoc (fuera del repo) confirmó los fallos 1 y 2. No es la suite del proyecto.
- ACCEPTANCE declara 9 de 11 PASS. No se reproduce desde las fuentes: la suite Playwright no está en los uploads.
- RELOAD: `BLOCKED` (sin spec, sin origen HTTP en esta revisión).
- Bridge real: `BLOCKED_REMOTE` (no hay backend en las fuentes).

## UNKNOWN (no están en las fuentes)

- `src/lib/actionBus.js` como archivo fuente. Solo existe la copia inline del snapshot.
- `tests/panel-01-chat.spec.js`, `tests/run_browser_qa.py`, `tests/qa-log.txt`, `tools/build_snapshot.py`.
- `screenshots/` y `snapshot/reference-*.jpg`. Sin capturas de referencia no hay comparación visual (REF).
- Skills originales 01 a 04 (tokens inmutables, catálogo, interacciones, protocolo).
- Si el bridge real existe y qué formato devuelve.
- Medida de contraste de crystal, orange y blue sobre tarjetas con alfa.
- Si el repo define el alias `@/` para los componentes Rare UI.

## Decisiones pendientes para el propietario

- Contraste de gris: los estados no alcanzan 3:1 sobre el lienzo (`tokens.md`).
- Uso de terracota en Little: el CSS la usa más allá de CTA (hallazgo 6).
- Miniaturas de tema en `app.js` distintas del CSS real (hallazgo 11).
- Licencia de Rare UI: no revisada. No se copió ni descargó nada.

## Cómo reanudar

1. Corregir hallazgos 1 a 5 en el fuente del proyecto y no en el snapshot.
2. Traer la suite Playwright y ejecutar `npx playwright test --trace off` contra `http://127.0.0.1:5173`.
3. Actualizar `ACCEPTANCE.md` solo con resultados ejecutados.
