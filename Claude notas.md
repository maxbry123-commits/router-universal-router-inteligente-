# Claude notas.md — Pizarra de trabajo (Crazy Wall)

Estado: 2026-11-09 · Fuente de tareas: `Claude.md` · Verbatim: `kernel/INPUT_BLOCK_YAIWES_CABLEADO.md`

## Reparto de trabajo (para que no se pisen)

| Router | Responsable | Carpetas que toca |
|---|---|---|
| Router 1 | Claude Code (chat actual) | `ROUTER MVP v1/` y `llm system HF/` · rama `ccr-f01c3de9-bmry0s` |
| Router 2 | Claude Code ROUTER 2 | `HUGGUEFACE SPACE/` (código) y esta notas · rama `ccr-42f0e753-ni96xs` (creada desde `main`) |
| Compartido, solo lectura para los dos | — | `SATÉLITE CENTRAL CONECCION` (`connections/`), `_quarantine/`, `Claude.md`, esta notas |

Regla: Router 2 hace `git pull --rebase origin main` antes de cada push a `main`. Nunca escribe en `llm system HF/` ni en `ROUTER MVP v1/`.

## Router 2 — CIERRE (2026-11-09)

### Candidatos a borrado en Hugging Face — LISTA PARA MINIMAX, NO EJECUTADA

Ningún borrado se hizo. Solo después de la auditoría final del owner:

1. `riu-router/boot.sh`: código muerto. El Dockerfile ejecuta `entrypoint.sh`.
2. `riu-router/proxy.py`: no lo ejecuta `entrypoint.sh`. Solo lo invocaba `boot.sh`.
3. `swe-code-s1/manager.py`: no se ejecuta (el entrypoint de s1 corre `llm system HF/manager.py`).
4. NO candidatos todavía: `scaler.py` en s1/s2/s3 y `manager.py` en s2/s3. El Dockerfile de s2 y s3 los copia en la imagen; borrarlos rompe el build. Se retiran cuando el Space haga auto-pull de GitHub. Eso es cambio de despliegue, fuera del alcance de Router 2.

### Flags 🚩 finales

Abiertos para la auditoría del owner (no bloquean el cierre):
- 🚩S2 `dev-change-me` como clave JWT por defecto en `hf-bucket-mcp/auth.py`.
- 🚩S3 `hf-bucket-mcp` `write_file` sin lista de usuarios permitidos.
- 🚩D2 El plan HF menciona carpetas del dataset que no existen en `main`.
- 🚩D3 `door.py`: raíz `router-inteligente-universal`, distinta a la del repo.
- 🚩REG Registro `huggingface_mirror` describe push; el código hace auto-pull.
- 🚩DEP s2/s3 copian `manager.py` y `scaler.py` en la imagen. Pasar a auto-pull es despliegue.

Cerrados por decisión de Router 2: B1, D1, L1 (excepción documentada), R1, X1, C1 (stub sin rotación), S1 (no tocado, registrado).

## Router 1 — progreso (2026-11-09)

| Tarea | Estado | Evidencia |
|---|---|---|
| Retiro del proxy original en MVP v1 | 🚩 | Requiere aprobación del owner |
| Diagnóstico NVIDIA 410 | 🚩 | Requiere llave NVIDIA en entorno |
| Motor de descarga | ⬜ no autorizado | Fase 2 |

Router 1 no toca `HUGGUEFACE SPACE/` ni los Spaces. Router 2 mantiene su alcance.

## Router 1 — siguiente

- T-A a T-J según `Claude.md` §8. Empieza por T-A (búsqueda de Rufo y Rowbot).

## Router 1 — loop (2026-11-09, segunda vuelta)

| Tarea | Estado | Evidencia |
|---|---|---|
| T-E Búsqueda dual | 🟡 | motor_descarga.buscar_github / buscar_huggingface; faltan 10 métodos por fuente y búsqueda por URL |
| T-F, T-H, T-I | ⬜ | pendientes |

🚩 (para el final):
- 🚩 Rufo y Rowbot no existen en ninguna fuente. Pendiente de confirmación del owner: el nombre exacto o la URL.
- 🚩 Ejecutar skills descargadas (requiere aprobación al pasar de descargar a ejecutar).

## Organización de la raíz (copia de la instrucción del owner, 2026-11-09)

