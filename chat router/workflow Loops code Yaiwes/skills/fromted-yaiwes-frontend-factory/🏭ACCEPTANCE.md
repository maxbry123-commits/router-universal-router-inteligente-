# Aceptación y verificación — FROMTED × YAIWES v0.2

## Qué se probó realmente

Verificación en Chromium **headless** sobre el `snapshot/index-standalone.html`, generado automáticamente de `index.html + styles.css + actionBus.js + app.js`. Resoluciones: **1440 × 900** escritorio, **390 × 844** móvil. Capturas en `screenshots/` y salida reproducible en `tests/qa-log.txt`. No se invocó ningún proveedor de IA ni API real.

**RESULTADO OBSERVADO:** 7 temas cambiables, 3 indicadores semánticos visibles, modo, toggles, chat sin respuesta falsa cuando no hay bridge, chat con bridge de prueba explícito, carga de archivo de bytes reales, búsqueda, pin, descarga, notas de raíz, nueva raíz, exportación, importación, reinicio, idiomas, animaciones; **0 errores JS**, sin desbordamiento horizontal.

**IMPORTANTE SOBRE BROWSER:** en este entorno la navegación de Chromium a `http://127.0.0.1` y a `file://` devolvió `ERR_BLOCKED_BY_ADMINISTRATOR`. Se probó usando `page.set_content` con HTML autocontenido **dentro de Chromium real**. Por ello, el test de **recarga en origen HTTP** se entrega en `tests/panel-01-chat.spec.js` pero no se declara completado aquí. La página `about:blank` no proporciona `localStorage` persistente, por lo que sería incorrecto afirmar RELOAD PASS basándose en ella. En un navegador normal, probarlo ejecutando Vite/servidor HTTP y Playwright JS.

## Matriz de aceptación, sin inventar PASS

| ID | Estado | Evidencia / pendiente |
|---|---|---|
| TEST_REFERENCE | **REVIEW** | Valores Little/Matte/Blanco copiados de skill 01; aprobación visual 1:1 requiere comparación final del propietario. |
| TEST_LAYOUT | **PASS** | No overflow horizontal a 1440 y 390. |
| TEST_BUTTONS | **PASS** | Acciones de chat, archivos, roots, import/export, reset en navegador; ausencia de bridge tratada como fallo. |
| TEST_DROPDOWNS | **PASS** | Modelo, mode-sheet y selector de idioma. |
| TEST_TABS | **PASS** | Navegación chat/files/wall/settings y pestañas de archivos. |
| TEST_INPUTS | **PASS** | Composer, búsqueda y notas de raíz. |
| TEST_STATE | **PASS (SESIÓN)** | Estado cambia, se exporta, importa y reinicia; no se afirma persistencia tras recarga. |
| TEST_RELOAD | **BLOCKED_ENV** | Falta ejecutar con URL localhost real por bloqueo de navegación en este entorno. |
| TEST_DESKTOP | **PASS** | Chromium 1440×900, captura disponible. |
| TEST_MOBILE | **PASS** | Chromium 390×844, navegación móvil, captura disponible. |
| TEST_CONSOLE | **PASS** | `pageerror` = 0 en ambos tamaños. |

**Balance:** **9/11 PASS**, 1 `REVIEW` (aprobación de referencia visual) y 1 `BLOCKED_ENV` (recarga en URL real). La integración con proveedor/modelos también es `BLOCKED_REMOTE` hasta conectar una implementación autorizada de `window.YAIWES_PLUGIN_BRIDGE`.

## Prueba automatizada en entorno con servidor real

```bash
npm install
npx playwright install chromium
npm test
```

El test `tests/panel-01-chat.spec.js` incluye la recarga real (`page.reload()`), además de valores canónicos de HEX, 7 temas, eventos, selector, archivos, estado local y errores. No se puede tratar como PASS hasta ejecutarlo en el entorno destino.

## Evidencia y arquitectura

- Código canónico: `index.html` + `styles.css` + `app.js` + `src/lib/actionBus.js`.
- Capturas: `screenshots/desktop-little.png`, `desktop-gris.png`, `mobile-little.png`, `mobile-gris.png`, y configuración.
- Inspector del código: `manifest.json`; reglas: `SKILL.md`, `AGENTS.md`.
- Snapshot generado: `python3 tools/build_snapshot.py`; no editar el snapshot a mano.
- Ningún repositorio remoto o archivo fuente original ha sido modificado.

**Referencias visuales preservadas:** `snapshot/reference-files-grok.jpg` y `snapshot/reference-mode-grok.jpg`, copias de las imágenes que el propietario subió para revisión.
