# Organización de raíces y motores de descarga/extracción

Fecha: 2026-11-11. Rama: `ccr-f01c3de9-bmry0s`. Documento de inventario y plan. No mueve ni renombra nada.

## 0. Resumen y hallazgos que cambian el encargo

| # | Premisa del encargo | Estado real (verificado) |
|---|---|---|
| H1 | Existe `external/tools/download_manager.py` con `DownloadManager` | **NO EXISTE.** No hay carpeta `external/` ni archivo `download_manager.py` en disco ni en git (`git ls-files`, `find`). |
| H2 | Hay que crear `external/motores/` con cuatro módulos | **NO SE CREA.** Los cuatro motores ya existen repartidos en `plugins/motores/` y `plugins/motores-descarga/` (sección 2). Crear `external/motores/` duplicaría código. |
| H3 | `componentes/` tiene 71 carpetas | `ls` muestra **69 entradas**. El 71 corresponde al contador de enlaces del directorio (2 + 69), no al número de carpetas. |
| H4 | Adjunto `DESCARGAR.sh` | **NO ENCONTRADO** en el repo (ni `*DESCARGAR*` versionado ni en disco). Estado: UNKNOWN. No se ejecutó nada. |
| H5 | Carpeta "Main" | No existe carpeta `Main/`. Puede referirse a la rama `main` o a la raíz. Se asume la raíz del repo. Pendiente de confirmar con el owner. |
| H6 | Motor de descarga con `ENGINE_PATH` | Bug: `plugins/motores-descarga/motor_2_queue_download_extract.py` usa por defecto la ruta `➡️📂motor descarga y extracción con huggueface/hf_download_extract_engine.py`, que **no existe**. El motor real está en `plugins/motores-descarga/hf_download_extract_engine.py`. Hay que pasar `ENGINE_PATH` por entorno o corregir el default (no corregido aquí). |

Decisión sobre ruta de motores: **NO es nueva**. No se crea `external/motores/` ni esqueletos. Se propone una fachada en `plugins/motores/` solo si el owner la confirma (sección 3).

## 1. Árbol actual de raíces (nivel 1 y 2)

Verificado con `ls` y `git ls-files`. Rutas con espacios o emoji se citan tal cual existen.