Destino en `chat-router/`, por grupo:
- 📂 Agentes
- 📂 Componentes
- 📂 Skills
- 📂 Chatbot
- 📂 Backend chat
- 📂 Frontend chat
- 📂 Motores de descarga y extracción y otros
- 📂 Tool plugins

En `main` puede existir una raíz falsa: un puente que apunta a esa ubicación. Se mueve poco a poco, en cada toque, sin mover todo de una vez.

## Gaps y decisiones pendientes (Router 1, 2026-11-09)

- G-1 Búsqueda Rufo/Rotboat en todas las ramas: pendiente.
- G-2 Auditoría X-Ray de 3 pasadas: pendiente de ubicar o rehacer.
- G-3 Enchufe Fables: falta decidir cuál archivo Python es la base.
- G-4 Modo de integración automática: falta decidir PR con auto-merge o push directo.
- G-5 Sandbox de skills: falta elegir entre sandbox propio y el de cada agente.
- G-6 Frontend: falta aprobar el enfoque de iframe por ventana.

## ALERTA (regla del owner, 2026-11-09)

Cambio de frontend, obligatorio:
1. Copiar el código de la ventana actual.
2. Crear la ventana nueva en paralelo.
3. Con autorización de sandbox, editar quirúrgicamente.
4. Eliminar la ventana vieja.
5. Añadir el sistema aislado de frontend.

Integración automática: auto pull siempre; ninguna integración se hace sin test de sandbox y autorización final del owner.

## Tareas pendientes del owner (2026-11-09)

- T-K Integrar descarga de componentes para tool.
- T-L Sistema para crear markdown (instrucción incompleta).
- T-M Catálogo de componentes UI (ver Claude.md §11).
- T-N Mejorar el selector de 2 vías.
- T-O Enrutadores de 100 entradas.

## Vuelta 5 — estado (2026-11-09)

Prioridad 1: cerrar Router 1 (ROUTER MVP v1, llm system HF/llm_router) y Router 2 (HUGGUEFACE SPACE/) al 100 % PASS en sandbox. Después: DeepSeek audita, y solo al decir "cerrado" se entrega la limpieza de Hugging Face para MiniMax.

Prioridad 2: chat, agentes, frontend, almacenamiento y memoria cableados.

Pendientes del owner en esta vuelta: P-1 a P-9 (ver Claude.md §13).

🚩 Dudas abiertas: (1) skill "Maxbry UI frontend" no aparece en mi lista de skills; (2) pruebas en vivo sin llaves ni red; (3) sub-agentes: dónde se registran si generan ruido.


## REGLAS DE TRABAJO (auditadas del chat y del input block, 2026-11-09)

Frontend
- F-1 Cambio de frontend: copiar la ventana actual, crear la nueva en paralelo, editar quirúrgicamente solo con autorización de sandbox y "Ok" del owner, eliminar la vieja y añadir el sistema aislado.
- F-2 Siempre usar el skill "Maxbry UI frontend" (buscarlo en el repo y todas las ramas; si no existe, reportarlo).
- F-3 Cablear el skill al README de arquitectura y a esta pizarra.
- F-4 Entregar un HTML de cada ventana en sandbox para ver antes de integrar.
- F-5 Criterio de frontend obligatorio: lo que salga fuera del criterio es Gap y se resuelve o va a pendientes.
- F-6 Selector de 2 vías: modelo que razona y agente que ejecuta en una sola ventana, cero fricción; el modelo lo ve como tool interna.
- F-7 Frontend de chat en `chat-router/chat/frontend/` (grupo "Frontend chat").

Organización
- O-1 Raíz de trabajo: `chat-router/`, por grupo: Agentes, Componentes, Skills, Chatbot, Backend chat, Frontend chat, Motores de descarga y extracción y otros, Tool plugins.
- O-2 En `main` solo puede existir un puente hacia esa ubicación ("raíz falsa").
- O-3 Se mueve poco a poco, en cada toque, con handoff. No se mueve todo de golpe.
- O-4 Un archivo = una responsabilidad. Máximo 200 líneas.
- O-5 No crear archivos nuevos fuera de lo necesario; no duplicar carpetas.
- O-6 Enlaces del índice en README y handoff de cada raíz.

