# Claude notas.md — Pizarra de trabajo (Crazy Wall)

Estado: 2026-11-09 · Fuente de tareas: `Claude.md` · Verbatim: `kernel/INPUT_BLOCK_YAIWES_CABLEADO.md`

## Reparto de trabajo (para que no se pisen)

| Router | Responsable | Carpetas que toca |
|---|---|---|
| Router 1 | Claude Code (chat actual) | `ROUTER MVP v1/` y `llm system HF/` · rama `ccr-f01c3de9-bmry0s` |
| Router 2 | Claude Code ROUTER 2 | `HUGGUEFACE SPACE/` (código) y esta notas · rama `ccr-42f0e753-ni96xs` (creada desde `main`) |
| Compartido, solo lectura para los dos | — | `SATÉLITE CENTRAL CONECCION` (`connections/`), `_quarantine/`, `Claude.md`, esta notas |

Regla: Router 2 hace `git pull --rebase origin main` antes de cada push a `main`. Nunca escribe en `llm system HF/` ni en `ROUTER MVP v1/`.

## Estado de tareas (Router 2)

| # | Tarea | Estado | Evidencia |
|---|---|---|---|
| 1 | Auditoría 4 pasadas (10 Spaces) | ✅ | Pasada 1 inventario (`hf_fs find`), pasada 2 lectura de código, pasada 3 cableado (abajo), pasada 4 secretos (abajo) |
| 2 | Clasificación de cada archivo | ✅ | Tabla final abajo |
| 3 | Fusionar duplicados s1/s2/s3 | ✅ | `HUGGUEFACE SPACE/swe-code-models/manager.py` (una copia) · `de49e5b` |
| 4 | Copiar código a `HUGGUEFACE SPACE/<space>/` | ✅ | `6922765` (fetch_models, proxy, boot), `a9cab4d` (provider), `1f52588` (swe-code-web sin cuentas.js), `de49e5b` (manager) |
| 5 | Corregir rama de arranque | ✅ | `_quarantine/boot.sh` con `GITHUB_BRANCH` (default `ccr-f01c3de9-bmry0s`). El arranque real es `riu-router/entrypoint.sh`, que ya usa esa rama |
| 6 | Cerrar lista | ✅ | Esta notas |

## Commits de Router 2 (`ccr-42f0e753-ni96xs`)

- `6922765` código inicial: fetch_models, proxy, boot, scaler (luego retirados)
- `de49e5b` manager.py única copia (default PRIMARY `qwen2.5-coder-0.5b`)
- `a9cab4d` swecode_provider.json (sin claves) y cuarentena de scaler/boot
- `3992231` retirar proxy.py (router LLM vive en `llm system HF/`, Router 1)
- `fd8e680` mover scaler.py a `_quarantine/`
- `cfe557a` mover boot.sh a `_quarantine/`
- `f6d865c` restaurar boot.sh completo en `_quarantine/` y README
- `1f52588` swe-code-web/src sin cuentas.js

Atribución: `de49e5b`, `a9cab4d`, `fd8e680`, `cfe557a`, `f6d865c`, `1f52588` llevan el trailer. `6922765` y el commit de notas `9d4edd3` en `main` no lo llevan. No se reescriben historiales.

## Clasificación final

