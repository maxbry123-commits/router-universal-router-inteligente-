# 00-LEEME-PRIMERO — Índice, correcciones y estado consolidado (Claude notas)

> **COMMAND CENTER PERMANENTE:** antes de este archivo leer `../➡️ ➡️ 📂 osquestador comand Center.md`. Ese archivo contiene la cola viva, INPUT_BLOCK verbatim, objetivos, delegación y LOOP DSL DAG; este archivo conserva contexto/provenance.


Escrito 2026-09-18 (HEAD leído al escribir: `3e6fc2258c52dd23343bd5cf91dedead021d5504`, RIU-0100). Esto es una ADENDA a `memoria.md`: no lo reemplaza ni lo resume. Léelo primero; después `memoria.md`.

## 1. Orden de lectura para una cuenta nueva
1. Este archivo.
2. `CONSEJOS-CONTINUIDAD-Y-RECUPERACION.md` (método de continuidad, plantillas, checklists).
3. `../CLAUDE.md` → `../bitácora stated JSON Craxy wall plan checkpoint router inteligente universal/{STATE.json, CHECKPOINT.json, PLAN-TAREAS.md, RECOVERY-PATCH.md, BITACORA-CRAZY-WALL.md}` (leer la bitácora desde las últimas entradas).
4. `../Handoff router inteligente universal.md`.
5. `memoria.md` (secciones 0-11) y, si hace falta, `../Readme arquitectura router inteligente universal/GUIA-MAESTRA-EJECUCION-LOOP-SOL-ROUTER-INTELIGENTE-UNIVERSAL.md` (método LOOP).
6. Para el ecosistema completo: `agentes/Claude notas/` (solo lectura; ver sección 5).

## 2. Reglas del Director vigentes (verbatim/resumen fiel, registradas 2026-09-18)
- Este Claude es parte de un EQUIPO de cuentas de Claude. Cuando se acaba el plan de una cuenta se cambia a otra, que retoma con `Claude notas/` + Crazy Wall/bitácora/STATE/CHECKPOINT/Handoff.
- El ÚNICO repo de trabajo (escritura) es `router-universal-router-inteligente-`. Otros repos (`agentes`, etc.) solo lectura.
- Seguir el método y las instrucciones del Director "1 a 1" (input block literal) y anotar cada avance en el Crazy Wall / bitácora / STATE / Handoff.
- Autorización previa (P1-P4, RIU-0098): reparar en el camino sin escalar, resolver GAPs disponibles dentro del alcance, no declarar PASS sin evidencia.

## 3. CORRECCIONES a memoria.md (hechas al recuperar contexto; verificadas leyendo el repo)
1. `hf_scheduler.py` SÍ EXISTE y está probado. `memoria.md` §8.2 y §10.5 dicen que "falta implementar"; es obsoleto. Evidencia: `router inteligente universal/integration/huggingface/hf_scheduler.py` (blob `12f4a947b108734d5ac0723471b6eea762ac5832`), `tests/test_hf_scheduler.py`, RIU-0074 (commits `5514e395...` y `83a76366...`, HF Job `6aac7c9eb1dc2b62dc58faf9`, 5/5 rondas, 7 passed cada una). Alcance: solo selección lógica HF1→HF2→HF3→WAITING (umbral RAM 95 %); el envío de Jobs sigue en `hf_jobs_compute.py`.
2. `red/identity_pool.py` SÍ EXISTE (RIU-0079): pool de identidades con referencias `secret_env`, selección por prioridad → mirror rank → id, failover por cuota/cooldown, registro atómico. Test `tests/test_identity_pool.py`, commit `7ec0a58b...`, HF Job `6aac7f48b1dc2b62dc58fb73`, 5/5, incluye rollover de 64 identidades. `memoria.md` no lo mencionaba.
3. `GAP_ADAPTER_REGISTRY_SCHEMA`: el código YA lo repara (RIU-0098): `huggingface_openai_chat.py::allowed_model_ids()` lee `runtime_inference_verified_model_ids`; `provider_live_model_ids()` expone REMOTE20 sin habilitarlo para chat. Estado correcto: `CODE_FIXED_TEST_WRITTEN_EXECUTION_PENDING`. `Handoff` (dice `OPEN`) y `CHECKPOINT` (`HF_ADAPTER_REGISTRY_SCHEMA_RECONCILED=false`) están desfasados.
4. En mi primer mensaje al Director de esta recuperación listé "escribir hf_scheduler.py" como pendiente: ERA UN ERROR mío por fiarme de memoria.md (ver punto 1).

