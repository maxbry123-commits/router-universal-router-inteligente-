# Claude notas.md — Pizarra compartida (limpia, 2026-11-11)

Fuente de tareas: `Claude.md` · Input block: `input_block_verbatim.yaml` · Solo reglas y referencias de metodo.

## Reglas de trabajo

Frontend
- F-1 Cambio de frontend: copiar la ventana actual, crear la nueva en paralelo, editar quirurgicamente solo con autorizacion de sandbox y "Ok" del owner, eliminar la vieja y anadir el sistema aislado.
- F-2 Siempre usar el skill "Maxbry UI frontend" (buscarlo en el repo y todas las ramas; si no existe, reportarlo).
- F-3 Cablear el skill al README de arquitectura y a esta pizarra.
- F-4 Entregar un HTML de cada ventana en sandbox para ver antes de integrar.
- F-5 Criterio de frontend obligatorio: lo que salga fuera del criterio es Gap y se resuelve o va a pendientes.
- F-6 Selector de 2 vias: modelo que razona y agente que ejecuta en una sola ventana, cero friccion; el modelo lo ve como tool interna.
- F-7 Frontend de chat en `chat-router/chat/frontend/` (grupo "Frontend chat").

Organizacion
- O-1 Raiz de trabajo: `chat-router/`, por grupo: Agentes, Componentes, Skills, Chatbot, Backend chat, Frontend chat, Motores de descarga y extraccion y otros, Tool plugins.
- O-2 En `main` solo puede existir un puente hacia esa ubicacion ("raiz falsa").
- O-3 Se mueve poco a poco, en cada toque, con handoff. No se mueve todo de golpe.
- O-4 Un archivo = una responsabilidad. Maximo 200 lineas.
- O-5 No crear archivos nuevos fuera de lo necesario; no duplicar carpetas.
- O-6 Enlaces del indice en README y handoff de cada raiz.

Auto pull e integracion
- A-1 Auto pull siempre en toda la raiz `chat-router/`.
- A-2 Integracion automatica obligatoria: test en sandbox, luego integracion del tool a la carpeta de tools, sin LLM salvo para razonar o escribir la conversion.
- A-3 Motor tipo plantilla: el modelo anota lo que quiere y el sistema corre solo.
- A-4 Ninguna integracion se fusiona sin sandbox y autorizacion final del owner.
- A-5 Escritura por rama de trabajo y PR. Nunca push directo a `main`, salvo los archivos de notas y plan que el owner autorizo.

Busqueda y escalado
- B-1 Antes de escalar: buscar como se hace y como se resuelve (research system, fuentes S01-S20, ruta de gaps).
- B-2 Busquedas de codigo con `gh api search` (permitido), lectura por la API de GitHub. No clonar salvo que haga falta.
- B-3 Busqueda en todas las ramas remotas y en todo el repo cuando el owner lo pide.

Modo de trabajo
- M-1 Modo Loop, bucle, cola, preline: avanzar hasta terminar todas las tareas. Sin parar, sin escalar, sin explicar de mas.
- M-2 Dudas: se resuelven con el input block y los planes. Si no se resuelven, flag y se listan al final, por inciso.
- M-3 Ninguna pregunta en medio del loop.
- M-4 Sub-agentes: maximo uno de revision por entrega; el de busqueda puede dividirse. Si generan ruido, su salida va a la seccion temporal de `Claude notas.md`.
- M-5 Revisor (sheriff, centinela, guardian, supervisor, juez) verifica contra el input block, no escribe codigo.

Notas y trazabilidad
- N-1 Un DSL DAG por tarea, un handoff JSON por tarea.
- N-2 Claude notas es la pizarra compartida. Lo cerrado se marca y se mueve a la seccion archivada.
- N-3 Cada punto del input block verbatim se anota 1 a 1 en `Claude.md`.
- N-4 README minimo por raiz, con enlace a su handoff.

