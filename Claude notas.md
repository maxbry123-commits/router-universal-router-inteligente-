# Claude notas.md — Pizarra de trabajo (Crazy Wall)

Estado: 2026-11-09 · Fuente de tareas: `Claude.md` · Verbatim: `kernel/INPUT_BLOCK_YAIWES_CABLEADO.md`

## Reparto de trabajo (para que no se pisen)

| Router | Responsable | Carpetas que toca |
|---|---|---|
| Router 1 | Claude Code (chat actual) | `ROUTER MVP v1/` y `llm system HF/` · rama `ccr-f01c3de9-bmry0s` |
| Router 2 | Claude Code ROUTER 2 | `HUGGUEFACE SPACE/` (código) y esta notas · rama `ccr-42f0e753-ni96xs` (creada desde `main`) |
| Compartido, solo lectura para los dos | — | `SATÉLITE CENTRAL CONECCION` (`connections/`), `_quarantine/`, `Claude.md`, esta notas |

Regla: Router 2 hace `git pull --rebase origin main` antes de cada push a `main`. Nunca escribe en `llm system HF/` ni en `ROUTER MVP v1/`.

## Estado por tarea (Router 2)

| # | Tarea | Estado | Evidencia |
|---|---|---|---|
| 1 | Auditoría 4 pasadas (10 Spaces) | 🟡 pasadas 1-2 hechas en 6 Spaces; pasada 3 y 4 en curso | Inventario `hf_fs find`; lectura de código ver abajo |
| 2 | Clasificación de cada archivo | 🟡 parcial (tabla abajo) | Esta notas |
| 3 | Fusionar duplicados s1/s2/s3 | 🟡 análisis hecho; copia única pendiente en commit separado | `manager.py` idéntico salvo default `PRIMARY` (ver flags) |
| 4 | Copiar código a `HUGGUEFACE SPACE/<space>/` | 🟡 parcial | Commit `6922765390c01a3f88a10ee5d48933f1f12ded99` en `ccr-42f0e753-ni96xs`: `scaler.py`, `fetch_models.py`, `proxy.py`, `boot.sh` |
| 5 | Corregir rama de arranque en `boot.sh` | ✅ en código; ⚠️ ver flag 🚩B1 | `HUGGUEFACE SPACE/riu-router/boot.sh` usa `GITHUB_BRANCH` (default `ccr-f01c3de9-bmry0s`) |
| 6 | Cerrar lista | ⬜ | Al final del loop |

## Hallazgos de la pasada 1-2 (inventario y lectura)

- **Spaces auditados (10):** `swe-code-s1`, `swe-code-s2`, `swe-code-s3`, `riu-router`, `swe-code-web` (privado), `claude-github-mcp-backup`, `local-llm-router`, `local-llm-router-v2`, `local-llm-router-v7`, `hf-bucket-mcp`. Los cuatro últimos: inventario y clasificación, sin copia.
- **Secretos (pasada 4, parcial):** en el código leído no aparece ningún valor literal de clave. Todas las credenciales se leen de variables de entorno (`GITHUB_TOKEN`, `RIU_API_KEY`, `WEB_ACCOUNTS`, `WEB_PASS`, `PUENTE_TOKEN`, `HF_TOKEN`, `GITHUB_PERSONAL_ACCESS_TOKEN`, `MCP_SECRET_PATH`, `MCP_SECRET_HF`). Reportado solo por patrón y ruta, nunca valor.
- **Cableado:** `riu-router/entrypoint.sh` (el que ejecuta el Dockerfile) clona `ccr-f01c3de9-bmry0s` y arranca `ROUTER MVP v1/system_prompt_py/openai_compatible_proxy`. `boot.sh` no es invocado por el Dockerfile: es código muerto en el Space.
- **s1/s2/s3:** `entrypoint.sh` de s1 clona el repo en tiempo de arranque y ejecuta `llm system HF/download_model.py` y `llm system HF/manager.py` (código de Router 1). Los `manager.py` locales de s1 no se ejecutan. s2 y s3 sí ejecutan su copia local, vía Dockerfile.

