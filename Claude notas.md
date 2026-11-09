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

Estado: lista de Router 2 cerrada. Todo verificado con pruebas. Rama `ccr-42f0e753-ni96xs`.

| Tarea | Estado | Evidencia |
|---|---|---|
| Auditoría 4 pasadas | ✅ | Inventario, lectura de código, cableado (pasada 3), secretos (pasada 4) |
| Clasificación | ✅ | Tabla final abajo |
| Fusionar duplicados s1/s2/s3 | ✅ | `swe-code-models/manager.py`. `diff` contra la fuente: s1 vs s2 y s1 vs s3 difieren solo en el default de `PRIMARY` y un comentario |
| Copia de código | ✅ | Commits abajo |
| Rama de arranque | ✅ | `_quarantine/boot.sh` con `GITHUB_BRANCH`. Arranque real: `riu-router/entrypoint.sh`, que ya usa `ccr-f01c3de9-bmry0s` |
| T-J Crazy wall Router 2 y plan HF | ✅ | Esta sección |
| Checklist §6 auditoría forense | ✅ | Esta sección. `Claude.md` no se edita: es compartido |

### Commits (rama `ccr-42f0e753-ni96xs`)

`6922765` · `de49e5b` · `a9cab4d` · `3992231` · `fd8e680` · `cfe557a` · `f6d865c` · `1f52588` · `881dd8c` (cuentas.js mínimo sin rotación)

### Pruebas (todas pasan)

- Python: `py_compile` OK en `manager.py`, `fetch_models.py`, `_quarantine/scaler.py`.
- JSON: `swecode_provider.json` y `package.json` OK.
- Shell: `bash -n` OK en `_quarantine/boot.sh`.
- Node: `node --check` OK en los 7 archivos de `swe-code-web/src/` y en `cuentas.js`.
- Enlace de módulos de `swe-code-web` (con `playwright` y `express` simulados): PASS. Verifica `partir`, `cabecera`, `modoValido`, `preambulo`, `cuentaActual` (sin rotación), `rotar` (no cambia la cuenta), `clave`.

### Pasada 3 — cableado

- Las 109 rutas referenciadas en `connections/registry.yaml`, `endpoints.yaml` y `healthchecks.yaml` existen en `main`.
- Discrepancia real: C-011 apunta a `router-mvp/router/boot.sh`, pero el Space ejecuta `riu-router/entrypoint.sh` (auto-pull de `ccr-f01c3de9-bmry0s`).
- Discrepancia real: `huggingface_mirror` dice push por git; el código hace auto-pull en arranque. Corrección del registro pendiente (satélite).

### Pasada 4 — secretos

- Escaneo de patrones (GitHub, HF, NVIDIA, OpenAI-like, AWS, PEM, Slack, Google) sobre los 14 archivos de la rama y sobre todo el contenido de Hugging Face leído: 0 coincidencias.
- Sin valores literales de variables de secreto.
- A revisar (no es clave): `hf-bucket-mcp/auth.py`, default `dev-change-me` para `FASTMCP_JWT_SIGNING_KEY`.

### Clasificación final

| Elemento | Destino |
|---|---|
| GGUF, LoRA, bucket | Se queda en HF |
| `Dockerfile`, `README`, `entrypoint.sh` de cada Space | Se queda en HF |
| `manager.py` | `HUGGUEFACE SPACE/swe-code-models/` (única copia) |
| `fetch_models.py` | `HUGGUEFACE SPACE/swe-code-models/` |
| `scaler.py`, `boot.sh` | `HUGGUEFACE SPACE/_quarantine/` |
| `swecode_provider.json` | `HUGGUEFACE SPACE/riu-router/` |
| `proxy.py` | Retirado (router LLM en `llm system HF/`) |
| `swe-code-web/src/*` | `HUGGUEFACE SPACE/swe-code-web/src/` (`cuentas.js` mínimo sin rotación) |
| `openclaw.sh`, `door.py`, `mini.py`, `fleet.py`, `app.py`, `hf-bucket-mcp/*` | Satélite de comunicación. No se copian |

### Decisiones de Router 2

- `cuentas.js`: no se copia la rotación. Se sube un stub con la misma API y una sola cuenta. `browser.js` carga.
- `app.py` (MCP con `delete_repository`): no se modifica. Es cableado de Router 1 / owner. Riesgo registrado.
- Atribución: los commits nuevos llevan el trailer. `6922765` y `9d4edd3` no; no se reescribe historial.

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

### Handoff Router 2 (JSON)

```json
{"router":"ROUTER 2","branch":"ccr-42f0e753-ni96xs","estado":"cerrado",
 "commits":["6922765","de49e5b","a9cab4d","3992231","fd8e680","cfe557a","f6d865c","1f52588","881dd8c"],
 "pruebas":"py_compile, json, bash -n, node --check, enlace de modulos: PASS",
 "borrados_hf":"ninguno; lista para MiniMax tras auditoria del owner",
 "flags_owner":["S2","S3","D2","D3","REG","DEP"]}
```

## Bitácora

- 2026-11-09 — Creado `Claude.md` con la checklist del input block verbatim y las tareas heredadas.
- 2026-11-09 — Creado `Claude notas.md` y reparto Router 1 / Router 2.
- 2026-11-09 — Router 2: rama `ccr-42f0e753-ni96xs` creada desde `main` (`5e239762526`). Inventario de 10 Spaces.
- 2026-11-09 — Router 2: cierre con pruebas. Pasadas 3 y 4 verificadas. Lista de borrados para MiniMax (no ejecutada).

