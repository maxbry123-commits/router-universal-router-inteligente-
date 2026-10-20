# Lista final — componentes de la fábrica UI

Solo lo que se necesita. Nada de ZIP pendientes. Nada de extras.

| Nombre | URL | Justificación |
|--------|-----|----------------|
| GrapesJS | https://github.com/GrapesJS/grapesjs | Canvas interno (clave). Armar página con bloques JSON. No se sirve al usuario. |
| Craft.js | https://github.com/prevwong/craft.js | El canvas puede pintarse con chrome FROMTED, no con UI de Craft. |
| Office-Ribbon-2010 | https://github.com/OkGoDoIt/Office-Ribbon-2010 | Menú tipo Office 2007: añadir/quitar botones por manifiesto, no HTML soldado. |
| Fluent.Ribbon | https://github.com/fluentribbon/Fluent.Ribbon | Contrato Ribbon (tabs, grupos, QAT). No portar WPF. |
| Fluent UI | https://github.com/microsoft/fluentui | Accesibilidad e iconografía. Color = skill 01, no marca Fluent. |
| VS Code contribution-points | https://github.com/microsoft/vscode-docs | `contributes` = el módulo declara, el host pinta. Gemelo moderno del Ribbon. |
| dockview | https://github.com/mathuo/dockview | HOST: paneles/pestañas/split de las 39 ventanas iframe. |
| lucide | https://github.com/lucide-icons/lucide | Iconos blancos que recogen Little. 1 icono = 1 botón. |
| assistant-ui | https://github.com/assistant-ui/assistant-ui | Bloques de chat reales (composer/thread), no mock. |
| i18next | https://github.com/i18next/i18next | Nombre de botón/ventana en es/en/fr/pt. |
| react-i18next | https://github.com/i18next/react-i18next | Mismo i18n si un Lego es React. |
| Workbox | https://github.com/GoogleChrome/workbox | PWA offline del HOST. |
| Tauri | https://github.com/tauri-apps/tauri | Binario Linux/Windows/macOS/Android/iOS. |
| Capacitor | https://github.com/ionic-team/capacitor | El mismo HTML a tiendas Android/iOS. |
| PWABuilder | https://github.com/pwa-builder/PWABuilder | Web → TWA Android instalable. |
| Bubblewrap TWA | https://github.com/GoogleChromeLabs/bubblewrap | Empaque TWA si PWABuilder no basta. |
| Dexie | https://github.com/dexie/Dexie.js | IndexedDB de manifiestos y plantillas. |
| localForage | https://github.com/localForage/localForage | Fallback storage si Dexie no corre. |
| PouchDB | https://github.com/pouchdb/pouchdb | Sync local-first de plantillas entre dispositivos. |
| browser-fs-access | https://github.com/GoogleChromeLabs/browser-fs-access | Cargar/Descargar archivos reales (naranja). |
| lote-01 ABS / wires | `UI YAIWES interface/fabrica-ui/runtime/lote-01-nucleo-host/` | Botón → ABS → kernel. Sin esto no hay producto. |
| JSONForms | https://github.com/eclipsesource/jsonforms | **Falta.** Ficha de cada botón = schema → form de config (clave). |
| XState | https://github.com/statelyai/xstate | **Falta.** LOOP S0–S8 y DAG de fábrica ejecutables, no prosa. |

ZIP de lo que falta:

- JSONForms https://github.com/eclipsesource/jsonforms/archive/refs/heads/master.zip
- XState https://github.com/statelyai/xstate/archive/refs/heads/main.zip

Subir: https://github.com/maxbry123-commits/frontend/upload/main/fabrica%20de%20UI%20INTERFACE%20fromtend/componentes%20para%20fabrica%20de%20interface