| Raíz | Nivel 2 (verificado) | Propósito |
|---|---|---|
| `README.md` | — | Índice de planos y cableado (Data, Control, HF, Control HF). |
| `SYSTEM_WIRING_REGISTRY.yaml` | — | Registro de cableado del sistema. |
| `FUERA_DE_LISTAS_CONTINUIDAD.md`, `INSTRUCCIONES_ANTONIO.md`, `SKILL_ORQUESTADOR.md`, `LIVE_URL.json` | — | Notas de continuidad, instrucciones y URL viva. |
| `.gitignore` | — | Exclusiones (`__pycache__`, `componentes_descargados/`, `skills/` de ROUTER MVP). |
| `.checkpoints/` | `LEDGER.jsonl`, `STATE.json` (versionados) | Estado/registro de checkpoints. |
| `.pytest_cache/` | vacío, no versionado | Caché de pytest. Ignorar. |
| `Skills/` | `orquestador-jefe-chat-router/` | Skill del orquestador jefe del chat router. |
| `chat-router/` | `Loop cola wachdog/`, `agentes/`, `plan/` | Pantalla del chat, agentes externos (donors, rowboat, ruflo) y planes de evidencia. |
| `componentes/` | 69 entradas de terceros (p. ej. `Chart.js`, `LiteLLM`, `langgraph`, `llama_index`, `skills/`) | Código de terceros. No se toca (regla de `docs/README.md`). |
| `control huggueface/` | `bootstrap_spaces.py`, `control_api.py`, `hf_upload.sh`, `mirror_spaces.py`, `registry_models.py`, `sync_to_hf.py`, `trigger_wake.py` | Control externo del plano HF: pausa, reinicio, mirror, wake, registro. **No ejecutar `bootstrap_spaces.py --apply`** (escribe secretos en HF). |
| `docs/` | `ARQUITECTURA.md`, `HANDOFF.md`, `README.md`, `WATCHDOG_CHECKLIST.md`, `bitacora/`, `handoff/` | Documentación y handoffs. |
| `fichas/` | `fichas_qwen/`, `plugin_fichas/`, `sdk/`, `system-prompt/`, `sentinela.py` | Fichas del router, system-prompt y SDK. |
| `llm system HF/` | `Dockerfile`, `README.md`, `download_model.py`, `entrypoint.sh`, `manager.py`, `registry.json`, `scaler_ram.py`, `llm_router/` | Space de HF (docker): cascarón del LLM. `download_model.py` usa `hf_hub_download`. |
| `ops/` | `historical_wiring_audit.py` | Auditoría histórica de cableado. |
| `plugins/` | `agentes/`, `chat/`, `chat-router/`, `connectivity/`, `deepseek_harness/`, `hf_compute/`, `hf_datasets/`, `hf_skills/`, `hf_storage/`, `lifeguard/`, `llm_local_swe_code/`, `llm_nvidia_groq_qwen/`, `memoria/`, `motores/`, `motores-descarga/`, `orquestador/`, `parallel/`, `puente_chat/`, `ssh_bridge/`, `workflow-loop-yaiwes/`, `router_api_cliente.py` | Edificio 2: harness y plugins. `motores/` y `motores-descarga/` son los motores (sección 2). |
| `raiz_fichas_prompt/` | `README.md` | Investigación de fichas y prompt (solo README). |
| `raiz_router/` | `README.md` | Investigación del router mínimo (solo README). |
| `router/` | `adapters/`, `api/`, `banco/`, `cognitive_control_plane/`, `domain/`, `engine/`, `gateway/`, `security/`, `tests/`, `verifier/`, `riu_kernel.py`, etc. | Edificio 1: el router (api, gateway, engine, seguridad, banco). |
| `router_llm_hf/` | `queue_manager.py`, `mode_router.py`, `escalation_guard.py`, `watchdog.py`, `recall_engine.py`, `output_contract.py`, `tests/` | Plano de control (decide y controla, no computa). |
| `router_recovery/` | `checkpoint_store.py`, `dispatcher.py`, `runner.py`, `pydantic_models.py`, `dag_schema.yaml`, `input_block.yaml`, `tests/` | Ejecutor determinista de DAG con ledger. Sin LLM en el camino crítico. |
| `ROUTER MVP v1/` | `system_prompt_py/` | Plano de datos (ejecuta y almacena). `system_prompt_py/componentes_descargados/` está ignorado por git (0 archivos versionados). |

## 2. Motores existentes y mapeo a los cuatro módulos pedidos

Los cuatro módulos del encargo ya tienen equivalente. Las entradas se leen del código (variables de entorno y `argparse`), no de documentación.

### 2.1 Árbol real

```
plugins/motores/
  busqueda-contexto/        motor_1_web_domains.py, motor_2_github_search.py,
                            motor_3_huggingface_search.py, motor_4_research_prepass.py (223 líneas),
                            sources.json, context_packet.schema.json
  descarga-copia/
    ➡️📂 motor de búsqueda/  websearch_engine.py, research_prepass.py (479 líneas),
                            trigger_hf_websearch.py, source_registry.json, tests
    ➡️📂motor de copiar archivos/  motor_3_copy_batches.py, motor_copy_root_to_repo.py
    ➡️📂motor de moves archivos/   motor_4_move_batches.py
  motores-caso/             motor_openclaw_deref_symlinks.py
plugins/motores-descarga/
  hf_download_extract_engine.py   (descarga por git, bundle zip, partes <= 12 MiB, verificación SHA, publish opcional)
  motor_1_extract_only.py         (extracción por lotes desde zip, con guarda de rutas)
  motor_2_queue_download_extract.py (cola con reintentos que invoca el motor 1/hf)
```

### 2.2 Módulos propuestos

