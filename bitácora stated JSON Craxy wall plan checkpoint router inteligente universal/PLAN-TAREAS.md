# PLAN DE TAREAS — ROUTER INTELIGENTE UNIVERSAL
Contrato: `tel.workflow/v3` · `FAIL_CLOSED_LOOP`.

## Estado consolidado
- Core P01/P02/P03 ✅
- Model certification 20/20 accounted ✅
- Regresión core ✅
- Connectivity Fabric 19/19 bridge v2 ✅
- Router runtime + probes ✅
- Suite amplia 75/75 ✅
- Connectivity runtime fresca 7/7 ✅
- Fail-closed sin secrets ✅
- HF Space OIDC write ✅

## Nodo activo
`RIU-0071_FORENSIC_XRAY_AUTHORITATIVE_INVENTORY`.

## Tareas activadas — sin sobreingeniería
1. **BOOTSTRAP_GITHUB** — cargar `RIU_GITHUB_PAT` en Router Actions Secrets con acceso a los 8 repos y permiso suficiente para escribir Actions secrets.
2. **BOOTSTRAP_HF** — cargar `RIU_HF_TOKEN` role=`write` para `COMAND-CENTER-1`.
3. **PROPAGATE_8_REPOS** — ejecutar manualmente `.github/workflows/riu-propagate-auth-secrets.yml`; debe abortar si falta `RIU_GITHUB_PAT`.
4. **PROBE_AUTH** — ejecutar `.github/workflows/riu-auth-presence-probe.yml`; exigir HF identity/role PASS y GitHub read-back/permisos sobre los 8 repos.
5. **CODEX_AUTH_1_2** — completar device-auth de las dos cuentas y persistir solo `auth.json` cifrado en Actions Secrets.
6. **CLAUDE_AUTH** — completar `claude setup-token` y persistir únicamente el token cifrado.
7. **GLOBAL_E2E** — GitHub + HF + MCP + memoria, con evidencia fresca y cierre final.

## Evidencia que ya existe
- Probe de presencia workflow materializado y seguro: `.github/workflows/riu-auth-presence-probe.yml`.
- Propagación fail-closed materializada: `.github/workflows/riu-propagate-auth-secrets.yml`.
- Probe run previo `34677207175`: credenciales globales estaban ausentes al momento de la prueba.
- HF OIDC frontend: runs `34675165228` attempt 2 y `34677293995` PASS; Hub read-back HTTP 200.

## GAP exacto
No falta arquitectura del router. Falta **inyectar y validar en runtime las credenciales globales externas** y completar los logins de suscripción de Codex/Claude. Los valores secretos no se escriben en Git, logs ni chat.

## Gate de cierre
`VERIFIED_CLOSED` solo cuando `GITHUB_PAT_RUNTIME_VERIFIED + HF_GLOBAL_WRITE_RUNTIME_VERIFIED + CODEX_1_2 + CLAUDE + MCP + MEMORY + CONNECTIVITY_GLOBAL_E2E_PASS` tengan evidencia fresca.


## RIU-0070 — X-RAY RAÍZ + EXTERNOS + PLAN DE CIERRE
1. **ROOT_XRAY_28** — contabilizar las 29 entradas raíz y asignar owner: runtime, connectivity, state, docs, evidence, donor/legacy.
2. **OMNIROUTE_ADAPTER** — definir/probar `connector_registry -> adapter_omniroute`; health, fallback y rate-limit simulation obligatorios.
3. **ORCA_ADE** — validar Orca gráfico como control plane externo para Claude Code/Codex con worktrees; no puede mergear sin verifier RIU.
4. **OMARCHY_HOST** — documentar/validar workstation opcional; nunca dependencia del runtime ni gate de producción.
5. **ANYDOC_ADAPTER** — wrapper de ingestión a Markdown y corpus multiformato; hashes y error path obligatorios.
6. **DEDUP_ROOT** — consolidar conexiones/índices duplicados por referencia, sin borrar hasta verificar que no haya información única.
7. **AUTH_RUNTIME** — continuar `CLAUDE_CODE_OAUTH_TOKEN`, `RIU_GITHUB_PAT`, `RIU_HF_TOKEN`, Codex 1/2, MCP y memoria sin exponer valores.
8. **GLOBAL_E2E** — ejecutar Router + GitHub + HF + adapters externos habilitados + verifier; registrar logs/URLs/SHA.
9. **SYNC_CLOSE** — STATE + PLAN + BITÁCORA + arquitectura deben coincidir antes de `VERIFIED_CLOSED`.

