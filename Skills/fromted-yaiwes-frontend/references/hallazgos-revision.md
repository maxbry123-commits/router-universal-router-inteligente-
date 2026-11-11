# Hallazgos de la revisión del chat (estado REVIEW)

Revisión de: `index.html` (064f4a74), `styles.css` (dff2f49e), `app.js` (c8312e59), `manifest` (093b534c), contrastada con `snapshot` (47b98c1c). Las líneas corresponden a los archivos de upload, no al repo.

**Tipo de evidencia**
- **[S]** Sonda ejecutada: Chromium headless shell sobre una copia de trabajo fuera del repo (`index.html` + `styles.css` + `app.js` + `actionBus` extraído del snapshot), servida en `127.0.0.1` (contexto seguro). No es la suite Playwright del proyecto.
- **[L]** Lectura de código, sin ejecutar.

## Los 5 más graves

| # | Archivo:línea | Tipo | Hallazgo |
|---|---|---|---|
| 1 | `app.js:5` (uso en 124, 158, 161, 222) | [S] | `makeId` llama `window.makeId()`, que no existe, cuando `crypto.randomUUID` está disponible (contexto seguro: localhost o HTTPS). Resultado en sonda: `rej: window.makeId is not a function`; **0 archivos añadidos** (`filesInState: 0`). En `send()` el bridge confirma (`ok:true`) pero el lanzamiento ocurre en 158: el mensaje de usuario no se guarda, la respuesta no se muestra y el borrador `hola` permanece. Como el usuario ve el envío sin respuesta, puede reenviar y ejecutar la acción remota dos veces. Además el botón de enviar queda `disabled` en el DOM (`sendButtonDisabled: true`) porque `refresh()` (162) no llega a ejecutarse. El snapshot (47b98c1c:153) tiene el mismo código. |
| 2 | `app.js:41`, `57`, `110`, `111` | [S] | `bus()` llama a `window.YAIWESActionBus.execute` sin comprobar que exista. Si `src/lib/actionBus.js` no carga (`index.html:10`), la llamada lanza de forma **síncrona**; `local()` usa `.catch`, que no captura ese error. `go()` y `theme()` actualizan `state` y se interrumpen antes de `persist()`/`refresh()`. Sonda: `state.page = settings` pero el encabezado sigue en "Chat". El envío además deja `sending=true` (153), sin `finally`: botón bloqueado hasta recargar. |
| 3 | `app.js:42-46`, `128-132` | [L] | `persist()` captura el error de `localStorage` y solo hace `console.warn`. Los archivos hasta 1 MB se guardan como `data:` (base64 ×1,33). Con unos pocos archivos se supera la cuota (~5 MB) y **la escritura completa falla**: se pierden archivos, borrador y mensajes al recargar, sin aviso al usuario. El toast de 132 dice "añadido" igualmente. El SKILL pide límite por archivo, pero no hay límite total. |
| 4 | `app.js:157` y `actionBus` del snapshot (47b98c1c:137) | [L] | Contrato del bridge desviado. (a) `actionBus` acepta `result.status` en `success/done/completed` aunque no haya `ok:true`; el contrato exige `{ok:true, reply}`. (b) Con `{ok:false, error}` la UI muestra solo `[BRIDGE_REJECTED]`; el texto `error` nunca aparece. (c) `app.js:160` acepta el alias `message`, que no está en el contrato. |
| 5 | `app.js:107` + `index.html:60` | [L] | `refresh()` reemplaza todo `#mainContent` con `innerHTML` en cada cambio (toggle de herramienta, tema, pestaña, pin). Se pierden foco y posición del cursor del textarea y de los controles. Además `#mainContent` tiene `aria-live="polite"`, así que cada refresh vuelve a anunciar la página completa a lectores de pantalla. |

## Contradicciones con el SKILL MAESTRO

