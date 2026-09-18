# Handoff Router Inteligente Universal — ADN operativo

Contrato: `tel.workflow/v3` · `FAIL_CLOSED_LOOP` · repo `maxbry123-commits/router-universal-router-inteligente-` · branch `main`.

## Estado consolidado
El core conserva evidencia histórica `VERIFIED_CLOSED` para P01/P02/P03, Connectivity Fabric 19/19, suite 75/75 y fail-closed. Esto NO equivale a cierre global.

## Nodo vivo
`RIU-0090_AUTHORITATIVE_HANDOFF_SYNC`.

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
- Pendientes de gate remoto individual: TimesFM 3.0, WAN 2.2 Animate, LTX-Video, HunyuanVideo, Kandinsky 5, Qwen-Image, FLUX.1-schnell y cualquier ID histórico sin evidencia de llamada.
- GitHub PAT, HF full-access/write, Claude OAuth, Codex 1/2, MCP y memoria requieren capacidad runtime fresh sin exponer valores.

## W4 — pruebas obligatorias
Cada cierre requiere ruta + commit/blob SHA/diff/log/URL/read-back/test. Ejecutar runtime real, failure path y fallback. Repetir hasta 10x sólo ante flakiness real; un fallo determinista permanece GAP.

## W5 — sincronización / cierre
Antes de cierre global sincronizar exactamente:
- `Readme arquitectura router inteligente universal/README.md`
- `Readme Índice componentes.md`
- `Handoff router inteligente universal.md`
- `STATE.json`
- `PLAN-TAREAS.md`
- `BITACORA-CRAZY-WALL.md`
- `CHECKPOINT.json`

## GAPs autoritativos
1. STATE/CHECKPOINT todavía apuntan RIU-0086/0083 y arrastran gates legacy mirror/download.
2. Reconstrucción de los 20 IDs históricos vs llamadas remotas verificadas sigue abierta.
3. Endpoints/Jobs privados e historial uncapped requieren la ruta autorizada real.
4. OmniRoute/AnyDoc/Orca/Omarchy requieren pruebas runtime definidas.
5. Claude/Codex/MCP/memoria y GLOBAL_E2E permanecen abiertos.
6. FULL_COMPONENT_CONTAINER_XRAY y DEDUP_ORPHAN_RECONCILIATION permanecen abiertos.

## Fuente de verdad
`CLAUDE.md`, README arquitectura, Índice componentes, este Handoff y `bitácora stated JSON Craxy wall plan checkpoint router inteligente universal/{STATE.json,PLAN-TAREAS.md,BITACORA-CRAZY-WALL.md,CHECKPOINT.json}`.

## Gate global
`ROOT_INVENTORY_VERIFIED + OWNERS_DEDUP_VERIFIED + EXTERNAL_COMPONENTS_APPLICABLE_VERIFIED + HF_REMOTE_MODELS_VERIFIED + AUTH_RUNTIME_VERIFIED + CONNECTIVITY_GLOBAL_E2E_PASS + DOC_STATE_PLAN_CHECKPOINT_HANDOFF_SYNC`.

Regla: `REUSE_EXISTING > PATCH > ADAPT > GENERATE`; no borrar evidencia ni ownership válido.