# INPUT VERBATIM DEL DIRECTOR — 2026-09-22 (bb) — contrato DSL DAG Sheriff formal, watchdog cada 30-60 min, GPT como supervisor adicional

Registrado ANTES de ejecutar. El Director adjuntó el documento `yaiwes.node-executor/xray-v2` (contrato formal RESEARCH→EXECUTE→VALIDATE, FAIL_CLOSED, JSON obligatorio, máx. 2 reintentos, anti-loop, captura verbatim del input) — texto completo ya visible en el chat de esta fecha; se archiva como referencia en vez de duplicar sus ~260 líneas aquí. Es una versión más detallada del mismo método ya usado como base del Sheriff (`agent-microkernel/kernel/sheriff.py`) y de `chain.yaml`.

---

Exacto así es ahora coloca un wachdog activo para que te actives cada 30 minutos o cada 1 hora para estar pendiente mientras el sentinela supervisor detecta y revisa por ti 

La única manes de no fallar es que trabajes deteminetista con los agentes si tus promt son ambiguos no funcionan 

Así que cuidas esos todo debe ser un shema contrato DSL Dag shema sheriff 
Como son agente puedes bloquear ciertas salidas para que no la caguén la clave está en ese sentido te di uno de ejemplo lo mejoras 100 veces 

Tengo dentro a gpt sol si lo necesitas lo activo adicional con un wachdog con tu instruccion sirve solo como supervisor porque alucina 

Analiza todo y planifica cada tarea antes de ejecutar anota todos 1 a 1 imput block verbartin 

Incia te dejo todo en tus manos 

Alguna pregunta?

---

## Cola 1 a 1
BB1. Adoptar el contrato `yaiwes.node-executor/xray-v2` (RESEARCH→EXECUTE→VALIDATE, JSON obligatorio, FAIL_CLOSED) como la forma exigida de cada tarea de agente.
BB2. Watchdog: Claude se activa cada 30-60 minutos, mientras el centinela (sheriff) supervisa y revisa por Claude en el medio.
BB3. Regla de oro: trabajar determinista con los agentes; prompts ambiguos no funcionan.
BB4. Todo debe ser esquema/contrato DSL DAG con Sheriff; como son agentes, se pueden bloquear ciertas salidas para que no se equivoquen — el documento adjunto es el ejemplo a mejorar "100 veces".
BB5. El Director tiene un GPT disponible ("GPT Sol", nombre cortado); si Claude lo necesita, el Director lo activa como supervisor adicional, bajo instrucción de Claude — solo como supervisor, porque alucina (no como ejecutor).
BB6. Analizar todo y planificar cada tarea antes de ejecutar; anotar todo 1 a 1 input block verbatim.
BB7. "Inicia, te dejo todo en tus manos." Pregunta: ¿alguna duda?

## Respuesta de Claude a BB7
- Ya se sigue el mismo patrón (research→execute→validate con Sheriff determinista en `chain.yaml`); se va a endurecer contra este contrato formal (JSON obligatorio, máx. 2 reintentos, anti-loop) en la próxima ronda.
- Watchdog: hoy corre cada hora (`riu-watchdog.yml`); se puede bajar a 30 min si se prefiere más reacción — Claude decide 1 hora por defecto salvo que el Director diga lo contrario.
- GPT como supervisor adicional: para conectarlo de verdad, Claude necesitaría una clave de API de OpenAI (o el conector correspondiente) — sin eso no se puede invocar. Queda pendiente hasta que el Director la dé.
