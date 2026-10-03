# Chat frontend · Wordflow YAIWES

Este módulo vive íntegramente en `chat router/chat fromtend/`. `index.html` carga el panel de chat (`src/panels/chat.js`), su configuración (`src/panels/settings.js`) y las ventanas individuales en `src/windows/`. Los paneles 03 y 04 tienen archivos separados pero no están implementados ni expuestos. No se ha reemplazado ni modificado `chat router/space/` ni su backend.

## Contrato de integración

El host debe inyectar `window.YAIWES_PLUGIN_BRIDGE.execute(actionId, payload)` **antes** de usar comandos remotos. Cada intento emite `yaiwes:ui-action` con `{ actionId, payload }`; ese evento es observabilidad, **no** confirmación. El bridge debe devolver un objeto de confirmación **con `ok: true`** o devolver `{ ok: false, error: "…" }` / rechazar en caso de fallo. La falta de bridge da `BRIDGE_MISSING`, y un comando vacío da `ACTION_UNCONFIGURED`. No hay URL, modelo ni respuesta simulada.

- `chat.send`: payload `{ message, modelId, modeId, selectors, toggles, attachments: [{name, file, attachmentId}] }`; el resultado **debe** traer `{ reply: string }`. Solo entonces se añaden los mensajes al historial y se limpia el borrador. `File` es un archivo real en memoria del navegador. El adaptador del host tiene que gestionar transporte, autenticación, límites y validación; ninguna clave vive aquí.
- Subida: `attachActionId` recibe `{ file, name, size, type }`, confirma `{ attachmentId }`. Si falla se mantiene el archivo local, marcado **local**, y se puede pasar su `File` real al bridge al enviar. La confirmación de envío del mensaje es independiente de la confirmación de subida.
- Voz: el permiso del micrófono lo pide el navegador; `voiceActionId` recibe `{ audio: Blob, mimeType }` al detener la grabación. Watchdog y ocho toggles se marcan activos únicamente tras confirmación del bridge.
- Modelos: se editan como pares `id | nombre`; opcionalmente `modelsActionId` trae `{ models: [{id,label}] }`. El `modelActionId` confirma la selección remota si está configurado; si no lo está, la selección es local y se envía al backend en `chat.send`. Los modos funcionan igual; cada uno tiene su propio `actionId` opcional.
- Las cinco ventanas reciben opciones configurables `id | nombre | actionId`. Seleccionar una opción invoca su comando (o el comando del selector) con `{ selectorId, optionId }`; sin comando no se declara éxito.
- Habilidades y conectores invocan los comandos configurados y esperan `{ items: [{id,label,description}] }`. Los 12 comandos del menú + y los ocho controles de encendido también se configuran por `actionId`.

Los nombres y descripciones de los controles principales, ocho modos, cinco selectores, ocho toggles y doce funciones se editan en Configuración. La configuración editable se guarda en `localStorage` solo para esta interfaz; no incluir tokens, credenciales ni código JavaScript. Los mensajes y archivos no se persisten. Esta carpeta **no está servida todavía por** `chat router/space/app.py` (ese servicio usa su propio `index.html`); el montaje en backend queda para una fase autorizada.

Validación local sin servidor ni prueba visual: `npm test` y `npm run check`. La comprobación visual y el despliegue esperan autorización expresa del propietario.
