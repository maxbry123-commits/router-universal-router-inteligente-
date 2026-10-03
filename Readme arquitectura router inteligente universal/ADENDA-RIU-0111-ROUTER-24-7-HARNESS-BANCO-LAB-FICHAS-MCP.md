# ADENDA RIU-0111 — Router 24/7, Harness por el Router, banco, laboratorio, fichas, MCP y puente HF (2026-10-03, Opus)

## En palabras simples
- Hay **un solo Router**. Corre en un procesador pagado de Hugging Face de 16 GB (Job CPU Basic, $0.01/h) que no se duerme.
- Como la direccion de un Job cambia cada vez que se relanza, el Space pagado `claude-github-mcp-backup` es la **puerta fija**: siempre la misma direccion y reenvia todo al Router vigente. El MCP de GitHub de ese Space sigue igual.
- Un **micro-kernel** dentro de la puerta revisa cada minuto: si faltan 20 min para que venza el Router, si falla 3 veces o si se pidio otro procesador, enciende el sucesor, espera que responda, cambia la direccion y recien apaga el anterior. Nunca queda sin Router.
- Si el Router pasa del 85% de CPU o RAM enciende mas procesadores (16 GB si es CPU, 32 GB si es memoria; hasta 10) y les manda trabajo; los de relevo se apagan a los 5 min sin uso.
- El **banco de secretos** se abre solo dentro del Router con la clave guardada como secreto del Space (nunca en GitHub). Una API nueva que se agregue al banco (y a `secret_bank/providers.json` en el bucket) entra sola, sin tocar codigo.
- El **Harness DeepSeek** usa el Router como proveedor (DeepSeek apagado) y la memoria como plugin.

## Direcciones (puerta fija)
Base: `https://comand-center-1-claude-github-mcp-backup.hf.space`
| Que | Ruta | Nota |
|---|---|---|
| OpenAI compatible (Harness, SDK, Hermes, OpenClaw) | `/v1/router` | model `auto`, un grupo, o `proveedor:modelo` (ej. `groq:qwen/qwen3.8-27b`); tools y SSE |
| MCP del Router | `/mcp/` | 13 herramientas: chat, catalogo, fichas, laboratorio, memoria, almacenamiento, computo HF |
| Fichas vivas | `/fichas`, `/fichas/catalog`, `/fichas/{id}`, `/fichas/{id}/run` | modos single, queue, parallel, council (juez); 1-20 modelos; espejo con `base_id` |
| Laboratorio | `POST /lab/run`, `GET /lab/last` | numera N01.., 3 pruebas por API, modelos disponibles, informe en SQLite y en bucket `lab/` |
| Banco | `/vault/status`, `POST /vault/autounlock` | nunca muestra valores |
| Memoria / almacenamiento | `/memoria/*`, `/chat/storage`, `/chat/storage/sync` | permanente en bucket `COMAND-CENTER-1/yaiwes-memoria-storage` |
| Puente HF | `/hf/status`, `/hf/models`, `/hf/datasets`, `/hf/datasets/file`, `/hf/skills`, `/hf/compute/run`, `/hf/compute/{id}`, `/hf/local/serve`, `/hf/hardware` | computo por Jobs; modelo guardado en HF servido en GPU como proveedor `local` |
| Pool elastico | `/control/hf/status`, `/control/hf/workers` | 85% -> enciende; 5 min sin uso -> apaga |
| Estado del kernel | `/door/status` | sin clave, sin secretos |
| Mini router L4/T4 | `/mini/v1` (model `t4`, `l4`, `t4:<repo>`, `l4:<repo>`), `/mini/status`, `/mini/config`, `/mini/approve`, `/mini/stop` | vive solo en HF; tope $5 por procesador con aprobacion |
Clave: `Authorization: Bearer <clave del Router>` o `X-API-Key`. Claves: secreto `RIU_AGENT_API_KEYS` (de Hy) y `RIU_AGENT_API_KEYS_2` (harness, guardada tambien en el banco como `router/harness-dsh`).

## Harness DeepSeek -> Router
```bash
MAXBRY_ROUTER_URL=https://comand-center-1-claude-github-mcp-backup.hf.space/v1/router \
MAXBRY_ROUTER_API_KEY=<clave del Router> DSH_TELEMETRY_MODE=DISABLED \
RIU_ROUTER_URL=https://comand-center-1-claude-github-mcp-backup.hf.space RIU_API_KEY=<clave del Router> \
dsh headless --patch 'chat router/deepseek-harness-chat/plugins/router-provider.cordis.yml' \
             --patch 'chat router/04-MEMORIA/plugin/harness-memoria.cordis.yml' "tarea"
```

## Donde vive cada cosa
| Pieza | Lugar |
|---|---|
| Codigo del Router | GitHub `router inteligente universal/integration/` (rama de trabajo) y bundle `code/router-bundle.tar.gz` en el bucket (lo que corre el Job) |
| Puerta + micro-kernel + mini router | Space HF `COMAND-CENTER-1/claude-github-mcp-backup`: `door.py`, `mini.py`, README |
| Registro del Router vigente | bucket `control/router-current.json`; bitacora del kernel `control/kernel-log.jsonl`; procesador pedido `control/router-desired.json` |
| Banco cifrado | bucket `claude-github-mcp-backup-storage/.../secret_bank/vault.db.gz.b64` (+ `providers.json`, + copias `.bak-*`) |
| Plugins del Harness | `chat router/deepseek-harness-chat/plugins/router-provider.cordis.yml`, `chat router/04-MEMORIA/plugin/` |

## Para cambiar el codigo del Router sin romper nada
1. Cambiar en GitHub y correr los tests. 2. Reconstruir el bundle (mismas carpetas que `code/router-bundle.json` registra) y subirlo al bucket. 3. `POST /hf/hardware {"flavor":"cpu-basic","relaunch_now":true}`: el kernel enciende el sucesor con el codigo nuevo y apaga el viejo.

## Estado verificado 2026-10-03 (laboratorio)
GitHub 5/5 OK; NVIDIA 5/5 OK; Groq 6/7 OK (groq-1 invalida); OpenAI 14 claves validas SIN SALDO (credit_balance_exhausted); HF tokens del banco `maxbry123` y `primary` invalidos (el token del entorno si funciona).

## Pendiente
- Recargar saldo OpenAI o quitar esas claves; renovar los 2 tokens HF del banco; borrar `groq-1`.
- Motores de memoria (Graphiti, Graphify, Memanto, AgentDB, FalkorDB, PostgreSQL): siguen como GAP (tarea de Sonnet).
- UI: los selectores de fichas, costo y aprobacion del mini router ya tienen sus rutas; falta dibujarlos en la interfaz.