Auto pull e integración
- A-1 Auto pull siempre en toda la raíz `chat-router/`.
- A-2 Integración automática obligatoria: test en sandbox, luego integración del tool a la carpeta de tools, sin LLM salvo para razonar o escribir la conversión.
- A-3 Motor tipo plantilla: el modelo anota lo que quiere y el sistema corre solo.
- A-4 Ninguna integración se fusiona sin sandbox y autorización final del owner.
- A-5 Escritura por rama de trabajo y PR. Nunca push directo a `main`, salvo los archivos de notas y plan que el owner autorizó.

Búsqueda y escalado
- B-1 Antes de escalar: buscar cómo se hace y cómo se resuelve (research system, fuentes S01–S20, ruta de gaps).
- B-2 Búsquedas de código con `gh api search` (permitido), lectura por la API de GitHub. No clonar salvo que haga falta.
- B-3 Búsqueda en todas las ramas remotas y en todo el repo cuando el owner lo pide.

Modo de trabajo
- M-1 Modo Loop, bucle, cola, preline: avanzar hasta terminar todas las tareas. Sin parar, sin escalar, sin explicar de más.
- M-2 Dudas: se resuelven con el input block y los planes. Si no se resuelven, flag 🚩 y se listan al final, por inciso.
- M-3 Ninguna pregunta en medio del loop.
- M-4 Sub-agentes: máximo uno de revisión por entrega; el de búsqueda puede dividirse. Si generan ruido, su salida va a la sección temporal de `Claude notas.md`.
- M-5 Revisor (sheriff, centinela, guardián, supervisor, juez) verifica contra el input block, no escribe código.

Notas y trazabilidad
- N-1 Un DSL DAG por tarea, un handoff JSON por tarea.
- N-2 Claude notas es la pizarra compartida. Lo cerrado se marca y se mueve a la sección archivada.
- N-3 Cada punto del input block verbatim se anota 1 a 1 en `Claude.md`.
- N-4 README mínimo por raíz, con enlace a su handoff.

Seguridad y entrega
- S-1 Claves y secretos: nunca en archivos, logs ni respuestas. Si una clave aparece en el chat, no se usa y se recomienda rotarla.
- S-2 Sin GitHub Actions, sin LFS en GitHub.
- S-3 Sin despliegue nuevo en Vercel ni en Hugging Face sin autorización expresa.
- S-4 Atribución en cada commit: Co-Authored-By y Claude-Session.
- S-5 `main` queda limpio; los puentes van en Markdown.

Cierre
- C-1 Paso 1: cerrar Router 1 y Router 2 al 100 % en sandbox, lo que se pueda probar localmente. Lo que dependa de servicios externos queda como 🚩.
- C-2 DeepSeek audita. Al decir "cerrado", se entrega la limpieza de Hugging Face para MiniMax.
- C-3 Paso 2: chat, agentes, frontend, almacenamiento y memoria cableados.

## RESPUESTAS DEL OWNER (2026-11-09)

- Rama: se desarrolla en la rama designada del sistema (`ccr-f01c3de9-bmry0s` para Router 1). Solo se escribe en `main` los archivos de notas y planes autorizados.
- Atribución: se usa la de la sesión actual, `session_01BK5y7GKUQ8CNDJSn8vc749`.
- Co-Authored-By: se mantiene como lo pidió el owner. 🚩 conflicto con la regla de sistema que prohíbe nombrar el modelo en commits; el owner decide.
- Modo: loop sin paradas hasta terminar. Los "stop" de esta pizarra quedan retirados.
- Nombres: buscar Rufo, Rowbot y Rotboat (el owner escribió las tres formas).
- Skill "Maxbry UI frontend": buscar en todo el repo. Si no existe, reportar.
- Búsqueda A1 y A2: sí, con `gh api search` y lectura por API.
- Carpetas: dentro de `chat-router/`, por grupo (O-1). `chat-router/plan/` es la única carpeta nueva por ahora.
- Clave: no se usa ni se guarda. Recomendado rotarla.
- NVIDIA 410 y pruebas en vivo: 🚩 hasta que haya llave en el entorno.
- T-L (sistema para crear a…): pendiente de aclarar por el owner; 🚩.

## RECEPCIÓN (2026-11-09) — propuesta externa "router_engine" (modo recepción, sin ejecutar)

