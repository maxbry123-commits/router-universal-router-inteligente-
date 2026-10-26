# Grok: prueba total del chat (después de la reorganización y el revert del frontend)

Repo: `maxbry123-commits/router-universal-router-inteligente-` rama `main`. Clona con `--branch main`.
Regla: PASS solo con salida real de comando o captura. No cambies nada si no te lo piden: solo prueba y reporta.

## 0. Qué cambió (para que sepas qué mirar)
- Código en dos raíces: `chat/frontend/` (Vercel, Root Directory ahora `chat/frontend`) y `chat/backend/` (`mvp/`, `deepseek_harness/`, `router_api_cliente.py`).
- Enlaces de compatibilidad en la raíz: `mvp -> chat/backend/mvp`, `plugins/deepseek_harness`, `plugins/router_api_cliente.py` (el Space arranca `python -m mvp.run`).
- Frontend: se eliminó `composer-filas.js/css` (cubo, Detener y controles vuelven como en la base; etiquetas de modo originales). Se mantienen Groq, permisos del servidor y cableado del selector.

## 1. Repo (sin red)
```
git clone --branch main https://github.com/maxbry123-commits/router-universal-router-inteligente-.git && cd router-universal-router-inteligente-
ls -la mvp plugins/deepseek_harness plugins/router_api_cliente.py        # deben ser enlaces
python3 chat/auditoria/cableado.py                                       # esperado: FAIL=0 (hay 14 avisos conocidos)
python -m pytest mvp -q                                                  # esperado: 221 passed
bash chat/e2e/todo.sh                                                    # batería Playwright (ver chat/e2e/README.md)
```
Esperado en `todo.sh`: todas las suites `0 FAIL` (modelos 10+10, paso2 26, RUI 23+23, paso 2.1 23+23, teclado 12, original 15, tools_ctl 9+9, botones 0 por revisar, pytest 221).

## 2. Producción web (Vercel `riu-jev-bridge.vercel.app`, móvil 345×700 y escritorio)
1. Abre `/chat/ui/version.json`: el `commit` debe empezar por el último de `main` (`git rev-parse --short HEAD`).
2. Recarga dos veces. A la vista y sin abrir ventanas: adjuntar, archivos, ancla, sandbox, micrófono, copiar, Auto, Detener, pendientes, IA, Agentes, System prompt, Enviar.
3. Envía «hola»: debe verse el cubo de pensamiento con segundos mientras trabaja y Detener siempre visible.
4. Modos: las etiquetas deben ser «Rápido — 512 tok», «Equilibrado — 1024 tok», «Pensar — 2048 tok».
5. Selectores: enciende uno, pregunta «¿qué modelo eres?» y comprueba que responde el del selector (Qwen 3.8 Max, un modelo Groq, uno NVIDIA). Si no hay selector encendido debe avisar cuál responde.
6. Chips IA / Agentes / System prompt: cada clic cambia de estado y se mantiene al recargar.
7. Captura de pantalla de cada paso; anota cualquier botón que se solape o no responda.

## 3. Router en vivo (Space `comand-center-1-riu-router.hf.space`) por HTTP y MCP
```
python3 -m mvp.pruebas_vivo.conectividad      # 16 pruebas de HTTP + MCP
python3 -m mvp.pruebas_vivo.guion             # guion MCP (docs/PRUEBAS_MCP.md)
```
- `GET /health` debe mostrar el commit nuevo (esperado: el de `main`). Si muestra uno viejo, reporta: el autopull no actualizó o rechazó el commit (revisa si sigue cargando `mvp.app`).
- MCP: `tools/list` (13 herramientas), `salud` (commit, modelos, nº de claves Groq/NVIDIA, permisos).
- t4 (delegación LLM) exige IA ON: pídele al Director que la encienda en el chat y repite.
- Alias: `ficha-qwen38max` debe resolver a `qwen3.8-max`.
- Tareas t1–t6 en 10 modelos de texto más, y modelos de imagen/voz (`--medios`) repartidos con Sol y GPT.

## 4. Qué reportar
Tabla `prueba | PASS/FAIL | evidencia (salida o captura) | commit probado`. Para cada FAIL: pasos exactos, pantalla (345×700 o escritorio), consola del navegador y qué esperabas. No arregles; pásalo al Director.

## 5. Conocido pendiente (no es fallo nuevo)
Narración en vivo de pasos del modelo (backend), botón «Nuevo proyecto» en la caja, rediseño de selectores, 23–25 componentes RIU (no existen en el skill), paneles Archivos/Canvas/Organización/Seguimiento llaman a `/chat/documents` y `/chat/org/*` que el Router MVP no sirve, claves Groq/NVIDIA del Space por confirmar.