### Olas
- W0 preservación/evidencia ✅ X-Ray documental materializado.
- W1 owners y deduplicación: EN CURSO.
- W2 externos: PENDIENTE pruebas runtime.
- W3 auth/connectivity: PENDIENTE credenciales/runtime.
- W4 E2E/final: PENDIENTE.

### Gate final RIU-0070
`ROOT_28_ACCOUNTED + EXTERNAL_4_BOUNDARIES_DEFINED + NO_ROUTING_OWNERSHIP_CONFLICT + AUTH_RUNTIME_VERIFIED + CONNECTIVITY_GLOBAL_E2E_PASS + STATE_PLAN_BITACORA_SYNC`.

Evidencia arquitectura: commit `8616da2a84bd5f803ca38a9bbeaea1ed93bafbac`.


## RIU-0071 — COLA AUTORITATIVA COMPLETA
### W1 — Forense/organización
1. **XRAY-ROOT-28** — 28/28 raíces contabilizadas; mantener owner y clasificación.
2. **XRAY-COMPONENTS** — continuar inventario por contenedores porque el árbol recursivo global está truncado; inventario base: `forensics/RIU-0071-XRAY-COMPONENT-INVENTORY-2026-09-17.json`.
3. **DEDUP-LITELLM ✅ AUDITADO / NO DELETE** — árboles divergentes; `LiteLLM` tiene SOURCE_URL + SOURCE_COMMIT `658f5066…`; `litellm` carece de esos marcadores y contiene ZIP parciales. Preservar ambos; `LiteLLM` canonical donor candidate, `litellm` legacy snapshot hasta resolver origen/uso.
4. **HF-BRIDGE-CONSOLIDATION ✅ AUDITADO** — owner canónico=`integration/huggingface`; `dispatcher.py` scheduler ADAPT_CANDIDATE; `hf_jobs_adapter.py` overlap de submit + scheduling; `router_hf_bridge.py` DONOR/LEGACY y no routing owner. Runtime scheduler pendiente de tests.
5. **LEGACY-ROUTER-CORES** — comparar `router inteligente software/componentes todos/router core*` contra runtime canónico; donor/legacy sin segundo owner.

### W2 — Hugging Face / modelos / routing
6. **HF-SCHEDULER ✅** — scheduler canónico HF1→HF2→HF3 en `integration/huggingface/hf_scheduler.py`; 5/5 rondas estables, 7 tests por ronda, Job `6aac7c9eb1dc2b62dc58faf9` COMPLETED.\n7. **HF-INVENTORY 🟡 PARTIAL** — fresh: OAuth COMAND-CENTER-1; ventana 100 Jobs (8 completed/1 canceled/91 error), 2 scheduled, 3 Spaces públicos, registry 20 slots; privado + historial uncapped siguen GAP. Evidencia `forensics/RIU-0075-HF-INVENTORY-PARTIAL-2026-09-17.md`.
8. **HF-MODEL-RUNTIME** — prueba real por modelo descubierto antes de operational PASS.
9. **HF-CODE-MODELS ✅ CLASIFICADO** — M04=CODE_SPECIALIZED por base model Qwen3-Coder; M15=CODE_CAPABLE_TRAINING_EVIDENCE generalista; otros 18 no demostrados Code-specialized. Runtime Code sigue pendiente.
10. **HF-MIRROR-REPLICA ✅ DISEÑO** — repo duplicate ≠ endpoint replicas ≠ revision-pinned snapshot; gates/provenance definidos. Ejecución real queda pendiente de destino/costo explícito.
10. **ROUTING-50-IDENTITIES ✅ 64 VERIFIED** — `red/identity_pool.py`; 64 identidades secuenciales, quota/cooldown/mirror/priority, secret refs only; HF Job `6aac7f48b1dc2b62dc58fb73`, 5×5 tests PASS.
11. **HF-COMPUTE ✅ POLICY** — HF1 CPU control/small; HF2 A10G medium baseline; HF3 large/burst by benchmark/provider. No fixed paid hardware assumed.
12. **AGENT-MODEL-MIX ✅ POLICY** — tiny 0.5–1.5B; small 3–4B; standard 7–8B; specialist/large 30B+ only with exact runtime PASS; identity failover before size escalation.
13. **HF-MCP-API ✅ BOUNDARY / E2E MCP PENDING** — official HF MCP OAuth/client-managed + Hub API token secret-ref separated; 5×10 tests PASS, remote RIU OAuth MCP handshake still pending.
14. **HF-SKILLS** — integrar skills HF verificadas.
15. **GITHUB-HF** — conexión autorizada GitHub+HF y evidencia runtime.
16. **HF-WATCHDOG-404 ✅ INCIDENTE RESUELTO / REPLACEMENT GAP** — causa raíz: commit frontend `e0b3cd3b…` eliminó intencionalmente la raíz antigua; Scheduled `6aa1af28…` quedó stale y fue suspendido con 2× read-back. Reemplazo canónico queda GAP hasta definir QUEUE/STATE/INDEX/DEST explícitos.

