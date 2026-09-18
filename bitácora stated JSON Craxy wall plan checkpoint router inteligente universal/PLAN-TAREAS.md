# PLAN DE TAREAS — ROUTER INTELIGENTE UNIVERSAL
Contrato: `tel.workflow/v3` · `FAIL_CLOSED_LOOP`.

## Estado consolidado
Core P01/P02/P03, regresión, Connectivity Fabric 19/19, suite 75/75 y HF Space OIDC conservan su evidencia histórica. La presencia documental NO equivale a cierre global.

## Nodo activo
`RIU-0089_AUTHORITATIVE_PLAN_RECONCILIATION`.

## Regla de arquitectura HF — AUTORITATIVA
AI Staff usa `REMOTE_INFERENCE_ONLY`: `RedUniversal -> connector_registry -> HF adapter/InferenceClient -> Inference Provider/Endpoint remoto -> model_id`.

**PROHIBIDO como gate activo:** descargar pesos, `snapshot_download`, mirror de pesos, hash de descarga o instalación local para integrar modelos AI Staff. RIU-0078 y RIU-0085/0086 se conservan únicamente como provenance histórica donde describan mirrors/downloads; quedan SUPERSEDED para el camino normal de inferencia.

Gate por modelo:
`REGISTER -> REMOTE_PROVIDER_DISCOVERY -> AUTH_REFERENCE -> REMOTE_INFERENCE_SMOKE -> FAILURE_FALLBACK_TEST -> EVIDENCE -> READY`.

No declarar READY por catálogo, README, presencia de ID o Job que sólo cargó un modelo efímeramente.

## W1 — organización / dedup / owners
1. Mantener 28 raíces contabilizadas y continuar X-Ray por contenedores; árbol recursivo global anterior fue truncado.
2. `RedUniversal` conserva ownership único de routing.
3. LiteLLM/litellm: preservar ambos hasta provenance/equivalencia completa; no borrar evidencia.
4. HF canonical owner=`integration/huggingface`; donors/legacy no adquieren ownership.
5. Comparar router cores legacy contra runtime canónico y clasificar donor/legacy/orphan/adapter-needed.

## W2 — componentes y HF
1. OmniRoute: downstream adapter detrás de connector_registry; health/fallback/rate-limit obligatorios.
2. AnyDoc: ingest adapter; multiformato/hash/error-path.
3. Orca: ADE externo; worktrees + verifier-gated merge; nunca router owner.
4. Omarchy: host opcional; nunca dependencia runtime.
5. HF scheduler: conservar evidencia Job `6aac7c9eb1dc2b62dc58faf9` 5/5.
6. HF inventory: separar repos propios, referencias de catálogo, llamadas remotas verificadas, Jobs efímeros, endpoints y almacenamiento persistente.
7. Modelos AI Staff pendientes de gate remoto individual: TimesFM 3.0, WAN 2.2 Animate, LTX-Video, HunyuanVideo, Kandinsky 5, Qwen-Image, FLUX.1-schnell.
8. El histórico `20/20 accounted` significa contabilización de catálogo, NO 20 integraciones remotas operativas.

## W3 — auth/runtime/connectivity
1. Validar referencias de secretos sólo en runtime; nunca imprimir valores.
2. GitHub PAT, HF full-access/write, Claude OAuth, Codex 1/2, MCP y memoria requieren evidencia fresh de capacidad efectiva.
3. Un 403 de una credencial limitada no demuestra ausencia de recursos si existe otra ruta autorizada; auditar la ruta real de Actions/secret-ref sin exponerla.
4. Repetir checks externos hasta 10x únicamente ante flakiness real; no convertir fallo determinista en PASS.

## W4 — pruebas
- Runtime real + failure path + fallback + read-back.
- Evidencia mínima por cierre: ruta + commit/blob SHA/diff/log/URL/read-back/test.
- Global E2E: Router + GitHub + HF + integrations habilitadas + verifier.

## W5 — sincronización / cierre
Antes de `VERIFIED_CLOSED`, sincronizar exactamente:
- `Readme arquitectura router inteligente universal/README.md`
- `Readme Índice componentes.md`
- `Handoff router inteligente universal.md`
- `STATE.json`
- `PLAN-TAREAS.md`
- `BITACORA-CRAZY-WALL.md`
- `CHECKPOINT.json`

## GAPs autoritativos actuales
- STATE todavía arrastra `current_node=RIU-0086` y tareas legacy mirror/download; debe migrarse sin borrar provenance.
- El plan anterior señalaba RIU-0071 y contenía gates de descarga para WAN/LTX/Hunyuan: corregido aquí por RIU-0089.
- Reconstrucción completa de los 20 IDs históricos vs llamadas remotas verificadas sigue abierta.
- Endpoints/Jobs privados e historial uncapped requieren auditoría mediante la credencial/runtime realmente autorizada.
- OmniRoute/AnyDoc/Orca/Omarchy aún requieren sus pruebas runtime definidas.
- Auth Claude/Codex/MCP/memoria y GLOBAL_E2E continúan abiertos.

## Gate global
`ROOT_INVENTORY_VERIFIED + OWNERS_DEDUP_VERIFIED + EXTERNAL_COMPONENTS_APPLICABLE_VERIFIED + HF_REMOTE_MODELS_VERIFIED + AUTH_RUNTIME_VERIFIED + CONNECTIVITY_GLOBAL_E2E_PASS + DOC_STATE_PLAN_CHECKPOINT_HANDOFF_SYNC`.

Regla de ejecución: `REUSE_EXISTING > PATCH > ADAPT > GENERATE`; si falta evidencia registrar GAP y continuar con el siguiente delta seguro.