## 4. Estado consolidado (fresco, 2026-09-18)
### 4.1 Desfase documental (GAP `DOC_STATE_PLAN_CHECKPOINT_HANDOFF_SYNC`, abierto)
| Documento | Nodo en que está |
|---|---|
| BITACORA-CRAZY-WALL.md | RIU-0100 (al día, tras esta sesión RIU-0101) |
| Claude notas/memoria.md | §11 (2026-09-18) |
| CHECKPOINT.json | RIU-0097 |
| Handoff | RIU-0093 + bloque RIU-0094 |
| PLAN-TAREAS.md | RIU-0089 |
| STATE.json | RIU-0086 (con gates legacy mirror/download activos) |
| README arquitectura | hasta RIU-0094 |
| Readme Índice componentes | FAST-CLOSE RIU-0058 |
Otra contradicción: CLAUDE.md y la bitácora dicen `tel.workflow/v3`; GUIA-MAESTRA dice `tel.workflow/v4` (`GAP-CONTRACT-VERSION-V3-V4-001`, requiere decisión del Director).

### 4.2 Qué significa realmente "VERIFIED_CLOSED 100 %"
Es SOLO el alcance histórico P01/P02/P03: hot-path `FastAPI → APIKeyGuard → Enchufe Gate → RedUniversal → GitHub public adapter → GitHub API → verifier → response` (Actions run `34582284615`, `2 passed`), API Key Manager (100 slots), Connectivity Fabric 19/19, suite 75/75, fail-closed. `global_closed=false`. En `Readme Índice componentes.md` casi todos los C01-C23 fuera de ese hot-path están como "GAP no bloqueante". Nota: `readme Handoff indice componentes.md` aún marca C10 como MISSING mientras la arquitectura lo da por verificado (RIU-0031, `5 passed`).

### 4.3 Runtime canónico (`router inteligente universal/`) — lo que existe
- `red/`: `enchufe_gate.py`, `red_universal.py` (dueño único del routing), `conectores.py`, `connector_registry.py`, `identity_pool.py`, `conector_gitlab.py`, `conector_mcp_app.py`.
- `integration/`: `connectivity_runtime.py`, `verify_runtime_connectivity.py`, `audits/` (C01, C03, C10-C13, R004), `huggingface/` (`hf_jobs_compute.py`, `hf_scheduler.py`, `huggingface_openai_chat.py`, `model_registry.json` V13, `router_hot_path.py`, `fastapi_gateway.py`, `api_key_auth.py`, `hf_skills_registry.json` y auditorías RIU-0030…0044).
- `tests/`: 20 archivos (conectores v6, enchufe gate v1.5/v2, schema v2, validator, red universal, resilience C10, connectivity runtime, hot path HF, hf_scheduler, identity_pool, registry HF, fast-close E2E).
- También: `adapters/`, `domain/`, `enchufe/`, `engine/`, `gateway/`, `security/`, `verifier/`, y el pool donor `Componente open soure router inteligente universal/` (62 carpetas vendor + submodule OmniRoute; presencia ≠ integración).
- Raíces del repo: 28 contabilizadas en RIU-0071 + `.gitmodules` (submodule OmniRoute, RIU-0083) + `Claude notas/` (RIU-0098) = 30 entradas hoy.

### 4.4 Hugging Face
- Contrato `REMOTE_INFERENCE_ONLY`: `RedUniversal → connector_registry → HF adapter/InferenceClient → Provider/Endpoint remoto → model_id`. Sin pesos propios (0 repos de modelos, 0 mirrors, 0 instalaciones persistentes).
- REMOTE20 V2: 20/20 con provider live (Job `6aad981352d0dbd7f1d6b827`); 0/20 inferencia autenticada (403). Causa: credencial `COMAND-CENTER-1` sin scope Inference Providers ni escritura de repo → `GAP-EXTERNAL-CREDENTIAL-SCOPE-001` (acción del Director).
- Inferencia real histórica (en HF Jobs, efímera): Qwen3-0.6B, gpt2, Qwen3-8B (son los 3 de `runtime_inference_verified_model_ids`).
- Video/imagen (Wan2.2 Animate, LTX-Video, HunyuanVideo, Kandinsky 5, Qwen-Image, FLUX.1-schnell, TimesFM): `GAP_PENDING`.

