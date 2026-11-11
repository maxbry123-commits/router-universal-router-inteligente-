# Contrato de acciones (action bus)

Fuentes: manifest (upload `093b534c-__manifest_3.json`, bloques `actions`, `backend`), `app.js` (upload `c8312e59-app.js`). La implementación del bus, `src/lib/actionBus.js`, no está en los uploads. La única copia disponible es la inline del snapshot (`47b98c1c-index-standalone.html`, líneas 112-146). Todo lo que sigue sobre el bus sale de esa copia y queda como **UNKNOWN** hasta tener el fuente.

## Reglas

1. Toda interacción emite `yaiwes:ui-action` con `detail: {actionId, payload, remote, timestamp}`.
2. **Solo `chat.send` es remoto.** Es la única llamada con `remote=true` (`app.js:155`). El resto son locales.
3. Una acción remota se considera completada solo con confirmación real del bridge. Un evento `yaiwes:ui-action` **no** es prueba de ejecución.
4. Sin bridge, la acción remota falla cerrada: devuelve `BRIDGE_MISSING`, el borrador se conserva y no aparece ninguna respuesta.

## Acciones (23, igual en manifest y en la allowlist del bus)

| actionId | Emitida en `app.js` | Tipo | Notas |
|---|---|---|---|
| `chat.send` | 155 | **REMOTA** | Payload: `{message, model, mode, tools, attachments:[{name,mime,size,dataUrl}]}` |
| `chat.close` | 197 | local | Borra mensajes, adjuntos y borrador, sin confirmación |
| `chat.export` | 147 (botón `index.html:55`) | local | Descarga JSON del chat |
| `chat.attach` | 198 | local | Abre el selector y añade a adjuntos |
| `mode.select` | 216 | local | Confirmado en el sheet de modo |
| `mode.thinking.toggle` | 216 | local | `enabled = modo think` |
| `model.select` | 233 | local | `change` sobre `#modelSelect` |
| `tool.document.toggle` | 205 | local | `tool.<k>.toggle` con k = document |
| `tool.website.toggle` | 205 | local | k = website |
| `tool.image.toggle` | 205 | local | k = image |
| `files.add` | 130 | local | Una emisión por archivo añadido. El botón (199) solo abre el selector |
| `files.pin` | 207 | local | |
| `files.download` | 138 | local | Solo si hay `blob:` o `data:` válido |
| `files.search` | 229 | local | Emitida en cada `input` del buscador |
| `wall.status.set` | 218 | local | Al guardar la raíz |
| `wall.note.set` | 218 | local | Al guardar la raíz |
| `wall.root.add` | 222 | local | |
| `theme.select` | 111 | local | |
| `locale.select` | 234 | local | |
| `ui.navigate` | 110 | local | |
| `ui.settings` | 211 | local | Toggles de movimiento y ayudas |
| `state.export` | 145 | local | Descarga JSON de estado |
| `state.import` | 238 | local | Emitida tras importar; el botón (202) solo abre el selector |
| `state.reset` | 224 | local | Emitida al confirmar; el botón (203) solo abre el sheet |

### Fuera del manifest

- `files.delete` (`app.js:209`): no emite nada. El borrado no tiene rastro de evento.
- `mode.open` (`app.js:195`, `data-action`): abre el sheet sin emitir acción.

Si se añade una acción, debe entrar en el manifest, en la allowlist del bus y en esta tabla. No se renombra un `actionId` sin migración (SKILL §8).

## Respuesta de `execute()` (copia del snapshot)

| Caso | Respuesta |
|---|---|
| ID fuera de allowlist | `{ok:false, code:'UNKNOWN_ACTION', actionId}` |
| Local | `{ok:true, code:'LOCAL_ACTION'}` |
| Remota sin bridge | `{ok:false, code:'BRIDGE_MISSING', actionId}` |
| Remota, bridge responde sin `ok:true` ni `status` de éxito | `{ok:false, code:'BRIDGE_REJECTED', result}` |
| Remota, bridge lanza excepción | `{ok:false, code:'BRIDGE_ERROR', error}` |
| Remota, éxito | `{ok:true, code:'REMOTE_OK', result}`, donde `result` es la respuesta cruda del bridge |

`app.js:157` solo muestra `result.code` en el toast. El campo `error` del bridge se pierde (hallazgo 4 en `hallazgos-revision.md`).

## Formato esperado del bridge

```js
// Contrato: window.YAIWES_PLUGIN_BRIDGE.execute(actionId, payload)
// Éxito:  { ok: true, reply: "texto producido por el modelo real" }
// Fallo:  { ok: false, error: "motivo" }
```

- `app.js:159` lee `result.result.reply`, y como alias `message` (`app.js:160`). El alias no está en el contrato.
- El bus acepta además `status` en `success`, `done` o `completed` sin `ok:true`. Eso se aparta del contrato (hallazgo 4).
- Si el bridge responde `{ok:true}` sin `reply`, la UI muestra "enviado" y no añade respuesta. Es un comportamiento válido, pero no es el contrato completo.
- El bridge nunca vive en el frontend. No poner en el navegador endpoints, PAT, API keys ni `token_ref` resueltos. Los secretos viven en el runtime seguro.

## Archivos y remoto

- Los adjuntos hasta 1 MB viajan en `dataUrl` (`app.js:154`). Los mayores (volátiles) se bloquean en `app.js:152` con un toast en español fijo. No hay bridge de subida: UNKNOWN.
- Cada envío limpia el borrador y los adjuntos solo tras `ok:true` (`app.js:162`).
