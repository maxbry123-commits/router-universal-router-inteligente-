# Plan de integración — fábrica UI

1 ventana = 1 archivo. Tokens Matte / Little / Blanco. Naranja solo Cargar/Descargar.
Lista de componentes: `LISTA-FINAL-FABRICA.md`. No integrar nada fuera de esa lista.

## Cómo se integra cada uno

| Orden | Componente | Dónde entra | Qué produce |
|-------|------------|-------------|-------------|
| F0 | lote-01 ABS / wires | `runtime/lote-01-nucleo-host/` | Botón dispara action id. Kernel ejecuta. |
| F1 | Office-Ribbon-2010 + Fluent.Ribbon | host F1 (clave) | Manifiesto de botones/grupos. Añadir/quitar sin editar HTML de ventana. |
| F2 | VS Code contribution-points | mismo manifiesto | `contributes.views` / `commands` = slots del host. |
| F3 | Fluent UI | tokens de a11y | Focus, roles. Color sigue skill 01. |
| F4 | lucide | cada botón | SVG blanco → Little. |
| F5 | dockview | HOST.html | Split/tabs de iframes de las 39. |
| F6 | GrapesJS | canvas F1 | JSON de página. Publish → plantilla. Nunca F2. |
| F7 | Craft.js | chrome del canvas | El editor se ve FROMTED. |
| F8 | JSONForms | panel clave, por botón | Schema → form: URL, método, token_ref, sandbox. **Subir ZIP.** |
| F9 | XState | LOOP + bitácora | Nodos F0…F12 ejecutables. **Subir ZIP.** |
| F10 | assistant-ui | ventanas chat | Composer/thread cableados a ABS, no mock. |
| F11 | i18next + react-i18next | nombres UI | es/en/fr/pt en manifiesto. |
| F12 | Dexie + localForage + PouchDB | persistencia | Plantillas y wires locales. Sync opcional. |
| F13 | browser-fs-access | Cargar/Descargar | Archivo real del OS. |
| F14 | Workbox | PWA HOST | Offline. |
| F15 | PWABuilder + Bubblewrap | Android | TWA instalable. |
| F16 | Tauri | desktop + móvil nativo | Un web, binario por OS. |
| F17 | Capacitor | tiendas | Mismo HTML. Strip Factory del build producto. |

## Fases

- **A** F0–F5: host + ABS + ribbon + dockview + lucide (lote-01 ya está).
- **B** F6–F9: canvas F1 + JSONForms + XState (esperan ZIP de los 2 que faltan).
- **C** F10–F13: chat + i18n + storage.
- **D** F14–F17: PWA → TWA → Tauri → Capacitor. Producto sin panel clave.

## Reglas

- Fábrica ≠ producto. Factory se quita en `03-producto`.
- Un canvas (GrapesJS). Un form de ficha (JSONForms). Un DAG (XState).
- No Appsmith/ToolJet/Budibase/Lowcoder como runtime.
- No extraer ZIP ajenos a esta lista.
