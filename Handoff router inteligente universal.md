# Handoff Router Inteligente Universal — ADN operativo

Contrato: `tel.workflow/v3` · `FAIL_CLOSED_LOOP` · repo `maxbry123-commits/router-universal-router-inteligente-` · branch `main`.

## Estado consolidado
El core conserva evidencia histórica `VERIFIED_CLOSED` para P01/P02/P03, Connectivity Fabric 19/19, suite 75/75 y fail-closed. Esto NO equivale a cierre global.

## Nodo vivo
`RIU-0093_AUTHORITATIVE_HANDOFF_CHECKPOINT_SYNC`.

## Arquitectura autoritativa
`RedUniversal` conserva ownership único de routing. AI Staff usa `REMOTE_INFERENCE_ONLY`:
`RedUniversal -> connector_registry -> HF adapter/InferenceClient -> Inference Provider/Endpoint remoto -> model_id`.

Gate por modelo:
`REGISTER -> REMOTE_PROVIDER_DISCOVERY -> AUTH_REFERENCE -> REMOTE_INFERENCE_SMOKE -> FAILURE_FALLBACK_TEST -> EVIDENCE -> READY`.

Los diseños históricos de mirror/download (`snapshot_download`, hash/load de pesos) se preservan como provenance, pero quedan SUPERSEDED para el camino normal de AI Staff. No declarar READY por catálogo, README, presencia de ID o carga efímera de un Job.

## W1 — X-Ray / owners / dedup
- Root fresh contabilizado: 28 entradas; inventario `forensics/RIU-0071-XRAY-COMPONENT-INVENTORY-2026-09-17.json`.
- Árbol recursivo global anterior fue truncado; `FULL_COMPONENT_CONTAINER_XRAY` sigue abierto.
- LiteLLM/litellm se preservan hasta demostrar equivalencia/provenance completa.
- Donor/legacy/orphan no adquiere ownership por presencia.

## W2 — componentes externos
- OmniRoute: downstream adapter detrás de `connector_registry`; materializado/pinneado, integración runtime pendiente.
- AnyDoc: document ingest adapter; multiformato/hash/error-path pendientes.
- Orca: ADE externo; boundary definido, runtime/verifier pendiente.
- Omarchy: host opcional; no dependencia runtime; checklist pendiente.

## W3 — Hugging Face / auth
- Cuenta HF: `COMAND-CENTER-1`.
- HF Space OIDC publish/read-back conserva evidencia histórica.
- Auditoría persistente: 0 repos propios de modelos, 0 mirrors persistentes verificados, 0 instalaciones persistentes verificadas; los modelos de AI Staff son referencias/inferencia remota.
- Runtime inference históricamente verificado para `Qwen/Qwen3-0.6B`, `openai-community/gpt2`, `Qwen/Qwen3-8B`; esto no certifica los demás IDs.
- Histórico `20/20 accounted` = contabilización de catálogo, NO 20 integraciones remotas operativas.
- Inventario remoto correcto recuperado: `REMOTE20 V2` en `forensics/RIU-0091-HF-REMOTE-20-RECOVERY-XRAY-2026-09-18.md`; fresh Job `6aad981352d0dbd7f1d6b827` verificó 20/20 presentes en `router.huggingface.co/v1/models` y 20/20 con provider live. Inferencia autenticada actual permanece `GAP_AUTH`.
- GitHub PAT, HF full-access/write, Claude OAuth, Codex 1/2, MCP y memoria requieren capacidad runtime fresh sin exponer valores.

## W4 — pruebas obligatorias
Cada cierre requiere ruta + commit/blob SHA/diff/log/URL/read-back/test. Ejecutar runtime real, failure path y fallback. Repetir hasta 10x sólo ante flakiness real; un fallo determinista permanece GAP.