### 4.5 GAPs abiertos (lista de trabajo)
`GAP-TEST-EXECUTION-001` (correr test del registry en runner real) · `GAP-EXTERNAL-CREDENTIAL-SCOPE-001` · `GAP-REMOTE20-REJECTED-IDS-CONFIRM-001` · `GAP-KAT-CODER-2.5-RESEARCH-001` · `GAP-UI-FICHAS-DESIGN-BUILD-001` · `GAP-CONTRACT-VERSION-V3-V4-001` · `GAP_DESTINATION_INPUT` (motor de descarga/extracción y reemplazo del Scheduled Job suspendido) · OmniRoute/AnyDoc/Orca/Omarchy sin runtime probado · MCP OAuth remoto E2E, memoria E2E, GLOBAL_E2E · `FULL_COMPONENT_CONTAINER_XRAY` y `DEDUP_ORPHAN_RECONCILIATION` · auditoría forense pasadas 3 y 4 · sincronización documental (4.1).

### 4.6 Próximo delta seguro (heredado, reafirmado)
`STATE_RECONCILIATION → CRAZY_WALL_SYNC → PLAN_SYNC → CHECKPOINT_SYNC → HANDOFF_SYNC → GAP-TEST-EXECUTION-001 → HF_REMOTE_MODEL_GATES (bloqueado por credencial) → EXTERNAL_COMPONENT_RUNTIME → AUTH_MCP_MEMORY → GLOBAL_E2E → FINAL_DOC_SYNC`. (`HF_SCHEDULER_IMPLEMENTATION` ya NO va en la lista: existe.)

## 5. Contexto del ecosistema (leído en `agentes/Claude notas/`, solo lectura)
- 7 proyectos: Agente Yaiwes (`agentes`), Osquestador Maxbry (`Orquestador-Maxbry-`), Router Inteligente Universal (este repo), UI Yaiwes (`nct-hub`, hipótesis), Fábrica de UI (`frontend`), Osquestador auditor + memoria (`osquestador-auditor`), NCT (`nct-core`).
- Jerarquía (CORRECCION-jerarquia-Wordflow): Yaiwes → NCT (Neuronas Code Turbo) → Wordflow Loop Code Yaiwes (motor de programación, ~95 % de Fables, KERNEL/orquestador único) → Seals Team (worker podado: `SealsExecutor.execute(NodeInput) → ToolReceipt → Evidence[] → NodeResult`).
- Estado en `agentes` (2026-09-18): Seals Team, Salidas 1-7 cerradas; pendiente Salida 8 (P1-27, P1-28, P2-31 y verificar el REQUISITO de 50 mundos). Pendiente crítico: CheckpointManager en memoria (no sobrevive a un crash), routers duplicados (`agent_router.py` vs `AgentFleetAdapter`), recovery tipado.
- REQUISITO-50-mundos: 50+ wordflows, cada uno con su mundo propio (Readme/memoria, Handoff, Crazy Wall, system prompt), mismo código base, distinto `worker_id`/task/workspace. Cerebras (6 keys) es SOLO para pruebas; en producción todos consumen API keys de ESTE Router. `router_modelos.py` y `consultor_experto.py` de `agentes` deben quedar con un adapter hacia el Router (tarea pendiente cuando el Router esté activo).
- CRITICO-3-carpetas: en `agentes` hay 3 carpetas casi idénticas ("wordflow loop code Yaiwes" con emoji = kernel real; "Wordflow loop code Yaiwes" sin emoji = proyecto ajeno tipo big-AGI; "Skills agente/"). Decisión del Director pendiente; no se ejecuta nada sin aprobación.
- DECISION-objetivo-osquestador: el Director decide el objetivo; quien opera el "joystick" es Yaiwes. Orca se estudia y se extrae su lógica hacia `agent_fleet_adapter.py` o `comandante_tactico_seal.py`; no se instala como componente.
- Método del otro Claude (PARCHE-RECUPERACION-MAESTRO): un paso por salida, micro-mundos, contrato de nodo máx. 3 pasos, "read fresh", solo FREE, REUSE primero, COPY-FIRST, nunca resumir, no PASS sin evidencia, MCP comparte CONTEXTO nunca AUTORIDAD.

