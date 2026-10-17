# Qué llegó a la fábrica vs qué falta

Inventario de `fabrica de UI INTERFACE fromtend/` en GitHub (primer nivel) + DESTINO previsto.

## Ya está en GitHub (llegó)

| Carpeta | Capa | Usar para |
|---------|------|-----------|
| GrapesJS | F1 canvas | editor bloques |
| Craft.js | F1 canvas | toolkit editor |
| Office-Ribbon-2010 | F1 host | menú tipo Office 2007 |
| Fluent.Ribbon | contrato | no portar WPF |
| Fluent-UI | look/a11y | iconos; color = skill |
| Appsmith | referencia widgets | **no** runtime usuario |
| ToolJet | referencia | no runtime |
| Budibase | embed iframe | no runtime |
| Lowcoder | referencia | no runtime |
| Tauri-2 | empaque | Linux/Win/móvil |
| Capacitor + plugins + file-sharer | empaque | Android/iOS |
| Wails | empaque | gap: ref `v3-alpha` (FULL_REPOS_EMPAQUE_LOCAL_GAPS.json) |
| Neutralino | empaque liviano | fallback |
| PWABuilder | TWA | Android desde PWA |
| Bubblewrap-TWA | TWA | Android |
| Workbox | offline | SW |
| Dexie, localForage, PouchDB | persistencia | manifiestos |
| browser-fs-access | FS | Cargar/Descargar |
| Filesystem | FS | kernel |
| VS-Code-Contribution-Points-Docs + Samples | manifiesto | contributes = RibbonX moderno |

Runtime copiado (cone UI): `UI YAIWES interface/fabrica-ui/runtime/lote-01-nucleo-host/` (ABS, slots, wire, access-key).

OSS extra en `📂componentes open soure fromtend/` (puntero, no copiado 78k): MaoMao-Window-Manager, dockview, lucide, assistant-ui, i18next, shadcn-ui, Saas-UI, Volt-React-Dashboard, Dashup.

## Falta (DESTINO pedía y no está como repo)

| Previsto | Para qué | ZIP a subir tú |
|----------|----------|----------------|
| Puck | canvas React FROMTED | https://github.com/measuredco/puck/archive/refs/heads/main.zip |
| Plasmic / Onlook | canvas F1 | ver 50-JUSTIFICACION |
| Node-RED | wires receta | https://github.com/node-red/node-red/archive/refs/heads/master.zip |
| n8n | wires | https://github.com/n8n-io/n8n/archive/refs/heads/master.zip |
| Blockly | bloques receta | https://github.com/RaspberryPiFoundation/blockly/archive/refs/heads/master.zip |
| JSONForms | ficha botón | https://github.com/eclipsesource/jsonforms/archive/refs/heads/master.zip |
| RJSF / Form.io | forms | — |
| Pyodide | sandbox Python | https://github.com/iodide-project/pyodide (wheels) |
| QuickJS | sandbox JS | — |
| WebContainers / Deno | sandbox | — |
| Directus / NocoDB / Payload | backend local 07 | **separado** de ventanas |
| Penpot | tokens diseño | — |
| NocoBase | internal tools | — |
| PocketBase | kernel API SQLite | recomendado, no estaba en DESTINO original |

## Gap empaque ya detectado

`FULL_REPOS_EMPAQUE_LOCAL_GAPS.json`: Wails `v3-alpha` no resolvió.

## Cómo completar

1. Tú descargas el ZIP.  
2. Lo subes a: https://github.com/maxbry123-commits/frontend/upload/main/fabrica%20de%20UI%20INTERFACE%20fromtend/componentes%20para%20fabrica%20de%20interface  
3. Yo lo parto 1 archivo = 1 función. **No clono a ciegas 20 monorepos.**