**buscar.py**
- Reutiliza: `plugins/motores/descarga-copia/➡️📂 motor de búsqueda/websearch_engine.py` (proveedores Brave, Tavily, Serper, Firecrawl por clave de entorno), `trigger_hf_websearch.py` (dispara un HF Job; no ejecutar), `busqueda-contexto/motor_1..4`.
- Entrada: consulta (`query`), lista de proveedores, límite por proveedor (`MAX_RESULTS_PER_PROVIDER`, por defecto 8), directorio de salida (`WEBSEARCH_OUTPUT_ROOT`). Para investigación previa: `research_prepass.py` con `--input-file`, `--plan-file`, `--registry`, `--budget-tokens`.
- Salida: paquete de contexto JSON según `context_packet.schema.json` (archivos en `WEBSEARCH_OUTPUT_ROOT`).
- Errores tipados: **NUEVO**. Ningún motor define excepciones propias. Propuesta: `BuscarError` con subtipos `ProveedorSinClave`, `ProveedorTimeout`, `ResultadoInvalido`.
- Estado: **REUTILIZAR** la lógica; la interfaz unificada es **NUEVA**.

**descargar.py**
- Reutiliza: `plugins/motores-descarga/hf_download_extract_engine.py` (adquisición por git con `SOURCE_REPO`/`SOURCE_REF`, verificación SHA-256 de árbol y blobs, partes de `PART_SIZE_MIB`=12, publicación solo con `PUBLISH=1`). Para modelos HF: `llm system HF/download_model.py` (`hf_hub_download`, con `MODEL_ID`/`MODEL_FILE`).
- `download_hf_model` y `download_github_folder` **NO EXISTEN** en el repo (búsqueda en git: solo aparece `snapshot_download` dentro de `chat-router/agentes/donors/smolagents`, que es código de terceros).
- Entrada: origen (repo git o `repo_id` de HF), ref, ruta de destino, token por entorno (`GITHUB_TOKEN`, `HF_TOKEN`; nunca en código).
- Salida: ruta local y manifiesto con SHA-256 verificado.
- Errores tipados: **NUEVO**. Propuesta: `DescargaError`, `IntegridadError` (SHA no coincide), `LicenciaPendienteError` (bloquea adjuntos sin licencia, ver sección 4).
- Estado: **REUTILIZAR** la lógica de `hf_download_extract_engine.py`; la clase `DownloadManager` es **NUEVA** (la anterior no existe).

**extraer.py**
- Reutiliza: `plugins/motores-descarga/motor_1_extract_only.py` (`safe_members`, `extract_one`, lotes con `BATCH_SIZE`, estado en `STATE_FILE`, límite `MAX_BATCHES`).
- Entrada: `ARCHIVE_INPUT` (zip), `DEST_DIR`.
- Salida: árbol extraído y estado persistido en JSON. Hash del árbol.
- Errores tipados: **NUEVO**. Propuesta: `ExtraccionError`, `RutaInsegura` (zip-slip), `ArchivoCorrupto`.
- Duplicado: `safe_extract` y `tree_hash` existen también en `hf_download_extract_engine.py`. Consolidar en un solo helper.
- Estado: **REUTILIZAR**.

**copiar_mover.py**
- Reutiliza: `motor_3_copy_batches.py` (copia por lotes), `motor_copy_root_to_repo.py` (raíz a repo, lotes de 2), `motor_4_move_batches.py` (mover por lotes). Variables: `SOURCE_DIR`, `DEST_DIR`, `COLLISION_POLICY` (por defecto `fail`), `BATCH_SIZE`, `MAX_BATCHES`.
- Entrada: origen, destino, política de colisión (`fail`, otras opciones según cada motor).
- Salida: estado por lote en `STATE_FILE`; sin borrado silencioso.
- Errores tipados: **NUEVO**. Propuesta: `ColisionError`, `DestinoNoVacio`, `OrigenInexistente`.
- Estado: **REUTILIZAR** los tres scripts; la unificación en un módulo es **NUEVA**.

### 2.3 Dónde colocar la fachada (decisión pendiente del owner)

