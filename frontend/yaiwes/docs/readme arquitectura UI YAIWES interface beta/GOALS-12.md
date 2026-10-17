# 12 GOALS · entrada y salida de cada ventana

Obligatorio en **toda** entrega HTML (antes de `OK`).  
Checklist en `UI code versiones/<ID>/CHECKLIST.md`.

## Del director

| # | Goal | Cómo se prueba |
|---|------|----------------|
| G01 | **No mock estático** | Cada control cambia estado. Fetch real si hay URL. Si no hay backend: log `SIN_BACKEND` visible en panel privado, no “éxito falso”. |
| G02 | **Botones en sandbox + backend privado** | 5 clicks. Panel **Factory** (clave, no es UI de usuario) para pegar URL, headers, función backend. |
| G03 | **Sandbox de ejecución por proceso** | Cada nodo/proceso corre code interno (iframe `sandbox` o worker). Timeout/memoria editables. |
| G05 | **Respeta el skill** | Tokens Matte `#0a0a0d` · Little `#2563eb` · Blanco `#ffffff` · naranja `#ff5500` solo Cargar/Descargar. |
| G06 | **Respeta instrucciones** | 1 ventana = 1 archivo. LOOP S0–S8. Sin unificar. |

## Del agente (las otras 6 + G04)

| # | Goal | Cómo se prueba |
|---|------|----------------|
| G04 | **Unir después de OK** | `FROMTED_MANIFEST.in/out` + `postMessage` + `CustomEvent`. Host puede cargar N ventanas. |
| G07 | **Plugins por botón** | Cada acción primaria emite evento `FROMTED_*` y llama `plugins.out`. |
| G08 | **01-original intacto** | Hash del source no cambia. FROMTED solo paleta/enchufes. |
| G09 | **Evidence + cruz** | `EVIDENCE.json` 5 clicks. 5 pasadas (hash, JS, tokens, ID, bitácora). |
| G10 | **Config interna 0 fricción** | Nombre i18n, on/off, no layout soldado. |
| G11 | **Factory ≠ producto** | Backend/sandbox config **nunca** en la UI del usuario final. |
| G12 | **Retomar cualquier ID** | Fotos + handoff + bitácora + este checklist por ventana. |

G01–G12 = **puerta S6**. Falta uno → no pido `OK`.
