# S1-18 Plantilla T-11 seccion O contra el arbol real (sin mover archivos)

Fuente: `chat router/01-PLAN/T-11/T-11-00-INPUT-BLOCK-VERBATIM.md` seccion O (lineas 417-438) y T-11-04.
Regla literal de la plantilla: el arbol es un MODELO DE REFERENCIA; sustituirlo por carpetas REALES; no crear carpetas solo para completar el dibujo.
Por eso no se movio ni creo ninguna carpeta. El repo ya trae la estructura numerada `chat router/00..13`.

| Nodo de la plantilla | Carpeta real verificada |
|---|---|
| Router principal | `router inteligente universal/` (solo lectura) |
| Memoria | `chat router/04-MEMORIA/` |
| Estado | `chat router/03-ESTADO/` |
| Workflows | `chat router/wordflow loop code Yaiwes/`, `chat router/📂 workflow Loops code Yaiwes/`, `chat router/➡️📂 Wordflow LOOP Yaiwes/` |
| MCP | `chat router/wordflow loop code Yaiwes/minimax_mcp/` |
| Pruebas | `runtime/tests/` dentro de cada carpeta de wordflow code |
| Evidencia | `chat router/11-EVIDENCIA/` |
| Harness DeepSeek | `chat router/deepseek-harness-chat/` |
| Motores descarga/busqueda | `Motores descarga extracción búsquedas/` y `chat router/➡️📂motores de descarga extracción copiado movimiento archivos agentes/` |
| Subrouters, APIs, Skills, Procesadores | sin carpeta propia verificada (no se inventa) |

No mover: las pruebas de motores buscan la ruta `chat router/➡️📂motores de descarga ...` y la de Wordflow tiene HANDOFF propio; mover rompe rutas.
Acuerdo: el arbol real sale en ARCHITECTURE-XRAY (T-11-04) que hace Haiku.
