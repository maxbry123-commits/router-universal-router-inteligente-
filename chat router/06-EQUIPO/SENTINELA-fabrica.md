# SENTINELA FABRICA — 2026-09-27 12:31 UTC
(modelo: moonshotai/kimi-k3@NVIDIA_API_KEY_2)

ESTADO: rojo — la tarea fabrica-01 (6 motores) está activa pero no hay ningún trabajo visible: cero commits, ramas, PRs y ejecuciones.

AVANCE:
- Ningún archivo de `fabrica de UI INTERFACE fromtend/motores/` aparece en los datos.
- El HANDOFF solo cubre chat-yaiwes (M-0..M-7 completados por Manus); no menciona la fábrica.
- La orden del Director (27-sep) exige terminar chat y motores; los motores no han arrancado.

DESVIOS DEL PLAN:
- Tarea fabrica-01 activa sin agente asignado ni ejecución lanzada (no se creó `TAREAS/fabrica-01.md` ni se pulsó el workflow, o no consta).
- Sin evidencia de lectura del documento 18 ni del repo frontend.

ORDENES CORRECTIVAS:
1. Agente coordinador: crear `TAREAS/fabrica-01.md` copiando el formato de `chat-01.md` y lanzar el workflow "Equipo Claude Code (espejos)" con id fabrica-01.
2. Agente espejo: leer `chat router/00-INSTRUCCIONES/INPUT-BLOCK-VERBATIM-CHAT-Y-PANEL-PARTE-4.md` (doc 18) y la carpeta `fabrica de UI INTERFACE fromtend/` antes de escribir código.
3. Agente espejo: entregar los 10 entregables dentro de `motores/` y dejar pasando `python -m pytest "fabrica de UI INTERFACE fromtend/motores/tests" -q`.
4. Agente espejo: abrir PR contra main en repo frontend y registrar la ejecución para que el Sentinela pueda validar.

PARA OPUS (solo si hay algo roto en Router/HF): nada