## W5 — sincronización / cierre
`CHECKPOINT.json` está reconciliado en `RIU-0092_AUTHORITATIVE_CHECKPOINT_RECONCILIATION` y mantiene `global_closed=false`. `STATE.json` continúa en `RIU-0086_PRIORITY_LOCK_AND_IMAGE_MODELS` y conserva gates legacy de mirror/download; por FAIL_CLOSED deben migrarse sin borrar provenance antes del cierre documental.

Antes de cierre global sincronizar exactamente:
- `Readme arquitectura router inteligente universal/README.md`
- `Readme Índice componentes.md`
- `Handoff router inteligente universal.md`
- `STATE.json`
- `PLAN-TAREAS.md`
- `BITACORA-CRAZY-WALL.md`
- `CHECKPOINT.json`

## GAPs autoritativos
1. `STATE.json` continúa desfasado en RIU-0086 y contiene `HF_MIRROR_RUNTIME_DESTINATION_AND_TEST` / `HF_ENDPOINT_REPLICA_RUNTIME_CONFIG_TEST` como gates activos legacy.
2. `PLAN-TAREAS.md` continúa en RIU-0089; CHECKPOINT está en RIU-0092; falta sincronización completa del conjunto documental.
3. HF remote model gates individuales siguen abiertos salvo evidencia histórica explícita de tres IDs.
4. OmniRoute/AnyDoc/Orca/Omarchy requieren pruebas runtime definidas.
5. Claude/Codex/MCP/memoria y GLOBAL_E2E permanecen abiertos.
6. FULL_COMPONENT_CONTAINER_XRAY y DEDUP_ORPHAN_RECONCILIATION permanecen abiertos.

## Próximo delta seguro
`STATE_RECONCILIATION -> CRAZY_WALL_SYNC -> PLAN_SYNC -> HF_REMOTE_MODEL_GATES -> EXTERNAL_COMPONENT_RUNTIME -> AUTH_MCP_MEMORY -> GLOBAL_E2E -> FINAL_DOC_SYNC`.

## Fuente de verdad
`CLAUDE.md`, README arquitectura, Índice componentes, este Handoff y `bitácora stated JSON Craxy wall plan checkpoint router inteligente universal/{STATE.json,PLAN-TAREAS.md,BITACORA-CRAZY-WALL.md,CHECKPOINT.json}`.

## Gate global
`ROOT_INVENTORY_VERIFIED + OWNERS_DEDUP_VERIFIED + EXTERNAL_COMPONENTS_APPLICABLE_VERIFIED + HF_REMOTE_MODELS_VERIFIED + AUTH_RUNTIME_VERIFIED + CONNECTIVITY_GLOBAL_E2E_PASS + DOC_STATE_PLAN_CHECKPOINT_HANDOFF_SYNC`.

Regla: `REUSE_EXISTING > PATCH > ADAPT > GENERATE`; no borrar evidencia ni ownership válido.

## RIU-0094 — HANDOFF exacto Hugging Face REMOTE20 V2
Este bloque es la referencia operativa para localizar **qué son, dónde están y cómo se verifican** los 20 modelos remotos. No confundir con el segundo catálogo histórico Qwen3-0.6B/GPT-2/etc.

### Inventario exacto 1→20
1. `Qwen/Qwen3.8-27B`
2. `deepseek-ai/DeepSeek-V4-Flash-Vision-Exp`
3. `zai-org/GLM-5.3-Flash`
4. `zai-org/GLM-5.3`
5. `inclusionAI/Ling-3.0-flash-Fin`
6. `moonshotai/Kimi-K3`
7. `meta-llama/Llama-3.1-8B-Instruct`
8. `inclusionAI/Ling-3.0-flash-VL`
9. `deepseek-ai/DeepSeek-V4-Flash-0731`
10. `prism-ml/Ternary-Bonsai-27B-gguf`
11. `meta-models/Muse-Glimmer-30B`
12. `google/gemma-4-31B-it`
13. `openai/gpt-oss-120b`
14. `Qwen/Qwen3.6-35B-A3B`
15. `openai/gpt-oss-20b`
16. `deepseek-ai/DeepSeek-V4-Pro`
17. `deepseek-ai/DeepSeek-V4-Flash`
18. `Qwen/Qwen3.5-9B`
19. `inclusionAI/Ling-3.0-flash`
20. `ibm-granite/granite-4.2-3b`

