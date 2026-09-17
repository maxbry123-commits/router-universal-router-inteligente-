# BITÁCORA CRAZY WALL — ROUTER INTELIGENTE UNIVERSAL

**Contrato:** `tel.workflow/v3` · **Modo:** `FAIL_CLOSED_LOOP`.

## RIU-0001..0062 — BASE CERRADA
P01/P02/P03=`VERIFIED_CLOSED`; `MODEL_CERTIFICATION_20_OF_20_ACCOUNTED`; regresión core `RIU FAST-CLOSE` PASS.

## RIU-0063/0064 — CONNECTIVITY FABRIC
- raíz canónica `conectividad con Router inteligente universal/`.
- 19/19 repos con `PUENTE-RIU-<repo>.yaml` v2.
- frontend v2 integra GitHub + HF `COMAND-CENTER-1` + Jobs CPU/GPU + Space `yaiwes-ui-factory` + Claude GitHub MCP + memoria.
- runtime base y fabric probados.

## RIU-0065 — SUITE COMPLETA
Regresión final amplia: **75 passed, 2 warnings**. Connectivity runtime fresco: **7 passed**. Fail-closed sin secrets validado.

## RIU-0066 — PROBES + RUNNER CODESPACES
Runtime implementa probes GitHub identity/permisos, HF whoami/role y GitHub MCP initialize sin exponer secretos. Runner `integration/verify_runtime_connectivity.py` preparado para ejecución en entorno autorizado.

## RIU-0067 — HF OIDC / TRUSTED PUBLISHER
- Space `COMAND-CENTER-1/yaiwes-ui-factory` confirmado `static`.
- frontend OIDC publica correctamente al Hub.
- runs `34675165228` attempt 2 y `34677293995`: upload PASS.
- Hub read-back HTTP 200 PASS.

## RIU-0068 — BOOTSTRAP GLOBAL AUTH
Core del Router = **100% VERIFIED_CLOSED**. La capa global de credenciales externas continúa separada del core y se valida fail-closed.

## RIU-0069 — CLAUDE DIRECT GITHUB ROOT ACCESS — NODO VIVO
Delta mínimo aplicado 2026-09-13:
- `GitHub Backup HF` queda clasificado como **respaldo opcional, no bloqueante**.
- Hugging Face no se usa como autoridad para editar GitHub.
- Nuevo `.github/workflows/claude-root-editor.yml` con `contents: write`, `pull-requests: write`, `issues: write`, usando `RIU_GITHUB_PAT` cuando existe o `github.token` para el repo actual.
- Nuevo `CLAUDE.md` en raíz: GitHub `main` es fuente de verdad y la ausencia del backup HF no detiene lectura/escritura de raíces.
- `.github/workflows/claude-token-setup.yml` corregido: ya no imprime en claro la sesión de `setup-token`; sanitiza salida y destruye el log runner-local.

### Evidencia
- `f3d0daa60cecc25e711886cac6b6f468feedfe05` — setup-token seguro.
- `946f1a0e1c976298c6c34d4e70f0a07243109aa6` — Claude Root Editor.
- `ddfeb73e4c5d80515e28ed8511c14f8f0fc1ba88` — `CLAUDE.md` canónico.

### GAP REAL RESTANTE
La configuración está materializada y leída de vuelta, pero **Claude runtime no se marca PASS** hasta ejecutar el workflow con `CLAUDE_CODE_OAUTH_TOKEN` disponible y obtener un commit/read-back real de una edición de raíz. Para edición transversal a otros repos también se requiere `RIU_GITHUB_PAT`/GitHub App con permisos efectivos.

## ESTADO
- Core/arquitectura/runtime: `VERIFIED_CLOSED` 100%.
- Ruta directa de Claude en GitHub: `MATERIALIZED`.
- Verificación runtime de escritura Claude: `PENDING_FRESH_WRITE_READBACK`.
- Nodo: `RIU-0069_CLAUDE_DIRECT_GITHUB_ROOT_ACCESS`.