Entrada recibida: propuesta de un nuevo paquete `router_engine/` (models, splitter AST, checkpoint JSONL, runtime, orchestrator) con 4 bloques de código y un DSL DAG.

Estado: NO integrado. Pendiente de decisión del owner.

🚩 Flags de la revisión:
- F-RE-1 Duplica piezas que ya existen: `workflow_tools.py`, `semantic_checkpoint.py`, `code_splitter.py`. Contradice la regla de reutilizar y no crear más archivos.
- F-RE-2 Nueva raíz `router_engine/` fuera de la organización R-4 (`chat-router/` por grupo).
- F-RE-3 Bug en `runtime.resume`: marca como completado un nodo en vuelo con `{"resumed": true}` sin ejecutarlo. Eso falsea el resultado tras un kill -9.
- F-RE-4 Bug en `checkpoint.append`: tras una línea corrupta no añade salto de línea; la siguiente escritura se pierde con ella. El comentario "truncar en el siguiente append" no está implementado.
- F-RE-5 El splitter usa `ast.unparse`: pierde comentarios y formato, y tras inyectar imports no vuelve a comprobar el límite de 200 LOC.
- F-RE-6 Las simulaciones son narrativas: no se ejecutaron. La simulación 4 (CONTRACT_FAILURE) no existe en el código.
- F-RE-7 Mezcla de fuentes: el "harness DeepSeek con JSONL atómico" citado es un tutorial externo, no el harness de este repo.
- F-RE-8 Referencias externas (AbstractRuntime, DagPipe, OpenArmature, cognivault, bernstein, semarun, pykomodo, Haystack): no verificadas en esta entrada.
- F-RE-9 "Ask Council AUTHORIZE" lo emite el propio documento. La decisión es del owner.
- F-RE-10 Restricción nueva no pedida por el owner: "máx. 25k caracteres por salida".
- F-RE-11 El planificador no reintenta cuando el JSON del LLM es inválido: `json.loads` lanza.

Recomendación de Router 1: reutilizar `workflow_tools` + `semantic_checkpoint` + `code_splitter`, corregir F-RE-3, F-RE-4 y F-RE-5 en esos archivos, y cablear el orquestador existente. No crear `router_engine/` sin decisión del owner.

Estado: stop para decisión del owner (recepción).


## Frente 5 — Almacenamiento y memoria (2026-11-09)

Anexo de cableado: `chat-router/plan/ANEXO_CABLEADO_ALMACENAMIENTO_MEMORIA.md`.
Estado: recepción. Lote recibido en R-01 a R-11 (ver anexo). 🚩 abiertos.
Bugs del lote: B1 a B5 (ver anexo, R-09). No ejecutar `router_engine/` ni `memory_repair.dag.yaml` sin decisión del owner.

## 📂 memoria/ — frente de almacenamiento y memoria (2026-11-09)

- Raíz: `Memoria/` (README.md, HANDOFF.md, ANEXO_INPUT_BLOCK.md).
- Estado: recepción. Anexo 1 a 1: F-01 a F-06. F-02 no leído.
- Preguntas de memoria: en `HANDOFF.md` §5 (6 preguntas).
- Frente Claude Code 4 para memoria: PENDIENTE.

## REGLAS DE EJECUCIÓN CONFIRMADAS POR EL OWNER (2026-11-09)

- E-1 Lenguaje: solo Python para el código de cómputo, memoria y recuperación.
- E-2 Reemplazar o fusionar. Si no se sabe fusionar, se deja lo que dio el owner. Lo sobrante se elimina.
- E-3 No escalar. Solo proponer mejoras del código recibido, siguiendo el DSL DAG.
- E-4 No inventar. Lo que el owner fijó (por ejemplo, un valor de 1.60) no se cambia.
- E-5 Dudas: primero el input block verbatim; luego los motores de investigación, vía sub-agente.
- E-6 Ejecución en loop. Tareas delegadas a sub-agentes con DSL DAG.
- E-7 Supervisión: sheriff, guardián, centinela, supervisor y juez revisan a los sub-agentes contra el input block y los DSL DAG.
- E-8 Bloqueantes reales: flag 🚩 al final de todo el loop, no antes.
- E-9 Frente de almacenamiento y memoria: PENDIENTE. No se ejecuta hasta que el owner lo indique.
