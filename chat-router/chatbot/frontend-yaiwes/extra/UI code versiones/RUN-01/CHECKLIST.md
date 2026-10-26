# CHECKLIST RUN-01 CASCADE · antes de OK

Ventana: **RUN-01** · archivo: `RUN-01-CASCADE.html`  
Source: `Ui Yaiwes interface beta/01-original/RUN/UI-YAIWES-Run.html` (solo vista CASCADE)  
Estado: **S6 SHOW** — no está en `02-fromted` hasta `OK RUN-01`.

## 12 goals

| G | Resultado | Evidencia |
|---|-----------|-----------|
| G01 No mock | PASS | + / modelo / rol / Run / Parar / Copiar YAML / dest cambian S. Fetch si hay URL factory. Sin URL → `SIN_BACKEND` en log privado. |
| G02 Botones + BE privado | PASS | Factory (clave). Campos method/url/headers/fn. No está en chrome de producto. |
| G03 Sandbox por proceso | PASS | Cada nodo: backend docker/subprocess, timeout, mem, **Probar sandbox** ejecuta transform JSON en iframe sandbox. |
| G04 Unir ventanas | PASS | `FROMTED_MANIFEST` + `postMessage` + events `FROMTED_CASCADE_*`. |
| G05 Skill | PASS | `--matte #0a0a0d --little #2563eb --fg #ffffff`. Naranja solo botón Cargar/Descargar. |
| G06 Instrucciones | PASS | 1 archivo. Sin tabs TREN/AUDITOR/ORQUESTA. |
| G07 Plugins botón | PASS | Run, +IA, + slot, dest, yaml, sandbox emiten `FROMTED_*`. |
| G08 Original | PASS | `01-original/RUN/UI-YAIWES-Run.html` no tocado. |
| G09 Evidence | PASS | Ver `EVIDENCE.json` (5 clicks simulados en parser). |
| G10 Config | PASS | Nombre nodo, on/off (quitar), i18n ES en labels. |
| G11 Factory ≠ user | PASS | Panel `#factory` hidden hasta clave. |
| G12 Resume | PASS | Fotos INDEX + handoff + este checklist. |

## 5 clicks (S4)

1. Abre → CASCADE visible.  
2. `+` inserta IA.  
3. Cambia modelo.  
4. Run → nodos running/done.  
5. Recarga: no rompe (localStorage opcional; default RAM).

## Cómo se une (después de OK)

Host:

```js
iframe.src = "RUN-01-CASCADE.html";
iframe.onload = () => iframe.contentWindow.postMessage({fromted:"HOST_THEME", tokens:{...}}, "*");
window.addEventListener("message", e => {
  if (e.data.fromted === "CASCADE_YAML") guardar(e.data.payload);
});
```

Backend privado (tú, no el usuario): Factory → URL `POST /api/agent/complete` → Run dispara `fetch`.