## Clasificación (Router 2)

| Elemento | Destino | Motivo |
|---|---|---|
| GGUF y adaptadores (datasets) | Se queda en HF | Binarios grandes |
| Bucket `yaiwes-memoria-storage` | Se queda en HF | Almacenamiento |
| `Dockerfile`, `README.md`, `entrypoint.sh` de cada Space | Se queda en HF | Cascarón mínimo |
| `manager.py` (s1/s2/s3) | `HUGGUEFACE SPACE/swe-code-models/manager.py` (una copia) | Duplicado; pendiente de commit |
| `scaler.py`, `fetch_models.py` | `HUGGUEFACE SPACE/swe-code-models/` | Duplicados; copiados |
| `riu-router/proxy.py` | `HUGGUEFACE SPACE/riu-router/proxy.py` | Copiado. 🚩 Según el plan iría a `llm system HF`; Router 2 no escribe ahí |
| `riu-router/swecode_provider.json` | Pendiente | Sin claves (`apiKey: "local"`). Copiar en el siguiente commit |
| `riu-router/boot.sh` | `HUGGUEFACE SPACE/riu-router/boot.sh` (corregido) | Copiado con `GITHUB_BRANCH` |
| `riu-router/openclaw.sh` | Pendiente de lectura | 12 KB, no leído |
| `swe-code-web/src/*` (8 archivos) | Pendiente de copia | 🚩C1 (ver abajo) |
| `claude-github-mcp-backup/app.py` | Cableado (MCP público), no copiar | 🚩S1 (ver abajo) |
| `claude-github-mcp-backup/fleet.py` | Pendiente de decisión | Flota de replicas; cableado de router |
| `claude-github-mcp-backup/door.py`, `mini.py` | Pendiente de lectura | No leídos |
| `hf-bucket-mcp/src/*` | Pendiente de lectura | No leídos |
| `local-llm-router*` (3) | Inventario, sin copia | Fuera del plan de copia |

## Flags 🚩

- 🚩1 RESUELTO (pasada 2). `riu-router/proxy.py` no lee ningún banco de claves; solo reenvía. `swecode_provider.json` no tiene claves.
- 🚩B1 BLOQUEANTE MENOR. `boot.sh` no es el arranque real: el Dockerfile ejecuta `entrypoint.sh`, que ya usa `ccr-f01c3de9-bmry0s`. La corrección de `boot.sh` queda documentada y no afecta al despliegue. Además, la lista de exclusiones en `boot.sh` no coincide con la de esta notas: `boot.sh` excluye `chat-router/agentes/{agentes-listos,frameworks,investigacion}/`, no `chat-router/agentes/*`.
- 🚩D1 DUPLICADO CON DIFERENCIA. `manager.py` en s1/s2/s3: el código es idéntico salvo el default de `PRIMARY` (`qwen2.5-coder-0.5b` / `lfm2.5-350m` / `qwen3.5-0.8b`) y un comentario. Cada entrypoint fija `PRIMARY_MODEL`, así que el default se unifica a `qwen2.5-coder-0.5b`. La copia única aún no está en GitHub. No se pudo verificar por hash: la sandbox bloquea `huggingface.co`.
- 🚩L1 LÍMITE DE 200 LÍNEAS. `manager.py` tiene ~400 líneas. Dividirlo sin poder ejecutarlo tiene riesgo. Se copia íntegro y se deja como excepción documentada hasta que Router 1 o el owner decidan.
- 🚩C1 CUENTAS WEB. `swe-code-web/src/cuentas.js` rota entre varios correos con una misma clave (`WEB_ACCOUNTS`, `WEB_PASS`) para reautenticar sesiones de sitios de chat de terceros con Playwright. Requiere revisión del owner antes de copiarlo o reubicarlo. Router 2 no lo copia en esta pasada.
- 🚩S1 MCP PÚBLICO. `claude-github-mcp-backup/app.py` expone herramientas que borran repositorios (`delete_repository`) y un `github_api` genérico con el PAT. El único control es la ruta secreta (`MCP_SECRET_PATH`, mínimo 20 caracteres) y no hay autenticación a nivel MCP. Es cableado de comunicación: no se copia a `HUGGUEFACE SPACE/`. Requiere decisión del owner.
- 🚩R1 DIRECTORIO DE ROUTER 1. El plan pide mover `proxy.py` y `manager.py` a `llm system HF/`, pero esa carpeta es de Router 1. Router 2 deja las copias en `HUGGUEFACE SPACE/` y Router 1 decide si las reubica.
- 🚩X1 LÍMITE DE TAMAÑO. `manager.py` (20 KB) y `proxy.py` (10 KB) no caben en un solo `push_files` junto con el resto sin riesgo. `manager.py` queda pendiente de un commit propio.

