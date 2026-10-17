# ESTADO-BACKEND — Chat BOTS (lo lee el agente de frontend para dibujar el avance)

Actualizado: 17-oct-2026 01:15, hora Bogotá (UTC-5). Rama: [`wip/chatbots-backend-mvp`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/tree/wip/chatbots-backend-mvp) (desde `main` `529b680b0e`). **No está en main.**

Estados: **hecho** = en main y probado · **en curso** = código en rama, falta prueba / revisión ×3 / Android · **pendiente** = sin código.

## 1. Fuente para el diagrama (Archify)

- El backend entrega el diagrama ya armado: `POST /plugins/orquestador/call/arquitectura` → `{archify, diagrama, piezas}`.
- `diagrama` = JSON Archify `schema_version: 1`, `diagram_type: architecture` (`components` con `type` frontend/backend/database/cloud/security/external, `row`/`col`, `tag` = estado; `connections` con `variant`). `piezas` = `[{id, nombre, estado}]`.
- Archify: https://github.com/tt-a1i/archify (MIT, commit `88d1ae4498`). Skill de agente: `npx skills add tt-a1i/archify -g`. Render: `node bin/archify.mjs validate|render architecture <json>` → HTML con SVG. **Lo descarga y renderiza el frontend** (la computadora del bot solo sirve para frontend). Validación del JSON con el validador de Archify: **por confirmar** (no corrida).
- Archivo fuente del estado: [`plugins/orquestador/arquitectura.py`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/wip/chatbots-backend-mvp/router%20inteligente%20universal/plugins/orquestador/arquitectura.py) (`PIEZAS`). El backend lo actualiza en cada commit.

## 2. Componentes cableados

| Pieza (id diagrama) | Archivo | Estado | Desde (Bogotá) |
|---|---|---|---|
| Chat BOTS pestaña (`ui`) | `chat router/chat frontend/orquestador.js` (rama `orquestador-agentes-rebase`, del frontend) | en curso | 16-oct 22:51 |
| Ventana arquitectura (`info`) | frontend: consume `arquitectura` | pendiente | — |
| Plugin orquestador (`orq`) | `plugins/orquestador/plugin.py`, `ficha.json` 0.3.0 | en curso | 17-oct 01:02 |
| Gobierno determinista (`gob`) | `plugins/orquestador/gobierno.py` | en curso | 17-oct 01:02 |
| Mirror por enlace (`mirror`) | `plugins/orquestador/mirror_repos.py` | en curso | 17-oct 01:02 |
| Sandbox (`sbx`) | `plugins/orquestador/sandbox.py` (sin cambios) | en curso | 16-oct 22:51 |
| HARNESS puente_chat (`harness`) | `plugins/puente_chat/` (+ tool `crear_agente`, `capacidad.py`) | hecho (harness) / en curso (tool) | 17-oct 01:02 |
| FICHA 4 + MODELO (`ficha`, `modelo`) | sin cambios | hecho | — |
| memoria_yaiwes SQLite (`mem`) · Graphiti/Graphify (`graf`) · bucket (`bucket`) | sin cambios; se usa la fachada `_mem().save` | hecho | — |
| Repos de agentes (`repos`) | `maxbry123-commits/openclaw`, `maxbry123-commits/hermes-agent`, `Agentes-motores-Wordflow-YAIWES` (por enlace) | hecho (existen) | — |

Ruta intacta: `orquestador.js → POST /plugins/orquestador/call/<acción> → plugin → HTTP puente_chat chat_async/resultado → FICHA → MODELO`.

## 3. Endpoints (`POST /plugins/orquestador/call/<acción>`)

| Acción | Entrada | Salida | Estado |
|---|---|---|---|
| `status` | — | memoria, sandbox, deploy, `gobierno {watchdog_timeout_s: 180, loop_duplicados: 2}` | en curso |
| `listar`, `crear`, `borrar`, `enviar`, `estado`, `aprobar`, `configurar`, `subir`, `archivos`, `ejecutar`, `chat_crear`, `token_guardar`, `deploy`, `modelos` | como en v2 (README §3.2) | — | en curso |
| `crear` / `configurar` + `objetivo` | `objetivo` (texto) | GOAL LOCK; cambiarlo sin `confirmado:true` → `OBJETIVO_BLOQUEADO` | en curso |
| `mirror` | `de: "repo:<agent_id>"` (además de `chat` / id) | agente con `repo {agent_id, nombre, url}`; **no copia código** | en curso |
| `agentes_repo` | — | `[{agent_id, nombre, repo, ruta, roles, url}]` (OpenClaw, Hermes + registro de la flota leído por llamada) | en curso |
| `repo_leer` | `agent_id`, `ruta` (README.md por defecto) | texto ≤12 000 caracteres, leído por llamada, no se guarda | en curso |
| `vigilar` | `seccion` (opcional) | `{revisadas, recuperados}`: `trabajando` > 180 s → `error` `FAIL_TIMEOUT` | en curso |
| `reiniciar` | `id` | agente a `activo` (suelta proceso) | en curso |
| `recibos` | `id` | últimos 20 recibos encadenados por hash + `objetivo_intacto` | en curso |
| `arquitectura` | — | JSON Archify + estado por pieza (§1) | en curso |

Campos nuevos en la vista del agente: `objetivo`, `fallo` (`FAIL_TIMEOUT`, `FAIL_MODEL`, `FAIL_TOOL`, `FAIL_NETWORK`, `FAIL_DEPENDENCY`, `FAIL_PERMISSION`), `repo`.

## 4. Pruebas

| Prueba | Dónde | Resultado |
|---|---|---|
| `router inteligente universal/tests/test_orquestador_mvp.py` (7 tests: goal lock + recibos, loop, watchdog + reiniciar, redacción, mirror por enlace, Archify, ficha) | GitHub Actions `riu-chatbots-backend-verify.yml` | **no corrió**: «account is locked due to a billing issue» (run [39008450153](https://github.com/maxbry123-commits/router-universal-router-inteligente-/actions/runs/39008450153), 17-oct 01:02) |
| Sintaxis (`ast.parse`) de los 7 `.py` | box (solo análisis estático, sin ejecutar backend) | OK |
| Space / Android 412 px 4G | — | pendiente (falta `HF_TOKEN` en el entorno para el deploy) |

## 5. Bitácora (Bogotá)

| Hora | Qué |
|---|---|
| 17-oct 01:02 | Rama creada desde `main` `529b680b0e`; commit 1/3 código MVP `64bd84ab66` |
| 17-oct 01:02 | CI bloqueado por facturación de GitHub Actions |
| 17-oct 01:15 | Commit 2/3 docs (este archivo, README arquitectura, HANDOFF, TAREAS/03) |