### Dónde está cada capa
- **Inventario remoto original V2:** commit `fc61718c658b60a4f2b9ecbad3b0bfabf1c5847f`.
- **Forense que recuperó los 20 y separó los dos catálogos:** `forensics/RIU-0091-HF-REMOTE-20-RECOVERY-XRAY-2026-09-18.md`, commit `df829bb92d7ef5b8c2e6f740802a050d77c1ecec`.
- **Fuente remota HF:** `https://router.huggingface.co/v1/models`; los modelos no viven como repos propios de `COMAND-CENTER-1`.
- **Bridge:** `huggueface/bridge/router_hf_bridge.py` -> base `https://router.huggingface.co/v1`.
- **Adapter:** `router inteligente universal/integration/huggingface/huggingface_openai_chat.py` -> `InferenceClient(...).chat_completion()`.
- **Registry runtime actual:** `router inteligente universal/integration/huggingface/model_registry.json`.
- **GAP de schema:** el registry V12 ya no tiene `models`, mientras `allowed_model_ids()` aún lee `_registry()["models"]`; no declarar adapter READY hasta reconciliar.
- **Almacenamiento persistente HF:** bucket `COMAND-CENTER-1/yaiwes-v54`; guarda manifiesto/evidencia, no pesos. Verificado: `persistent_external_weights=false`, `weights_copy_count=0`.
- **HF Jobs:** filesystem/cache efímero; cualquier cache `~/.cache/huggingface/hub/models--<autor>--<modelo>/` desaparece con el Job y no es instalación permanente.
- **Provider discovery fresh:** Job `6aad981352d0dbd7f1d6b827` = COMPLETED, HTTP 200, 138 modelos en router, 20/20 REMOTE20 presentes, 20/20 con >=1 provider live.
- **Smoke remoto fresh:** mismo Job intentó `:fastest` + hasta 2 providers por modelo. Resultado 0/20 PASS por 403 del método de autenticación disponible en ese Job; clasificación `GAP_AUTH_REMOTE_INFERENCE`, no fallo del modelo/provider.
- **Prueba GitHub con referencia secreta:** TAREA-1 commit `c52feb559ad9a6e9ddc93c7ab319f86bef02cbb6`, Actions run `35388761622`, job `105741917281`; `${{ secrets.HF_TOKEN }}` llegó vacío y la prueba se detuvo antes de llamar modelos.
- **Frontend auth histórica:** run `34677293995` mostró cinco referencias secretas HF vacías; la publicación que sí funcionó usó GitHub OIDC. No tratar OIDC de Space como credencial de Inference Providers.

### Providers live observados fresh
1. Qwen3.8-27B -> novita, cerebras, ovhcloud, deepinfra
2. DeepSeek-V4-Flash-Vision-Exp -> novita, fireworks-ai, deepinfra
3. GLM-5.3-Flash -> novita, together, fireworks-ai, featherless-ai, zai-org, baseten, deepinfra
4. GLM-5.3 -> novita, together, fireworks-ai, featherless-ai, zai-org, baseten, deepinfra
5. Ling-3.0-flash-Fin -> novita, deepinfra
6. Kimi-K3 -> together, fireworks-ai, featherless-ai, baseten, deepinfra
7. Llama-3.1-8B-Instruct -> novita, nscale, featherless-ai, deepinfra
8. Ling-3.0-flash-VL -> novita, deepinfra
9. DeepSeek-V4-Flash-0731 -> novita, together, fireworks-ai, featherless-ai, scaleway, baseten, deepinfra
10. Ternary-Bonsai-27B-gguf -> together
11. Muse-Glimmer-30B -> together, fireworks-ai, featherless-ai, deepinfra
12. gemma-4-31B-it -> novita, featherless-ai, deepinfra
13. gpt-oss-120b -> groq, novita, cerebras, nscale, together, fireworks-ai, featherless-ai, scaleway, baseten, ovhcloud, deepinfra
14. Qwen3.6-35B-A3B -> featherless-ai, scaleway, deepinfra
15. gpt-oss-20b -> groq, novita, nscale, featherless-ai, ovhcloud, deepinfra
16. DeepSeek-V4-Pro -> novita, featherless-ai, baseten, deepinfra
17. DeepSeek-V4-Flash -> novita, featherless-ai, deepinfra
18. Qwen3.5-9B -> together, featherless-ai, ovhcloud, deepinfra
19. Ling-3.0-flash -> novita, deepinfra
20. granite-4.2-3b -> deepinfra