## Preguntas para el owner

1. ¿Autorizas mover `cuentas.js` y la rotación de cuentas web fuera de `swe-code-web`, o prefieres que quede como está y documentado?
2. ¿Qué hacemos con `app.py` (MCP público con `delete_repository`)? ¿Lo restringimos o lo dejamos como está?
3. ¿Cuándo se autoriza el borrado en Hugging Face (lo ejecuta MiniMax)?

## Handoff Router 2 (JSON)

```json
{
  "router": "ROUTER 2",
  "branch": "ccr-42f0e753-ni96xs",
  "commit_codigo": "6922765390c01a3f88a10ee5d48933f1f12ded99",
  "tareas": {
    "1_auditoria": "parcial: pasadas 1-2 completas en 6 Spaces de copia; pasada 3 y 4 en curso",
    "2_clasificacion": "parcial",
    "3_dedupe": "analisis listo; manager.py unico pendiente",
    "4_copia": "parcial: scaler, fetch_models, proxy, boot",
    "5_boot_branch": "hecho en codigo; boot.sh no es el arranque real",
    "6_cierre": "pendiente"
  },
  "flags_abiertos": ["D1", "L1", "C1", "S1", "R1", "X1", "B1"],
  "pendiente_siguiente_commit": [
    "HUGGUEFACE SPACE/swe-code-models/manager.py (unico)",
    "HUGGUEFACE SPACE/riu-router/swecode_provider.json",
    "HUGGUEFACE SPACE/swe-code-web/src/* (tras decision C1)",
    "lectura de openclaw.sh, door.py, mini.py, hf-bucket-mcp/src/*"
  ]
}
```

## DSL DAG (Router 2)

```
audit(10 spaces) -> classify -> dedupe(manager) -> copy(HUGGUEFACE SPACE/) -> boot_branch -> close
   ✅ inventario     🟡 parcial    🟡 analisis        🟡 parcial              ✅ codigo       ⬜
```

## Bitácora

- 2026-11-09 — Creado `Claude.md` con la checklist del input block verbatim (secciones 2 a 6) y las tareas heredadas.
- 2026-11-09 — Creado `Claude notas.md` (esta pizarra) y el reparto de trabajo entre Router 1 y Router 2.
- 2026-11-09 — Plan de Hugging Face como borrador, a la espera de la auditoría de 4 pasadas.
- 2026-11-09 — Router 2: rama `ccr-42f0e753-ni96xs` creada desde `main` (`5e239762526`). Inventario de 10 Spaces. Commit de código `6922765` con scaler, fetch_models, proxy y boot.
- 2026-11-09 — Router 2: flags 🚩D1, 🚩L1, 🚩C1, 🚩S1, 🚩R1, 🚩X1, 🚩B1 abiertos.

## Resolución de flags (2026-11-09)

- 🚩1 RESUELTO. `riu-router/proxy.py` no lee ningún banco de claves. Solo reenvía a los puertos internos. Las claves llegan por variables de entorno del Space. `swecode_provider.json` no contiene claves (`apiKey: "local"`).
