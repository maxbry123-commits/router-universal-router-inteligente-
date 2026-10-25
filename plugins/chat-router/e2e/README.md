# Pruebas del chat en navegador (e2e)

Servidor local (`servidor.py`): el Router real (`mvp/app.py`) con modelos simulados (`qwen`, `groq`), HF en memoria y `/api/power` simulado, sirviendo el frontend tal como lo hace Vercel (`build.sh`). **No toca el Space ni gasta tokens.**
`bash plugins/chat-router/e2e/todo.sh` corre todo. Una suite suelta: `python3 servidor.py &` y luego `node paso2.js`.

| Suite | Qué comprueba |
|---|---|
| `modelos_e2e.js` | el modelo que responde es el del selector (glm → qwen3.8 con historial de otro → Groq → tras recargar) |
| `paso2.js` | botones, chips, respuesta en texto, medios, Continuar, checklist |
| `composer3_e2e.js` | caja de escritura: 3 selectores sin pisarse en 4 pantallas, ventanas, Detener |
| `rui.js` | los 22 componentes RIU |
| `paso21.js` | Conexiones, ROOM, Servidor |
| `tools_ctl.js` | LLM tool / Agente tool / Proyectos / modo Objetivo |
| `botones.js [movil\|desk] [hoja:#boton:#ventana]` | pulsa de verdad cada botón y exige un efecto |
| `axe.js`, `teclado.js` | accesibilidad WCAG 2.2 AA y teclado |
| `narracion.js`, `inventario.js`, `phone.js` | diagnóstico: cubo de pensamiento/Detener/textos de espera; inventario base vs. actual; captura a 345×700 |

Si `playwright`/`axe-core` están en otra carpeta: `NODE_PATH=/ruta/node_modules CHROMIUM=/ruta/chromium AXE_JS=/ruta/axe.min.js bash plugins/chat-router/e2e/todo.sh`.
