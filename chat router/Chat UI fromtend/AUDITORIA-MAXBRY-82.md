# Auditoría Maxbry — 82 archivos, estado del chat (2026-10-04)

Origen: árbol histórico `6c742b8ad662241cccc5b57914223022068333d3:chat router/01-PLAN/SKILLS-MAXBRY-UI` (33 en `diseno/`, 49 en `componentes/`). Se cotejó cada entrada con la matriz de auditoría anterior y se revalidaron los deltas del chat actual. **Incorporado no significa que se haya copiado literalmente el HTML/TSX original**: sólo que el contrato aplicable al chat tiene implementación modular. «No aplica» significa otro panel/shell, referencia no homologada o duplicado; se vuelve a examinar en la segunda fase. Ningún estado en este archivo prueba equivalencia visual o ejecución de backend.

| ID | Archivo | Función contrastada | Estado actual del chat | Evidencia/destino histórico |
|---|---|---|---|---|
| D01 | 😄SKILL.md | Flujo REFERENCE→…→DELIVERY; microflujo MODELO→MODO→TOOLS→REDACTAR→ACTION BUS→BRIDGE→RESPUESTA/ERROR; HTML/CSS/JS separados; 1 ventana = 1 archivo; no mock; contrato `YAIWES_PLUGIN_BRIDGE.execute`; 3 temas canónicos; i18n es/en/fr/pt; 11 comprobaciones; trazabilidad | PARCIAL | `src/bridge.js`, `src/app.js`, `src/windows/*`, `src/i18n.js`, `styles/tokens.css`, `tests/*` |
| D02 | SKILL-MAESTRO-FROMTED-YAIWES-BORRADOR.md | Mismos contratos; little principal | PARCIAL | igual que D01 |
| D03 | README-SKILL-PARTE-1-GRIS-PRINCIPAL.md | `gris` V07 principal; jerarquía fondo→panel→módulo→seleccionado→máscara; sólo el módulo elegido usa `#3C3C3C`; geometría 24/12/10/28 px, iconos 14–16, textos 16/14/12/11; tema≠selección≠estado; checklist de 13 puntos; estados APROBADO_VISUAL / PROBADO_FUNCIONAL / PENDIENTE | PARCIAL — tokens y Gris principal; aceptación visual pendiente | `src/config.js` (`gris` inicial), `styles/tokens.css`, `src/components/theme-palette.js`; falta aceptación visual |
| D04 | README-SKILL-FROMTED-YAIWES-GRIS-Y-LETRAS.md | Gris principal + 8 categorías tipográficas configurables | PARCIAL | sólo lo de D01 |
| D05 | SKILL-PARTE-2-TIPOGRAFIA-EN-REVISION.md | 8 categorías (title, subtitle, body, input, placeholder, output, button, meta) × 10 propiedades | NO APLICA A ESTA FASE | — |
| D06 | README-SKILL-PARTE-3-ICONOS-Y-EMOJIS-EN-REVISION.md | 54 iconos V12, 6 categorías, 6 colores funcionales, 6 estados, acción real por icono, persistencia, exportación, táctil/teclado | PARCIAL | `src/components/icon.js` (14 glifos lineales 24×24, trazo 1.7) |
| D07 | ESPECIFICACION_VISUAL_PANEL_YAIWES_FROMTED.md | Tema gris, geometría, configuración, conectores, editor visual, iconos, móvil, composer, adjuntos, web, thinking, estados, niveles de razonamiento, opciones, componentes universales, modelo de estado, contratos, arquitectura; §15–17 HTML/CSS/JS de referencia del panel *Connections* (sidebar con marca «Y», tokens gris); §22 mapa funcional | PARCIAL | Chat/Agente (input, adjuntos, voz, comandos, modos): `chat-composer.js`, `modes.js`, `tools.js`, `record-voice.js`; marca Y: `mark.js` |
| D08 | FROMTED-YAIWES-PRUEBA-PALETA-V07.html | Paleta gris V07 aprobada | PARCIAL — referencia Gris, sin comparación visual autorizada | `styles/tokens.css` + `tests/design-contract.test.js`; sin navegador |
| D09 | FROMTED-YAIWES-COLORES-ICONOS-V09.html | Selectores de color de texto/iconos V08/V09 | NO APLICA A ESTA FASE | — |
| D10 | FROMTED-YAIWES-LETRAS-GRIS-V10.html | Tipografía sobre gris | NO APLICA A ESTA FASE | — |
| D11 | YAIWES-LETRAS-V11.html | Tipografía V11 | NO APLICA A ESTA FASE | — |
| D12 | YAIWES-ICONOS-PRO-V12.html | Biblioteca 54 iconos V12 | PARCIAL | `icon.js` (glifos propios) |
| D13 | YAIWES-ICONOS-PRO-V12-1.html | idéntico a D12 (MD5 59c1cb82) | DUPLICADO | — |
| D14 | YAIWES-CRAZY-WALL.html | Panel Crazy Wall / Actividades | NO APLICA A ESTA FASE | `src/panels/panel-03.js` placeholder `NOT_IMPLEMENTED` |
| D15 | YAIWES-CRAZY-WALL-1.html | variante Crazy Wall (MD5 distinto) | NO APLICA A ESTA FASE | — |
| D16 | YAIWES-CRAZY-WALL-2.html | variante Crazy Wall (MD5 distinto) | NO APLICA A ESTA FASE | — |
| D17 | YAIWES-PERFIL-VISUAL-DEMO.html | 6 temas: little, matte, blanco (canónicos) + crystal, orange, blue (propuestas) | PARCIAL — siete perfiles seleccionables; comparación visual pendiente | `styles/tokens.css`, `src/components/theme-palette.js`; 7 paneles; sin comparación visual |
| D18 | RUI-YAIWES-5-COMPONENTES-DEMO.html | 5 componentes (folder, bounce/hook/proximity sidebar, family drawer) | NO APLICA A ESTA FASE | — |
| D19 | RUI-YAIWES-LOTE-1-DEMO.html | lote 1 (bounce, hook, gooey, family drawer, proximity) | NO APLICA A ESTA FASE | — |
| D20 | RUI-YAIWES-LOTE-1-DEMO-1.html | idéntico a D19 (MD5 035f8856) | DUPLICADO | — |
| D21 | UI-YAIWES-interface-lote-anotacion.zip | handoff, CABLEADO-BIBLIOTECA-150, INVENTARIO-39, METODO-DE-TRABAJO, p01 chat, p04 sheet agregar, p05 sheet herramientas, p09 mode dropdown, p02/p03 docs, p06 proyecto, p07 sidebar, p08 artefactos, p10 conocimiento, v2-01 chat, v2-02 artifact, v2-03 settings, v2-04 directorio, DOC1_FRONTEND, Run, Crazy Wall | PARCIAL | p01/v2-01 chat → `panels/chat.js`; p04/p05 → `windows/tools.js`; p09 → `windows/modes.js`; v2-03 → `panels/settings.js` |
| D22 | ♾️🫠index.html | 4 pantallas (chat, files, wall, settings), little, Action Bus | PARCIAL | chat + settings reconstruidos en módulos propios |
| D23 | 🥳index-standalone.html | 7 temas (incl. `gris`, crystal, orange, blue) autocontenido | PARCIAL — HTML autónomo generado; navegador no probado | `scripts/build-review.mjs` → `chat Yaiwes fromtend.revisar.html`; sin navegador |
| D24 | ⛳styles.css | tokens `--radius-phone/card/button/sheet`, `--status-green/blue/red` + soft, `--brand`, `--title/--sub/--dim`, `--border-strong` | PARCIAL | `styles/tokens.css` (status-green/blue/red, temas) |
| D25 | 🚀app.js | `data-action` chat.attach, chat.close, files.add, mode.open, state.export/import/reset, wall.root.add; send, exportChat, persist, toast, theme, openSheet | PARCIAL — export/import/reset añadidos; files/wall son otra fase | `src/bridge.js`, `src/actions/chat-session.js`, `src/actions/settings-transfer.js`, `src/config.js` |
| D26 | 🏭ACCEPTANCE.md | 11 TEST_* con sus resultados **de la referencia**, no del chat actual; ERR_BLOCKED en su entorno | BLOQUEADO | tests node cubren BUTTONS/DROPDOWNS/INPUTS/STATE en DOM simulado |
| D27 | 🛜VERSION.md | historial, estado REVIEW, lo probado/no probado | PARCIAL | `README.md` del chat |
| D28 | 🤣README (5).md | REFERENCE+CONTEXT+SKILLS+BROWSER+VERIFIER; servir en localhost; no mocks | PARCIAL | no-mock cumplido |
| D29 | ➡️manifest (3).json | defaultTheme little; canónicos 3; candidatos 4 | INCORPORADO (con conflicto) | `config.js` DEFAULT_CONFIG.theme="little", 3 temas |
| D30 | 👾package.json | vite, playwright, snapshot python | NO APLICA A ESTA FASE | el chat usa `node --test` + esbuild + linkedom |
| D31 | 🐻vite.config.js | servidor Vite | NO APLICA A ESTA FASE | — |
| D32 | 📌playwright.config.js | tests Chromium | BLOQUEADO | — |
| D33 | 📲👨‍💻📳📱🖥️Run UI YAIWES.html | pantalla Run (ejecución/evidencia) | NO APLICA A ESTA FASE | `panel-04.js` placeholder |
| C01 | 01-folder-component-DESCARGAR.sh | curl del TSX original (commit 1d572f4b) | NO APLICA A ESTA FASE | — |
| C02 | 02-bounce-sidebar-DESCARGAR.sh | idem | NO APLICA A ESTA FASE | — |
| C03 | 03-hook-sidebar-DESCARGAR.sh | idem | NO APLICA A ESTA FASE | — |
| C04 | 04-family-drawer-DESCARGAR.sh | idem | NO APLICA A ESTA FASE | — |
| C05 | 05-proximity-sidebar-DESCARGAR.sh | idem | NO APLICA A ESTA FASE | — |
| C06 | 06-duration-picker-DESCARGAR.sh | idem | NO APLICA A ESTA FASE | — |
| C07 | 07-fluid-orb-DESCARGAR.sh | idem | NO APLICA A ESTA FASE | — |
| C08 | 08-scroll-progress-DESCARGAR.sh | idem | NO APLICA A ESTA FASE | — |
| C09 | 09-code-block-DESCARGAR.sh | idem | NO APLICA A ESTA FASE | — |
| C10 | 10-otp-input-DESCARGAR.sh | idem | NO APLICA A ESTA FASE | — |
| C11 | 11-gravity-letters-DESCARGAR.sh | idem | NO APLICA A ESTA FASE | — |
| C12 | 12-github-activity-DESCARGAR.sh | idem | NO APLICA A ESTA FASE | — |
| C13 | 13-emoji-reaction-DESCARGAR.sh | idem | NO APLICA A ESTA FASE | — |
| C14 | 14-notification-bell-DESCARGAR.sh | idem | NO APLICA A ESTA FASE | — |
| C15 | 15-step-player-DESCARGAR.sh | idem | NO APLICA A ESTA FASE | — |
| C16 | 16-grid-reveal-DESCARGAR.sh | idem | NO APLICA A ESTA FASE | — |
| C17 | 17-gooey-nav-DESCARGAR.sh | idem | NO APLICA A ESTA FASE | — |
| C18 | 18-delete-button-DESCARGAR.sh | idem | NO APLICA A ESTA FASE | — |
| C19 | 19-animated-counter-DESCARGAR.sh | idem | NO APLICA A ESTA FASE | — |
| C20 | 20-matrix-orb-DESCARGAR.sh | idem | NO APLICA A ESTA FASE | — |
| C21 | 21-task-list-DESCARGAR.sh | idem | NO APLICA A ESTA FASE | — |
| C22 | 22-voice-note-DESCARGAR.sh | idem (voice-note es un reproductor de nota de voz, no la captura) | NO APLICA A ESTA FASE | captura real de voz: `record-voice.js` (propio) |
| C23 | 01-folder-yaiwes.tsx | wrapper React del folder | NO APLICA A ESTA FASE | — |
| C24 | 02-bounce-sidebar-yaiwes.tsx | wrapper React | NO APLICA A ESTA FASE | — |
| C25 | 03-hook-sidebar-yaiwes.tsx | wrapper React | NO APLICA A ESTA FASE | — |
| C26 | 04-family-drawer-yaiwes.tsx | wrapper React | NO APLICA A ESTA FASE | — |
| C27 | 05-proximity-sidebar-yaiwes.tsx | wrapper React | NO APLICA A ESTA FASE | — |
| C28 | DESCARGAR-CODIGO-ORIGINAL.py | descarga ZIP upstream rare-ui @1d572f4b | NO APLICA A ESTA FASE | — |
| C29 | DESCARGAR-CODIGO-ORIGINAL.sh | clone + checkout upstream | NO APLICA A ESTA FASE | — |
| C30 | VERIFICAR-22.py | verifica 22 TSX presentes | NO APLICA A ESTA FASE | — |
| C31 | LISTA-22.md | nombres de los 22 | NO APLICA A ESTA FASE | — |
| C32 | README-RARE-UI-01-05.md | 5 adaptadores, codemod, backup, flujo ORIGINAL→SNAPSHOT→COLOR→RENDER→TEST | NO APLICA A ESTA FASE | — |
| C33 | README (2).md | idéntico a C32 (MD5 8e6f79c7) | DUPLICADO | — |
| C34 | README (4).md | idéntico a C32 (MD5 8e6f79c7) | DUPLICADO | — |
| C35 | README (3).md | estructura YAIWES-CODE/ y UPSTREAM/ | NO APLICA A ESTA FASE | — |
| C36 | README-1.md | idéntico a C35 (MD5 d191cf03) | DUPLICADO | — |
| C37 | README-RUI-YAIWES-LOTE-1.md | fuente Rare UI, **paleta gris**, regla «sólo tokens/colores», licencia, pendiente prueba visual | PARCIAL — gris incorporado; Rare UI queda en shell | `styles/tokens.css`; 22 componentes Rare UI para shell/segunda fase |
| C38 | RUI-22-ARCHIVOS-INDIVIDUALES.zip | empaqueta los 22 scripts | NO APLICA A ESTA FASE | — |
| C39 | RUI-YAIWES-LOTE-1-TEST-REPORT.md | PASS de la demo Rare UI **de la referencia** | NO APLICA A ESTA FASE | — |
| C40 | install-lote-1.sh | `npx shadcn add` ×5 | NO APLICA A ESTA FASE | — |
| C41 | install-rui-01-05.sh | `npx shadcn add` ×5 + recolor | NO APLICA A ESTA FASE | — |
| C42 | manifest (2).json | lote 1 (5 componentes) | NO APLICA A ESTA FASE | — |
| C43 | manifest-22.json | 22 componentes con commit fijado y URL | NO APLICA A ESTA FASE | — |
| C44 | manifest.json | 22 nombres | NO APLICA A ESTA FASE | — |
| C45 | page.tsx | demo Next de los 5 | NO APLICA A ESTA FASE | — |
| C46 | patch-lote-1.mjs | sustituye HEX por tokens `--yaiwes-*` | NO APLICA A ESTA FASE | — |
| C47 | recolor-rui-01-05.mjs | recolor con backup | NO APLICA A ESTA FASE | — |
| C48 | rareui-yaiwes-theme.css | `--yaiwes-bg #1B1B1B … --yaiwes-accent #0848F7, success #12D86A, danger #FF475F, warning #FF7B1A` | INCORPORADO — tokens Gris mapeados; visual pendiente | `styles/tokens.css` Gris V07 y estados funcionales |
| C49 | rui-yaiwes.css | mismos valores gris en nombres shadcn | PARCIAL — valores Gris; nombres shadcn no aplican al chat | `styles/tokens.css` Gris V07; esquema shadcn pertenece a React |

Deltas comprobados frente a la auditoría anterior: Gris V07 ahora es tema principal; Little, Matte y Blanco siguen presentes; Crystal, Orange y Blue aparecen como referencias no aprobadas. Existen `pending`/`progress` y exportación/importación/reinicio de configuración. Siguen sin probarse las once condiciones de aceptación en navegador ni la ruta HTTP con autenticación real. Los 82 PNG de la auditoría X-Ray coincidieron con su SHA-256, pero el informe X-Ray consigna 0 verificaciones visuales y 0 ejecuciones de runtime.