- Opción A (recomendada): mantener los motores donde están y añadir una fachada `plugins/motores/fachada/` con los cuatro módulos (`buscar.py`, `descargar.py`, `extraer.py`, `copiar_mover.py`) que solo importan los motores existentes. No duplica código.
- Opción B: crear `external/motores/` como pide el encargo. No recomendada: `external/` no existe, y crearla crea una segunda copia de los mismos motores.
- Esta fachada **no se creó**, porque la ruta no es nueva y el encargo prohíbe duplicar.

## 3. Plan de movimientos (solo plan, no ejecutado)

Criterio: no mover nada que tenga importadores o referencias sin actualizarlas. Git tiene 0 archivos de `componentes_descargados/` versionados. El archivo versionado más grande fuera de `componentes/` pesa 12 MiB, por debajo del límite de 100 MB de GitHub, así que no hace falta LFS (prohibido).

| Candidato | Tamaño | Quién lo referencia | Decisión | Motivo |
|---|---|---|---|---|
| `chat-router/agentes/rowboat/_archives/rowboat.bundle.zip.part-0001`, `-0002`, `-0003` | 12 MiB, 12 MiB, 3.8 MiB | `chat-router/agentes/rowboat/DOWNLOAD_EXTRACT_MANIFEST.json` (nombres, tamaños y SHA-256) | **NO** | El manifiesto verifica las partes por nombre y ruta. Mover exige actualizar el manifiesto y revalidar SHA. |
| `chat-router/agentes/ruflo/ruflo_0001..0004.zip` | 8 MiB, 11.4 MiB, 11.4 MiB, 5.8 MiB | Solo referencias en `chat-router/agentes/ruflo/README.md` y `ruflo/README.md` (texto) | **NO** | Sin importador de código; mover no aporta nada y rompe la documentación. |
| `chat-router/agentes/rowboat/code/assets/readme-spaces/spaces-hero.gif` | 9.8 MiB | Sin referencias en git (búsqueda por nombre) | **NO** (sin referencias, pero es asset de terceros) | No hay motivo técnico. Está dentro de código vendorizado. |
| `chat-router/agentes/rowboat/code/apps/x/demo.gif` | 7.2 MiB | `rowboat/code/README.md` y `docs/readme/README.*.md` (rutas relativas) | **NO** | Rompe 7 READMEs si se mueve. |
| `chat-router/agentes/ruflo/ruflo-plugins.gif` | 5.3 MiB | `ruflo/README.md` (ruta relativa) | **NO** | Igual que el anterior. |
| `chat-router/agentes/ruflo/v3/@claude-flow/cli/assets/model-router/seed-router.krr.json` (+ `.high.json`) | 2.2 MiB (+1 MiB) | `ruflo/scripts/auto-retrain-router.mjs`, `refit-calibrator-from-production.mjs`, `train-bundled-krr.mjs` | **NO** | Lo leen scripts con ruta fija. |
| `chat-router/agentes/ruflo/ruflo/src/chat-ui/static/chatui/omni-welcome.gif` | 1.2 MiB | `Dockerfile` (COPY) y `welcome.js` | **NO** | Lo copia el Dockerfile. |
| `ROUTER MVP v1/system_prompt_py/componentes_descargados/**` (p. ej. `catalog.generated.ts` 4.4 MB) | varios | Ignorado por `.gitignore`, no versionado | **NO** | No entra en commits. Fuera de alcance. |
| `package-lock.json`, `pnpm-lock.yaml`, `bun.lock` | 0.9 a 1.2 MiB | Herramientas npm/pnpm/bun | **NO** | Mover rompe la instalación. |
| `router_recovery/__pycache__/` y `.pytest_cache/` | pequeño | No versionados | **NO** | Caché. |

Planes propuestos (no ejecutados):
- **P1.** Consolidar `plugins/motores-descarga/` dentro de `plugins/motores/` (p. ej. `plugins/motores/descarga-extraccion/`). Antes: corregir `ENGINE_PATH` (H6) y buscar referencias. En git solo aparece `docs/ARQUITECTURA.md` (texto). Riesgo bajo.
- **P2.** Renombrar las carpetas con emoji de `plugins/motores/descarga-copia/` a nombres ASCII. Riesgo medio: cualquier script o doc que use esas rutas se rompe. Requiere grep previo de cada ruta.
- **P3.** Partir archivos >200 líneas (ver sección 5), con splitter AST, sin mover carpetas.