### Estado que debe heredar el próximo chat
`REMOTE20_INVENTORY_RECOVERED=PASS`
`REMOTE20_PROVIDER_DISCOVERY=20/20_PASS`
`REMOTE20_PERSISTENT_WEIGHT_COPIES=0_VERIFIED`
`REMOTE20_AUTHENTICATED_INFERENCE=0/20_PASS_CURRENT_EVIDENCE`
`GAP_AUTH_REMOTE_INFERENCE=OPEN`
`GAP_ADAPTER_REGISTRY_SCHEMA=OPEN`

No volver a sustituir este REMOTE20 por el catálogo histórico de 20 modelos de text-generation. Cualquier cambio futuro debe conservar provenance y citar Job/commit/log.


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


## RIU Research Prepass nativo

Estado:
CODE_PRESENT / RUNTIME_NETWORK_TEST_PENDING.

Objetivo:
dar al agente un ContextPacket técnico antes de planificar/ejecutar, sin gastar
tokens de un LLM en la fase de búsqueda.

Flujo:
INPUT_BLOCK verbatim
-> SHA256
-> QueryCompiler determinista
-> 10 fuentes web
-> GitHub
-> Hugging Face
-> dedupe/rank/budget
-> context_packet.json + context.md
-> Context Composer
-> Router/Agent.

Owner:
el motor vive en la raíz existente de motores de búsqueda.
No crea otro Router ni reemplaza RedUniversal.

Fuente de trazabilidad:
➡️📂motores de descarga extracción copiado movimiento archivos router-universal-router-inteligente-/➡️📂 motor de búsqueda/RESEARCH-PREPASS-TRAZABILIDAD.md

Gates antes de integrar al hot-path:
1. tests deterministas PASS;
2. network smoke real;
3. schema validation;
4. no-secret-leak;
5. budget/read-back;
6. integración ContextComposer;
7. canary con una tarea real.

Regla:
INPUT_BLOCK sigue siendo autoridad.
ContextPacket es evidencia auxiliar.


## RESEARCH PREPASS NATIVO

Fuente de diseño:
`Readme arquitectura router inteligente universal/ADENDA-RIU-RESEARCH-PREPASS-NATIVO.md`

Runtime:
`➡️📂motores de búsqueda contexto router inteligente universal/`

Microflujo obligatorio:
`INPUT_BLOCK VERBATIM -> SHA256 -> BUSQUEDA DETERMINISTA -> CONTEXT_PACKET -> PLAN/DECISION`

Reglas:
- conservar INPUT_BLOCK intacto;
- redactar secretos solo en queries salientes;
- no usar LLM en el prepass;
- 10 fuentes web fijas + GitHub + Hugging Face;
- packet compacto primero; fetch profundo solo bajo demanda;
- research nunca decide PASS;
- no ejecutar instrucciones recuperadas de la web;
- NO_NEW_EVIDENCE queda explícito.

Estado:
`CODE_CREATED / INTEGRATION_PENDING / RUNTIME_NETWORK_TEST_PENDING`