| # | Archivo:línea | Regla violada | Detalle |
|---|---|---|---|
| 6 | `styles.css:12-19` | Little: "terracota solo CTA primario" (SKILL §2) | `var(--brand)` se usa para foco (12), icono de navegación activa y texto de acción (13), kicker y overline (14-15), botones de archivo activos (16), borde de toast (19) y selección de tema (18). |
| 7 | `styles.css:10` (gris) | Estados legibles en gris (SKILL §2, AGENTS "contraste apropiado") | Sobre el lienzo `#969ba2` el contraste es verde 1,93 / azul 2,43 / rojo 2,34 (por debajo de 3:1). Sobre la tarjeta `#d6d9de`: verde 3,81 (no cumple 4,5:1 para texto). Calculado contra color sólido, no contra el tinte `--status-soft-*`. |
| 8 | `app.js:67`, `73` | Tema activo visible | El inspector y el pill muestran `Little` escrito a mano, aunque el tema cambie. |
| 9 | `app.js:90`, `152`; `index.html:41, 55, 56, 61, 64, 67, 68` | i18n completa (SKILL §8) | Textos fijos en español (`INPUT`, `MISIÓN`, toast de archivo grande, aria-labels). En en/fr/pt quedan en español. |
| 10 | `app.js:93` | Escapado de atributos | `style="background:${meta.bg}"` sin `esc()`. Hoy solo viene de constantes, así que no hay inyección, pero rompe la regla. |
| 11 | `app.js:111`, `styles.css:6` vs `app.js:10` | Tokens = fuente real | `THEMES.crystal.card` vale `rgba(135,190,210,.36)` en `app.js:10`, pero `--card` vale `rgba(242,250,255,.095)` en `styles.css:6`. La miniatura del selector no coincide con el tema real. |
| 12 | `app.js:209` | Toda acción local emite evento (SKILL §4) | Borrar archivo no emite acción; `files.delete` no está en el manifest. |
| 13 | `app.js:186`, `index.html` | Trazabilidad | `notifyAction` escribe en `#actionLog`, que no existe en `index.html`. La rama queda muerta. |
| 14 | `app.js:229-230` | Código limpio | Variables muertas (`entries`, `old`, `pos`) en el handler de búsqueda. |
| 15 | `app.js:183`, `226` | Diálogo coherente | Esc nativo cierra `<dialog>` sin pasar por `closeSheet()` (no hay listener de `close`): `sheetKind` queda obsoleto. |

## Verificado correcto

- `esc()` (app.js:23) escapa `& < > " '`. Todo dato de usuario (nombres de archivo, notas, mensajes, nombres de raíz) pasa por `esc()`. Excepciones solo con constantes: 93 y `${actions}` en 70.
- No hay respuestas de IA inventadas. El único `role:'assistant'` (161) sale de la respuesta remota. El único `setTimeout` de app.js (115, 141) gestiona toasts y revocación de URL.
- Solo `chat.send` es remoto (`app.js:155`, `bus(...,true)`). El resto es local.
- Los iconos `ic('…')` usados (16) existen en el `symbol` de `index.html:15-38`.
- Las claves `t('…')` literales existen en es, en, fr y pt.
- Los 23 IDs del manifest coinciden con los que emite `app.js` y con la allowlist del `actionBus` del snapshot.

## Items UNKNOWN

- `src/lib/actionBus.js`: no está entre los uploads. Solo hay una copia inline en el snapshot (47b98c1c:112-146), que se usa como proxy.
- `tests/panel-01-chat.spec.js`, `tests/run_browser_qa.py`, `tests/qa-log.txt`, `tools/build_snapshot.py`, `screenshots/`, `snapshot/reference-*.jpg`, skills originales 01-04: no están en los uploads.
- Si el bridge real existe: UNKNOWN. No hay backend en las fuentes.
- ACCEPTANCE declara 9/11 PASS. No se pueden reproducir: la prueba de recarga no existe en las fuentes, y las pruebas se hicieron sobre el snapshot con `set_content`. El `pageerror: 0` no prueba la rama de `makeId` (hallazgo 1), que solo se activa en contexto seguro.
- El valor canónico de `--brand` de gris (`#3b444e`) no coincide con el "acento #303740" del SKILL; el CSS usa `#303740` para `--primary-bg`.
