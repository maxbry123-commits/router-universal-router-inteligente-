# Verificación: cómo probar y cómo declarar el resultado

## Estados permitidos

| Estado | Cuándo |
|---|---|
| `PASS` | Ejecutado en navegador real, con evidencia guardada (captura, log, salida del test) |
| `FAIL` | Ejecutado y fallado. Anotar el error observado |
| `REVIEW` | Revisado por código o comparado visualmente, sin ejecución completa. O pendiente de aprobación del propietario |
| `BLOCKED` | No se pudo ejecutar, con la causa escrita (falta archivo, puerto, entorno) |
| `BLOCKED_REMOTE` | Depende del bridge real y no hay backend conectado |
| `BLOCKED_ENV` | El entorno impide la prueba (por ejemplo, navegación bloqueada a localhost) |

No escribir `PASS` para algo que no se ejecutó. Un `pageerror: 0` del snapshot no prueba que el código fuente esté libre de errores.

## Qué se ejecutó en esta revisión

Solo una sonda ad hoc, fuera del repo. Se usó `actionBus` extraído del snapshot y `app.js` sin modificar. Ver `hallazgos-revision.md`.

| Escenario | Resultado observado |
|---|---|
| Localhost, bridge de prueba `ok:true` | Añadir archivo: `FAIL` (`window.makeId is not a function`, 0 archivos). Enviar: `FAIL` (borrador conservado, sin mensaje, botón deshabilitado). Navegar a Configuración: funciona en la sonda (no es PASS: una sola ejecución, sin captura) |
| Localhost, sin `actionBus.js` | Navegar: `FAIL` (estado cambia, DOM no). Enviar: `FAIL` (botón bloqueado). Errores `Cannot read properties of undefined (reading 'execute')` |

La suite Playwright del proyecto (`tests/panel-01-chat.spec.js`) no está en los uploads. Ningún `PASS` de ACCEPTANCE se reproduce desde estas fuentes.

## Entorno de ejecución

- Chromium para Playwright ya instalado en este entorno: `/opt/pw-browsers/chromium-1243/chrome-linux64/chrome`. Headless shell: `/opt/pw-browsers/chromium_headless_shell-1243/chrome-headless-shell-linux64/chrome-headless-shell`.
- `npx playwright install chromium` solo si falta ese binario.
- Python sin `playwright` en este entorno; la suite es Node.
- `chrome --headless=new --dump-dom` se quedó colgado (timeout 120 s). Con el headless shell funcionó: `--no-sandbox --disable-gpu --virtual-time-budget=5000 --dump-dom URL`.

## Cómo correr la suite (cuando el fuente esté en el repo)

Desde la carpeta del proyecto (`package.json`, `vite.config.js`, `playwright.config.js` de los uploads):

```bash
npm install
npm run dev                  # vite --host 127.0.0.1 --port 5173
npx playwright test --trace off         # override de trace: retain-on-failure del config
npx playwright test tests/panel-01-chat.spec.js --trace off
```

- `baseURL` y `webServer` apuntan a `http://127.0.0.1:5173`. `reuseExistingServer: true`.
- `--trace off` evita trazas pesadas. Las capturas se guardan con `screenshot: only-on-failure`.
- El snapshot se regenera con `python3 tools/build_snapshot.py` (no está en los uploads). No editar el snapshot a mano.

### RELOAD: origen real obligatorio

La persistencia de `localStorage` no vale en `about:blank`, en `file://` ni con `set_content`. La prueba de recarga debe ir en `http://127.0.0.1:5173` y usar `page.reload()`. Si el origen es distinto, marcar `BLOCKED_ENV`.

## Matriz de 11 comprobaciones

Las 11 comprobaciones son las de SKILL §7. Esta columna es el estado de esta revisión, no el del proyecto.

| ID | Evidencia mínima | Estado en esta revisión |
|---|---|---|
| REF | HEX canónicos contra `styles.css` + comparación visual con la referencia | REVIEW. Hex verificados en `tokens.md`. Sin capturas de referencia |
| LAYOUT | Sin scroll horizontal a 1440 y 390 px | BLOCKED. No se ejecutó |
| BUTTONS | Cada botón tiene acción real o bloqueo explícito | FAIL (adjuntar y añadir archivos, por hallazgo 1). Resto: REVIEW |
| DROPDOWNS | Cambio confirmado o borrador cancelable (modelo, modo, idioma) | REVIEW |
| TABS | Panel correcto y `aria-selected` | REVIEW. `aria-selected` presente en `app.js:86` |
| INPUTS | Teclado y clic; datos validados (nombre de raíz, nota, import) | REVIEW |
| STATE | Cambios locales visibles y veraces | FAIL (archivos no se guardan, hallazgo 1; cuota, hallazgo 3) |
| RELOAD | Persistencia en origen HTTP real | BLOCKED. Sin spec. Además, hallazgo 3 |
| DESKTOP | Captura y prueba a 1440×900 | BLOCKED. No se ejecutó |
| MOBILE | Captura, scroll, tap, navegación inferior a 390×844 | BLOCKED. No se ejecutó |
| CONSOLE | Cero errores JS inesperados | FAIL (`makeId` y `execute` leídos en la sonda) |

Remoto: `BLOCKED_REMOTE` para `chat.send` hasta tener un bridge real y una prueba de integración. Sin backend, la UI debe mostrar `BRIDGE_MISSING`.

## Qué incluir al declarar un lote

Para cada lote: fuente, referencia visual, archivo tocado, versión, tema, acciones tocadas, comando de prueba, rutas de capturas, estado por comprobación, diferencia y reparación. Esto va en `VERSION.md` y `ACCEPTANCE.md` del proyecto.