## RIU-0070 — X-RAY RAÍZ + 4 COMPONENTES EXTERNOS — NODO ACTIVO
Delta 2026-09-17:
- Auditoría shallow X-Ray completada sobre **29 entradas raíz**, snapshot base `d001d96cfa382888d409255e5dd3e9d2b6372860`.
- README arquitectura actualizado: commit `8616da2a84bd5f803ca38a9bbeaea1ed93bafbac`.
- PLAN-TAREAS actualizado: commit `b5c2d5585de2eba4de11bfb08795cca56f71b811`.
- STATE actualizado: commit `561b546d1344a551cb9c09387044d7aadf4aa88c`.
- Fuentes externas verificadas: OmniRoute=`diegosouzapw/OmniRoute`; Orca ADE=`saiichi/orca`; Omarchy=`basecamp/omarchy`; AnyDoc=`firecrawl/anydoc`.
- Owners preservados: runtime=`router inteligente universal/`; connectivity=`conectividad con Router inteligente universal/`; estado=`bitácora.../`; evidencia=`forensics/` + JSON de auditoría; donor/download quedan sin ownership.
- No se declara instalación runtime de los cuatro externos. Estado: `BOUNDARY_DEFINED / PENDING_RUNTIME_TEST`.

### Plan de cierre RIU-0070
1. Consolidar owners/duplicados por referencia sin borrar evidencia.
2. Materializar OmniRoute/AnyDoc como adapters; validar Orca como ADE externo y Omarchy como host opcional.
3. Cerrar auth GitHub/HF/Claude/Codex + MCP/memoria y ejecutar E2E global.
4. Sincronizar arquitectura + STATE + PLAN + BITÁCORA y exigir URLs/SHA/log/read-back antes de `VERIFIED_CLOSED`.

### Gates
- `ROOT_29_ACCOUNTED`
- `EXTERNAL_4_BOUNDARIES_DEFINED`
- `NO_ROUTING_OWNERSHIP_CONFLICT`
- `AUTH_RUNTIME_VERIFIED`
- `CONNECTIVITY_GLOBAL_E2E_PASS`
- `STATE_PLAN_BITACORA_SYNC`

Estado actual: **ACTIVE / GAP runtime**.


### READ-BACK RIU-0070
PASS 2026-09-17: README arquitectura, PLAN-TAREAS, STATE, BITÁCORA y CHECKPOINT fueron releídos desde `main`; los cinco marcadores RIU-0070 están presentes. Este PASS cierra sólo la **sincronización documental/estado**. Adapters externos, auth runtime y E2E global permanecen abiertos.


## RIU-0071 — FORENSIC X-RAY AUTORITATIVO — NODO ACTIVO
- Fresh HEAD inicial: `55b8136a8f19d3bf9dda5f5febe0398ba5f07ff4`.
- Corrección: raíz real = **28**, no 29; `.github/workflows` era hijo, no raíz.
- Probe recursivo: 35.979 entradas devueltas, `truncated=true`; no se declara inventario total de archivos.
- Inventario por contenedores: runtime top-level=11; donor OSS dirs=62; legacy component roots=5.
- Duplicado candidato: `LiteLLM` / `litellm`; prohibido borrar antes de provenance/content comparison.
- Bridges HF candidatos a consolidación: `integration/huggingface`, `coneccion huggueface Github/router`, `huggueface/bridge`.
- Inventario: `forensics/RIU-0071-XRAY-COMPONENT-INVENTORY-2026-09-17.json`, commit `a5a3e02cea01d753a495b5090c4ae46146200a64`.
- Cola del chat recuperada: inventario HF, pruebas modelos, Code, mirrors, >50 identidades, compute, mix agentes, MCP/API, skills, GitHub+HF, watchdog 404, externos, auth y E2E.
Estado: **ACTIVE / NO GLOBAL CLOSE**.