Seguridad y entrega
- S-1 Claves y secretos: nunca en archivos, logs ni respuestas. Si una clave aparece en el chat, no se usa y se recomienda rotarla.
- S-2 Sin GitHub Actions, sin LFS en GitHub.
- S-3 Sin despliegue nuevo en Vercel ni en Hugging Face sin autorizacion expresa.
- S-4 Atribucion en cada commit: Co-Authored-By y Claude-Session.
- S-5 `main` queda limpio; los puentes van en Markdown.

Cierre
- C-1 Paso 1: cerrar Router 1 y Router 2 al 100 % en sandbox, lo que se pueda probar localmente. Lo que dependa de servicios externos queda como flag.
- C-2 DeepSeek audita. Al decir "cerrado", se entrega la limpieza de Hugging Face para MiniMax.
- C-3 Paso 2: chat, agentes, frontend, almacenamiento y memoria cableados.

Ejecucion (confirmadas por el owner)
- E-1 Lenguaje: solo Python para el codigo de computo, memoria y recuperacion.
- E-2 Reemplazar o fusionar. Si no se sabe fusionar, se deja lo que dio el owner. Lo sobrante se elimina.
- E-3 No escalar. Solo proponer mejoras del codigo recibido, siguiendo el DSL DAG.
- E-4 No inventar. Lo que el owner fijo no se cambia.
- E-5 Dudas: primero el input block verbatim; luego los motores de investigacion, via sub-agente.
- E-6 Ejecucion en loop. Tareas delegadas a sub-agentes con DSL DAG.
- E-7 Supervision: sheriff, guardian, centinela, supervisor y juez revisan a los sub-agentes contra el input block y los DSL DAG.
- E-8 Bloqueantes reales: flag al final de todo el loop, no antes.
- E-9 Frente de almacenamiento y memoria: PENDIENTE. No se ejecuta hasta que el owner lo indique.

## Metodos de trabajo de frontend

- Skill vigente: `Skills/fromted-yaiwes-frontend` (rama `ccr-f01c3de9-bmry0s`): https://github.com/maxbry123-commits/router-universal-router-inteligente-/tree/ccr-f01c3de9-bmry0s/Skills/fromted-yaiwes-frontend
- Handoff del skill: https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/ccr-f01c3de9-bmry0s/docs/handoff/SKILL_FRONTEND_FROMTED_YAIWES.md
- Skill "Maxbry UI frontend" (nuevo): PENDIENTE. Lo entrega el owner.

## Organizacion y motores

- Plan de raices y motores: https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/ccr-f01c3de9-bmry0s/docs/handoff/ORGANIZACION_RAICES_Y_MOTORES.md
- Motores de descarga, extraccion, busqueda, copiar y mover: PENDIENTE. Su codigo lo entrega el owner.

## Tareas en curso

Handoffs en https://github.com/maxbry123-commits/router-universal-router-inteligente-/tree/ccr-f01c3de9-bmry0s/docs/handoff

| Tarea | Estado | Handoff |
|---|---|---|
| T01 Auditar notas de agentes | Auditada; limpieza pendiente de confirmacion | T01_auditar_notas_agentes.md |
| T02 Skill frontend | Creado; revision del chat pendiente | T02_skill_frontend_fromted_yaiwes.md |
| T03 Raices y motores | Plan creado; motores pendientes | T03_organizar_raices_motores.md |
| T04 Componentes open source | Pendiente | T04_verificar_componentes_open_source.md |
| T05 Mover agentes | Pendiente | T05_mover_agentes.md |
| T06 Mover memoria | No completado (movimiento revertido) | T06_mover_memoria.md |
| T07 Recablear satelite | Pendiente; satelite por confirmar | T07_recablear_satelite_central.md |
| T08 Listar componentes del harness | Pendiente (depende de T06) | T08_listar_componentes_memoria_harness.md |
| T09 URLs de origen | Pendiente | T09_urls_origen_motores.md |
| T10 Limpiar notas e input block | Hecho en `main` | T10_limpiar_claude_notas_input_block.md |

## Pendiente del owner

- Skill "Maxbry UI frontend" nuevo.
- Codigo de los motores de descarga, extraccion, mover y copiar.
- Confirmar si el satelite es `connections/`.
