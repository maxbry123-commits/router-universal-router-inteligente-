# README DE NOTAS DE CLAUDE — WATCHDOG (contra la sobre-ingeniería)

Escrito por Claude para Claude (y para cualquier agente) por orden del Director (`INPUT-VERBATIM-2026-09-21-r-…`). Léelo ANTES de tocar el watchdog o los agentes.

## Reglas del Director (no negociables)
1. Hasta que el Director regrese, Claude queda a cargo. **Sin sobre-ingeniería y sin hacer NADA fuera de sus instrucciones.** Si algo debería cambiar respecto a lo que él indicó (diseño, herramientas, marcos), se le PREGUNTA; no se decide y se anota como "desviación".
2. Modo loop/bucle: no parar ni escalar hasta terminar todas las tareas. Se trabaja SOLO con lo que él pidió: terminar el chat, terminar HF (modelos de IA en HF), las auditorías, Muse Glimmer + agentes Meta, el puente con Jev.
3. Consumo mínimo de tokens de pago: los agentes usan solo NVIDIA, Groq y Cerebras (DeepSeek V4 Flash / MiniMax M3 únicamente como respaldo si toda la ruta falla). El watchdog no usa ningún modelo.
4. Anotar cada instrucción del Director textual (1 a 1) antes de ejecutar. Lo que no se pueda resolver es un GAP, no se inventa.
5. Claude delega: el cerebro edita el DSL DAG (`chain.yaml`, `ROUTE.json`); los agentes ejecutan y anotan; el Sheriff (determinista) da el PASS.

## Qué hace este watchdog y qué NO
- SÍ: cada hora lee los Crazy Wall, escribe `STATUS.md` y `LOG.md` y relanza `RIU Agents Run` si hay agentes pendientes (máx. 3 veces sin avance).
- NO: no edita cadenas, no crea agentes, no cambia rutas, no gasta modelos, no toca nada fuera de `agents-yaiwes/WATCHDOG/`.
- Límite honesto: Claude no puede despertarse solo cada hora. El watchdog deja el estado listo; Claude lo lee al abrir sesión o cuando el Director lo pida. Si `STATUS.md` dice "ESCALAR A CLAUDE": mejorar la ruta o el DSL DAG del agente lento y, solo si sigue lento, proponer más agentes (2 o 4) al Director.

## Orden de trabajo (la forma más corta)
Auditor → convertir sus PENDIENTES en pasos de las cadenas → cerrar chat y HF → repetir la auditoría para LLM locales → Muse Glimmer + agentes Meta → puente con Jev (bloqueado por permisos de Vercel).
