# Claude notas.md — Tareas pendientes y reglas de trabajo

## Tareas pendientes (1 a 1, del input block verbatim)

- T01 Auditar notas de agentes en el repo; dejar solo codigo, README, handoffs y cableado.
- T02 Skill unificado de frontend FROMTED x YAIWES, con revision del chat.
- T03 Organizar raices y motores de descarga, extraccion, busqueda, copiar y mover.
- T04 Verificar componentes open source sueltos y enviarlos a Componentes/.
- T05 Mover agentes a Agentes/.
- T06 Mover almacenamiento y memoria a Memoria/ y luego a memoria/, con centinela de conteos.
- T07 Recablear con el Satelite Central.
- T08 Listar componentes de memoria y almacenamiento conectados al harness DeepSeek.
- T09 Dar la URL de origen de cada componente y los enlaces a los motores de descarga y extraccion.
- T10 Limpiar Claude notas.md e input_block_verbatim.yaml, dejando reglas y referencias de metodo.
- T11 Confirmar fe57c122ed en main (limpieza de Claude notas.md subida sin autorizacion registrada).

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
- S-6 Para tareas del owner no se usa disco del contenedor ni sandbox: solo API de GitHub.

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