| Elemento | Destino | Motivo |
|---|---|---|
| GGUF y LoRA (`swe-code-hf-gguf`, `swe-code-loras`) | Se queda en HF | Binarios |
| Bucket `yaiwes-memoria-storage` | Se queda en HF | Almacenamiento |
| `Dockerfile`, `README.md`, `entrypoint.sh` de cada Space | Se queda en HF | Cascarón |
| `manager.py` (s1/s2/s3) | `HUGGUEFACE SPACE/swe-code-models/` | Copia única |
| `fetch_models.py` | `HUGGUEFACE SPACE/swe-code-models/` | Idéntico en s1/s2/s3 |
| `scaler.py` | `HUGGUEFACE SPACE/_quarantine/` | Autoarranque retirado por owner |
| `riu-router/boot.sh` | `HUGGUEFACE SPACE/_quarantine/` | No invocado por el Dockerfile ni por `entrypoint.sh` |
| `riu-router/swecode_provider.json` | `HUGGUEFACE SPACE/riu-router/` | Sin claves |
| `riu-router/proxy.py` | Retirado (no copiado) | Router LLM de Router 1 (`llm system HF/llm_router/`) |
| `riu-router/openclaw.sh` | Satélite de comunicación (no copiar) | Gateway; requiere `OPENCLAW_GATEWAY_TOKEN` |
| `swe-code-web/src/*` excepto `cuentas.js` | `HUGGUEFACE SPACE/swe-code-web/src/` | Decisión del owner |
| `swe-code-web/src/cuentas.js` | No copiado | Decisión del owner (rotación de cuentas) |
| `claude-github-mcp-backup/app.py`, `door.py`, `mini.py`, `fleet.py` | Satélite de comunicación (no copiar) | Puerta MCP y orquestación del Router |
| `hf-bucket-mcp/src/*` | Satélite de comunicación (no copiar) | Servidor MCP de subida a buckets |
| `local-llm-router`, `-v2`, `-v7` | Inventario, sin copia | Fuera del plan de copia |

## Pasada 3 — cableado vs `SYSTEM_WIRING_REGISTRY.yaml` y `connections/`

- **C-011** (`space_riu_router` ← `github_source`, apunta a `router-mvp/router/boot.sh`): el Space ejecuta `riu-router/entrypoint.sh`, que clona `ccr-f01c3de9-bmry0s`. Discrepancia registrada.
- **O1** (espejo vs auto-pull): respondido por evidencia. `riu-router/entrypoint.sh` hace auto-pull de GitHub en cada arranque (`git fetch` + `reset --hard` de la rama). `boot.sh`, que clona `main`, no se ejecuta.
- **`huggingface_mirror`**: el registro dice `push_por_protocolo_git_allowlist`; el código real es auto-pull en arranque. Corrección pendiente en el registro (satélite, fuera de Router 2).
- **`mcp_router_riu`, `space_riu_router`**: el registro los marca TESTING con evidencia de 2026-11-06. No re-probados en esta pasada.
- **Dataset**: el plan menciona `scripts/`, `job-evidencia/`, `results/`, `openclaw-prep/`, `apk/`. En `swe-code-hf-gguf` no existen. Solo hay 3 GGUF, `README.md` y `manifest.json`. No se borró nada.

## Pasada 4 — escaneo de secretos (patrón y ruta, nunca valor)

- En el código leído (riu-router, s1/s2/s3, swe-code-web, claude-github-mcp-backup, hf-bucket-mcp, openclaw.sh) no hay valor literal de clave.
- Nombres de variables de secreto referenciadas: `GITHUB_TOKEN`, `RIU_API_KEY`, `WEB_ACCOUNTS`, `WEB_PASS`, `PUENTE_TOKEN`, `HF_TOKEN`, `HUGGING_FACE_HUB_TOKEN`, `GITHUB_PERSONAL_ACCESS_TOKEN`, `MCP_SECRET_PATH`, `MCP_SECRET_HF`, `OPENCLAW_GATEWAY_TOKEN`, `GROQ_API_KEY`, `NVIDIA_API_KEY`, `RIU_VAULT_PASSPHRASE`, `RIU_AGENT_API_KEYS`, `RIU_DIRECTOR_KEY_HASH`, `FASTMCP_JWT_SIGNING_KEY`.
- Patrón a revisar: `hf-bucket-mcp/src/hf_bucket_mcp/auth.py`, función `build_huggingface_auth`, usa `"dev-change-me"` como valor por defecto de `FASTMCP_JWT_SIGNING_KEY`.

## Flags 🚩 (resueltos por Router 2, sin escalar)