### W3 — Externos
17. **OMNIROUTE** — adapter downstream, health/fallback/rate-limit test.
18. **ANYDOC** — ingest adapter + corpus multiformato + error path/hashes.
19. **ORCA** — ADE externo con worktrees y verifier-gated merge.
20. **OMARCHY** — host opcional; checklist, nunca dependencia runtime.

### W4 — Auth/connectivity
21. **CLAUDE** — OAuth presence + harmless root write/read-back.
22. **CODEX-1/2** — device auth verificable sin persistir secretos en claro.
23. **GITHUB-PAT/HF-WRITE** — runtime roles/permisos efectivos.
24. **MCP/MEMORY** — boundary E2E fresh.

### W5 — Cierre
25. **GLOBAL-E2E** — Router + GitHub + HF + integrations habilitadas + failure paths.
26. **FINAL-DEDUP-ORPHANS** — ninguna eliminación sin provenance/equivalencia/read-back.
27. **SYNC-FINAL** — arquitectura + STATE + PLAN + BITÁCORA + CHECKPOINT + Handoff consistentes.
28. **VERIFY_FINAL** — sólo `VERIFIED_CLOSED` con todas las pruebas/evidencias requeridas.


## RIU-0085 — HF REAL INVENTORY + VIDEO MODELS
1. **INVENTORY_REAL** — mantener separado repos propios (0 fresh), inferencia verificada (3), referencias Router provisionales (4), mirrors persistentes verificados (0) e instalaciones locales persistentes verificadas (0).
2. **WAN22_ANIMATE** — licencia/revision/tamaño -> motor existente -> descarga -> hashes -> carga/inferencia -> evidencia -> PASS sólo si todo cumple.
3. **LTX_VIDEO** — resolver licencia exacta -> revision/tamaño -> descarga/hash -> carga/inferencia.
4. **HUNYUANVIDEO** — resolver licencia exacta -> revision/tamaño -> descarga/hash -> carga/inferencia.
5. **COMPUTE_RECALC** — recalcular HF1/HF2/HF3 después de conocer pesos/requisitos reales de los modelos aceptados.


## PRIORITY LOCK — 5 tareas solamente hasta supervisión Claude
1. **HF Skills Library** — verificar instalación/descubrimiento/runtime.
2. **Dataset HF conectado** — comprobar conexión/lectura/evidencia real.
3. **HF compute + 50 API identities + modelos/mirrors** — inventario real, dimensionamiento y prueba sin exponer secretos.
4. **Integración de modelos AI Staff** — TimesFM 3.0 + WAN 2.2 Animate + LTX-Video + HunyuanVideo + Kandinsky 5 + Qwen-Image + FLUX.1-schnell, uno por uno, fail-closed.
5. **Archify Skills + diagrama de flujo** — resolver upstream exacto, descargar/integrar skills y mantener diagrama listo vs pendiente.

Fuera de estas cinco tareas: PAUSADO hasta supervisión Claude.
