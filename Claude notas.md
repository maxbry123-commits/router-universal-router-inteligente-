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

Estado: stop para preguntas. Nada más se ejecuta hasta respuesta del owner.

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

Estado: stop para preguntas del owner. Ninguna tarea ejecutada en esta vuelta; no hay tareas completadas que borrar.