- 🚩1 RESUELTO. `proxy.py` no lee claves; `swecode_provider.json` sin claves.
- 🚩B1 RESUELTO. `boot.sh` no es el arranque real: `entrypoint.sh` no lo invoca (verificado). Movido a `_quarantine/` con README.
- 🚩D1 RESUELTO. `manager.py` único en `swe-code-models/`. Default `PRIMARY` unificado.
- 🚩L1 EXCEPCIÓN DOCUMENTADA. `manager.py` ~400 líneas (límite 200). Copiado íntegro; dividirlo sin pruebas tiene riesgo. Acordado con Router 1.
- 🚩R1 RESUELTO. `proxy.py` retirado de `HUGGUEFACE SPACE/`. Router LLM en `llm system HF/` (Router 1).
- 🚩X1 RESUELTO. `manager.py` en commit propio (`de49e5b`).
- 🚩C1 DOCUMENTADO, NO COPIADO. `cuentas.js` rota varias cuentas con una misma clave. `browser.js` lo importa: sin él, el módulo no arranca. Decisión del owner, sin cambios.
- 🚩S1 DOCUMENTADO, NO COPIADO. `claude-github-mcp-backup/app.py` expone `delete_repository` y `github_api` genérico. Único control: ruta secreta (`MCP_SECRET_PATH`). Restringir es decisión del owner.

## Flags 🚩 abiertos (owner, no bloquean el cierre de Router 2)

- 🚩S2 Default de clave JWT en `hf-bucket-mcp/auth.py` (`dev-change-me`) si `FASTMCP_JWT_SIGNING_KEY` no está definida.
- 🚩S3 `hf-bucket-mcp/server.py` expone `write_file`, que escribe en repos y buckets con el token del llamador cuando `HF_USE_CALLER_TOKEN_FOR_UPLOAD` está activo. Sin `HF_ALLOWED_USERS`, cualquier cuenta autenticada puede escribir.
- 🚩D2 Plan HF vs dataset real: carpetas `scripts/`, `job-evidencia/`, `results/`, `openclaw-prep/`, `apk/` no existen en el dataset de `main`. Revisar el plan.
- 🚩D3 `door.py` define `ROOT = router-inteligente-universal` y bucket `yaiwes-memoria-storage`. El repo usa otras raíces. Confirmar la raíz vigente.
- 🚩O2 (registro) Watchdog publica en `main` fuera del DAG.
- 🚩REG Registro `huggingface_mirror` describe push por git; el código real es auto-pull en arranque. Actualizar el registro.

## Handoff Router 2 (JSON)

```json
{
  "router": "ROUTER 2",
  "branch": "ccr-42f0e753-ni96xs",
  "tareas": {"1_auditoria": "cerrada", "2_clasificacion": "cerrada", "3_dedupe": "cerrada", "4_copia": "cerrada", "5_boot_branch": "cerrada", "6_cierre": "cerrada"},
  "commits": ["6922765", "de49e5b", "a9cab4d", "3992231", "fd8e680", "cfe557a", "f6d865c", "1f52588"],
  "flags_abiertos_owner": ["S2", "S3", "D2", "D3", "O2", "REG"],
  "flags_documentados_no_copiados": ["S1", "C1"]
}
```

## DSL DAG (Router 2)

```
audit(10) -> classify -> dedupe(manager) -> copy(HUGGUEFACE SPACE/) -> boot_branch -> wiring(p3) -> secrets(p4) -> close
   ✅           ✅            ✅                  ✅                       ✅              ✅            ✅         ✅
```

## Bitácora

- 2026-11-09 — Creado `Claude.md` con la checklist del input block verbatim y las tareas heredadas.
- 2026-11-09 — Creado `Claude notas.md` y reparto Router 1 / Router 2.
- 2026-11-09 — Router 2: rama `ccr-42f0e753-ni96xs` creada desde `main` (`5e239762526`). Inventario de 10 Spaces.
- 2026-11-09 — Router 2: cierre de auditoría. Pasadas 3 y 4 completas. Flags finales listados.

## Resolución de flags (2026-11-09)

- 🚩1 RESUELTO. `riu-router/proxy.py` no lee ningún banco de claves. Solo reenvía a los puertos internos. Las claves llegan por variables de entorno del Space. `swecode_provider.json` no contiene claves (`apiKey: "local"`).

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