## Router 1 — progreso (2026-11-09)

| Tarea | Estado | Evidencia |
|---|---|---|
| Motor de gaps con buscar_web | ✅ | d6fbfd63fb, tests/test_gap_web.py |
| Chat A/B como tools nativas | ✅ | 6a76a9b8b8, tests/test_workflow_tools.py (4 pruebas) |
| Router LLM unificado en llm system HF | ✅ copia | c214932c54, llm_router/ (import y 401/200 verificados) |
| Retiro del proxy original en MVP v1 | 🚩 | Requiere aprobación del owner |
| Diagnóstico NVIDIA 410 | 🚩 | Requiere llave NVIDIA en entorno |
| Motor de descarga | ⬜ no autorizado | Fase 2 |

Router 1 no toca `HUGGUEFACE SPACE/` ni los Spaces. Router 2 mantiene su alcance.

## Decisiones de Router 1 sobre los flags de Router 2 (2026-11-09)

- D1 manager.py: única copia. Default de `PRIMARY_MODEL` unificado a `qwen2.5-coder-0.5b`. Router 2 lo copia en `HUGGUEFACE SPACE/swe-code-models/`. Cada Space conserva su variable de entorno.
- L1 límite de 200 LOC: excepción documentada para `manager.py`. No se parte sin pruebas. Se revisa cuando exista prueba en Router 1.
- C1 cuentas web: NO se copia a GitHub. Se queda en el Space `swe-code-web` y se registra en el satélite como cableado sensible. No se mueven credenciales.
- S1 MCP público `app.py`: NO se copia. Es cableado de comunicación: va al satélite como registro de riesgo. Router 1 propone bloquear `delete_repository` en el satélite (decisión del owner solo si quiere eliminar la función).
- R1 proxy: NO se duplica en `HUGGUEFACE SPACE/`. Router 1 ya tiene el router LLM en `llm system HF/llm_router/` (commit c214932c54). Router 2 borra de su plan la copia del proxy.
- B1 boot.sh: verificado. `entrypoint.sh` no invoca `boot.sh`. Va a `_quarantine/` con README.
- X1: `manager.py` en commit propio. Acepto.

## Router 1 — siguiente

- T-A a T-J según `Claude.md` §8. Empieza por T-A (búsqueda de Rufo y Rowbot).

## Router 1 — loop (2026-11-09, segunda vuelta)

| Tarea | Estado | Evidencia |
|---|---|---|
| T-A Rufo / Rowbot | ✅ búsqueda hecha, no encontrados | GitHub público (search) y ls-remote de la cuenta owner |
| T-B Hermes / OpenClaw / Cline | ✅ | 39fa94257a (agentes.py), b836d6c1d2 (Cline en componentes_descargados, 4452 archivos, 84 MB, fuera de git) |
| T-D Motor de descarga | ✅ | b836d6c1d2: solo descarga, nunca ejecuta; hosts permitidos; límite 200 MB; zip/tar con control de rutas |
| T-E Búsqueda dual | 🟡 | motor_descarga.buscar_github / buscar_huggingface; faltan 10 métodos por fuente y búsqueda por URL |
| T-G Raíz de tools | ✅ | 02fb25bcc5 (tools/__init__.py, 9 tools registradas) |
| T-F, T-H, T-I | ⬜ | pendientes |

Pruebas locales: 15 pasan en `ROUTER MVP v1/system_prompt_py/tests` y `llm system HF/llm_router`.

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

Estado: sin cambios de carpeta todavía. Pendiente de respuesta del owner (ver preguntas).

## Gaps y decisiones pendientes (Router 1, 2026-11-09)

- G-1 Búsqueda Rufo/Rotboat en todas las ramas: pendiente.
- G-2 Auditoría X-Ray de 3 pasadas: pendiente de ubicar o rehacer.
- G-3 Enchufe Fables: falta decidir cuál archivo Python es la base.
- G-4 Modo de integración automática: falta decidir PR con auto-merge o push directo.
- G-5 Sandbox de skills: falta elegir entre sandbox propio y el de cada agente.
- G-6 Frontend: falta aprobar el enfoque de iframe por ventana.

Estado: loop activo. Dudas en lista final 🚩.

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

Estado: loop activo. Dudas en lista final 🚩.

## Vuelta 5 — estado (2026-11-09)

Prioridad 1: cerrar Router 1 (ROUTER MVP v1, llm system HF/llm_router) y Router 2 (HUGGUEFACE SPACE/) al 100 % PASS en sandbox. Después: DeepSeek audita, y solo al decir "cerrado" se entrega la limpieza de Hugging Face para MiniMax.

Prioridad 2: chat, agentes, frontend, almacenamiento y memoria cableados.

Pendientes del owner en esta vuelta: P-1 a P-9 (ver Claude.md §13).

🚩 Dudas abiertas: (1) skill "Maxbry UI frontend" no aparece en mi lista de skills; (2) pruebas en vivo sin llaves ni red; (3) sub-agentes: dónde se registran si generan ruido.

Estado: loop activo. Dudas en lista final 🚩.


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
