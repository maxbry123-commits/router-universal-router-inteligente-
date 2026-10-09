# H-01, H-02 y H-05 — Inventario, mapa de destino y comparación (EQUIPO-2)
Ejecutado por Claude (el chat de Haiku no tenía acceso a GitHub). Rama: devin/1790824641-chat-agent-plan. Fecha: 2026-10-02. Solo lectura: no se movió ni se borró nada.

## H-01 Inventario de lo que hay suelto en `chat router/`
Archivos sueltos en la raíz (5):
- INPUT-BLOCK-VERBATIM-CHAT-Y-PANEL.md (50391 bytes)
- INPUT-BLOCK-VERBATIM-CHAT-Y-PANEL-PARTE-3.md (18369 bytes)
- INPUT-BLOCK-VERBATIM-CHAT-Y-PANEL-PARTE-4.md (32495 bytes)
- ORQUESTADOR-DE-TRABAJO.yaml (4790 bytes)
- PLAN-DSL-DAG-CHAT-AGENTES-INFRA.yaml (10958 bytes)

Carpetas numeradas: 00-INSTRUCCIONES, 01-PLAN, 02-ARQUITECTURA, 03-ESTADO, 04-MEMORIA, 05-AGENTES, 06-ESPEJOS, 07-SENTINELAS, 09-CLAUDE-CODE, 10-CHAT-FUNCIONES, 11-EVIDENCIA, 12-FABRICA-MOTORES, 13-CHAT-UI-SUITE. (No existe la 08.)
Carpetas sin número: chat_orders, deepseek-harness-chat, space, ui.

Cuatro carpetas con nombre parecido al del Wordflow:
1. `wordflow loop code Yaiwes` (la original)
2. `📂 workflow Loops code Yaiwes` (la nueva, copia exacta, creada en la ronda 0)
3. `➡️📂 Wordflow LOOP Yaiwes` (solo contiene la carpeta de motores)
4. `➡️📂motores de descarga extracción copiado movimiento archivos agentes` (a nivel de chat router)

Hallazgo: la carpeta de motores (hash de árbol 4951574898a81f0bd51a57ae99fa31c48b1d1e65) existe 3 veces idéntica: en `chat router/`, dentro de `➡️📂 Wordflow LOOP Yaiwes/` y dentro de la raíz del Wordflow (por tanto también dentro de la nueva).

## H-05 Comparación de la carpeta duplicada
`➡️📂 Wordflow LOOP Yaiwes` contiene UN solo ítem: la carpeta de motores. Ese ítem ya está idéntico dentro de la raíz nueva. Faltan 0 archivos. No hay nada que copiar.

## H-02 Mapa de destino (propuesta)
⚠️ = necesita decisión del Director.

| Ítem | Dónde está hoy | Propuesta | Nota |
|---|---|---|---|
| Los 5 archivos sueltos | `chat router/` | ⚠️ Decidir | Hay dos órdenes del Director que chocan: (a) moverlos a `chat router/Workflow Loop code Yaiwes/01-PLAN/` y (b) dejar todo dentro de `📂 workflow Loops code Yaiwes`. ROOT-MAP-T11.yaml cita 3 de ellos en `chat router/` (raíces 04 y 05); si se mueven hay que actualizar ROOT-MAP en el mismo paso (H-06). El handoff del Devin dice NO EJECUTAR el plan de infraestructura y el orquestador (ya integrados en los nodos). |
| `wordflow loop code Yaiwes` (vieja) | `chat router/` | Se queda | No se borra hasta H-10 con permiso del Director |
| `➡️📂 Wordflow LOOP Yaiwes` | `chat router/` | Candidata a borrar en H-10 | Su único contenido ya está en la raíz nueva. ROOT-MAP raíz 11 la cita: actualizar si se borra |
| `➡️📂motores de descarga...` (nivel chat router) | `chat router/` | Candidata a borrar en H-10 | Duplicado idéntico. ROOT-MAP raíz 11 la cita: actualizar si se borra |
| Carpetas numeradas 00 a 13, chat_orders, deepseek-harness-chat, space, ui | `chat router/` | ⚠️ Se quedan donde están, salvo decisión | ROOT-MAP-T11 las cita en su lugar actual (por ejemplo 13-CHAT-UI-SUITE, ui, space, 04-MEMORIA, 05-AGENTES, 00-INSTRUCCIONES). Meterlas dentro de la raíz nueva rompería ROOT-MAP, el handoff y los comandos |