## 4. Adjuntos del owner (inventario por nombre y tamaño)

Solo nombres y tamaños. No se abrió contenido de los binarios.

| Adjunto | Dónde está en el repo | Tamaño | Decisión |
|---|---|---|---|
| **Diseño YAIWES** (HTML/MD de frontend factory: `FROMTED-YAIWES-*`, `YAIWES-CRAZY-WALL*`, `RUI-YAIWES-*`, `ESPECIFICACION_VISUAL_PANEL_YAIWES_FROMTED.md`, `SKILL-MAESTRO-FROMTED-YAIWES-BORRADOR.md`, etc.) | `componentes/skills/workflow-loop-yaiwes/fromted-yaiwes-frontend-factory/` | 60 MB (carpeta `workflow-loop-yaiwes` completa) | Presente. Conservar. No se mueve. |
| Diseño YAIWES (frontend original) | `plugins/chat-router/frontend/yaiwes/` | 23 MB | Presente. Conservar. |
| Frontend YAIWES (puente) | `plugins/chat-router/frontend-yaiwes/`, `componentes/skills/frontend-yaiwes/` | 196 KB, 52 KB | Presente. Conservar. |
| Plugin del flujo YAIWES | `plugins/workflow-loop-yaiwes/` | 3.2 MB | Presente. Conservar. |
| Constitución YAIWES | `plugins/puente_chat/constitucion/CONSTITUCION-YAIWES.json` | 8 KB | Presente. Conservar. |
| **Rare UI** | `componentes/skills/workflow-loop-yaiwes/rare-ui/` (`LICENSE`, `registry.json`) | 20 KB | **PENDIENTE DE LICENCIA.** La licencia es "MIT + Commons Clause License Condition v1.0 + Attribution" (© 2026 Swami Malode). La Commons Clause restringe vender el software. No reutilizar en código de producto hasta que el owner confirme la autorización. |
| **DESCARGAR.sh** (`*-DESCARGAR.sh`) | No encontrado en el repo | — | **UNKNOWN.** Si el owner lo tiene, debe aportarlo por separado. No se ejecutó. Regla: no ejecutar scripts `*-DESCARGAR.sh`. |

## 5. Regla de tamaño (≤ 200 líneas, splitter AST)

Verificado con `wc -l` en los motores. Incumplen la regla:
- `plugins/motores/descarga-copia/➡️📂 motor de búsqueda/research_prepass.py`: 479 líneas.
- `plugins/motores/busqueda-contexto/motor_4_research_prepass.py`: 223 líneas.

Escaneo parcial: se revisaron solo los primeros 400 `.py` versionados fuera de `componentes/`, y los que tienen emoji en la ruta se revisaron aparte. Incumplen también, entre otros: `plugins/puente_chat/plugin.py` (3624), `fichas/fichas_qwen/plugin.py` (2679), `plugins/puente_chat/herramientas.py` (1067), `plugins/agentes/07-SENTINELAS/sentinela_orquestador.py` (773). Escaneo completo: **UNKNOWN** (pendiente).

## 6. Lo que quedó BLOCKED o UNKNOWN

- BLOCKED: `external/tools/download_manager.py` no existe. No se puede verificar la reutilización prometida.
- BLOCKED: decisión del owner sobre la ubicación de la fachada (opción A o B).
- BLOCKED: licencia de Rare UI (Commons Clause).
- UNKNOWN: contenido de `DESCARGAR.sh`; no está en el repo.
- UNKNOWN: escaneo completo de tamaños de archivos fuente.
- UNKNOWN: qué es exactamente "Main" (sección H5).
- Bug sin corregir: `ENGINE_PATH` por defecto en `motor_2_queue_download_extract.py` (H6).
- No se ejecutó ningún `*-DESCARGAR.sh`, ni `bootstrap_spaces.py --apply`, ni descarga de terceros, ni push.