## 6. Cobertura de lectura de esta recuperación (honesta)
Leído completo en esta sesión: CLAUDE.md, memoria.md (Router), BITACORA-CRAZY-WALL.md, STATE.json, CHECKPOINT.json, PLAN-TAREAS.md, RECOVERY-PATCH.md, Handoff, README arquitectura, GUIA-MAESTRA, Wordflow LOOP/README, Readme Índice componentes, readme Handoff índice componentes, `hf_scheduler.py`, `huggingface_openai_chat.py`, y de `agentes`: memoria.md, LISTA-TRABAJO-4-FRENTES, REQUISITO-50-mundos, CRITICO-3-carpetas, CORRECCION-jerarquia, DECISION-objetivo, PARCHE-RECUPERACION-MAESTRO-1de3. Árboles de carpeta listados: raíz, runtime `red/`, `integration/`, `tests/`.
Conocido solo por los resúmenes de memoria.md (no releído archivo por archivo): los 15 informes de `forensics/` (RIU-0071…0096, AUTH-REPAIR).
NO leído: los ~62 donors vendor, `Documentos proyectos router inteligente universal/` (75 entradas: DOC-A00…A06, CHAT-B01…B11, PIPELINE.md, ROUTING_CONTRACT.md, diseño de UI, etc.), `dataset Yaiwes/`, `Yaiwes Cognitive Control Plane/`, `conectividad con Router inteligente universal/`, `coneccion huggueface Github/`, `router inteligente software/`, VERBATIM-01…06B de `agentes`, y el código de `red/*.py`, `security/`, `verifier/`, `gateway/`, `engine/`, `adapters/`, `domain/`, `enchufe/`. Esa lectura corresponde a las pasadas forenses 3 y 4.


## NOTA DE INTEGRACIÓN — DATASET MYTHOS / YAIWES — 2026-09-21

**Estado de origen:** dataset canónico V3 cerrado en `dataset Yaiwes/`: **107 métodos / 1.139 registros**, tiers A/B/C, almacenamiento `segmented_jsonl` e índice autoritativo `dataset Yaiwes/indexes/shard_index.json`. Evidencia registrada en `dataset Yaiwes/CRAZY-WALL-DATASET-YAIWES-V3.json`: runner externo exact-SHA, **24/24 tests PASS**, plugin en `PASS_SHADOW_READY` y no activo en producción por diseño.

### Diseño resumido
`INPUT Router Universal -> clasificación/selección -> registry.json -> shard_index.json -> lectura SOLO del rango del método -> registros Mythos/YAIWES/Meta/Cognitive Control -> Context Composer -> kernel/modelo/agente -> verificación -> salida`.

Regla arquitectónica: **nunca cargar el dataset completo al LLM**. El Router consulta primero `registry.json`, después `shard_index.json` y recupera únicamente `start_line + count` del método seleccionado. Los cuatro JSONL seed históricos están `SUPERSEDED_NOT_ROUTED`.

### Componentes a integrar
- Contenido: `dataset Yaiwes/data/shards/`.
- Registro maestro: `dataset Yaiwes/registry.json`.
- Índice canónico: `dataset Yaiwes/indexes/shard_index.json`.
- Reglas/adapters: `dataset Yaiwes/filters/rules.yaml` + `dataset Yaiwes/adapters/adapters.yaml`.
- Mecanismo: `Yaiwes Cognitive Control Plane/` con Source of Truth, Context Composer, Consistency Engine, Router y Policy Guard.
- Adapter final: `dataset Yaiwes/plugin/yaiwes_dataset_plugin.py`, **read-only / shadow-ready**.

### Método de integración al Router Inteligente Universal
1. Conectar el hot-path del Router a una interfaz de consulta read-only del dataset; no duplicar shards ni crear un segundo router propietario.
2. Entregar query/intención al selector; resolver método(s) y tier en registry; recuperar sólo rangos indexados; construir ContextPack con presupuesto y deduplicación.
3. Mantener fail-closed: Source of Truth + Consistency Engine resuelven evidencia/conflictos; Policy Guard decide permisos antes de cualquier efecto. Input Shark continúa upstream externo, `fusion:false`.

### Hardening antes de declarar integración runtime PASS
- Reconciliar `indexes/methods.json` y documentación antigua con `shard_index.json`/segmented JSONL.
- Hacer que el Router aproveche los 107 métodos y consuma `adapters.yaml` + `rules.yaml`, evitando drift de configuración.
- Unificar el verificador para dataset + Control Plane + plugin y conservar evidencia exact-SHA.
- No activar el plugin en producción hasta cumplir su governance gate (aprobación + ficha firmada). **Presencia/shadow PASS no equivale a integración runtime del Router Universal.**

**Objetivo:** usar Mythos/YAIWES como capa externa de conocimiento y control cognitivo del Router Inteligente Universal, conservando a `RedUniversal`/hot-path existente como dueño del routing y al dataset como retrieval selectivo, no como router paralelo.
