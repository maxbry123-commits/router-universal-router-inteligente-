# Router: 10 HTTP + 10 MCP conectadas

Generado el 2026-11-18. Router activo: `https://comand-center-1-space-grupo-1-router-mvp-1.hf.space` | Destino nuevo: `https://comand-center-1-router-universal-router-inteligente.hf.space`

Estado: **los 6 Spaces del router (2 grupos x 3) estan PAUSED** (HF 402, sin creditos prepago) + `hf-bucket-mcp` (infraestructura MCP, tambien PAUSED) -> las 10 rutas vivas devuelven **503**. El Space destino `router-universal-router-inteligente` esta **RUNNING** (static).
En codigo, las **10/10 rutas existen** (route table real del proxy, import real). Auth: `x-api-key` = `ROUTER_API_KEY` (banco cifrado `banco/vault.json`, clave `HF_VAULT_KEY`).

## Los 2 grupos de servidores en HF (compute + almacenamiento persistente)

| Grupo | Rol | Spaces (3) | Puerto | Compute |
|---|---|---|---|---|
| 1 · space grupo 1 router MVP 1 | compute (proxy Router MVP v1) | `space-grupo-1-router-mvp-1`, `space-grupo-1-router-mvp-1-v2`, `space-grupo-1-router-mvp-1-v7` | 7860 | Space docker · `cpu-upgrade` (32 GB RAM, CPU de pago) |
| 2 · space grupo 2 router LLM HF | LLM local GGUF | `space-grupo-2-router-llm-hf-1`, `space-grupo-2-router-llm-hf-2`, `space-grupo-2-router-llm-hf-3` | 7861 | Space docker · `cpu-upgrade` (32 GB RAM, CPU de pago) |

Renombrados en HF el 2026-11-18 (`move_repo`). Los nombres anteriores (`local-llm-router*`, `swe-code-s1/s2/s3`) ya no existen.

**Almacenamiento persistente, 2 capas**
1. `/data` — disco persistente de cada Space de pago: estado, checkpoints y cache de los GGUF.
2. `hf://buckets/COMAND-CENTER-1/yaiwes-memoria-storage` — memoria compartida por el MCP oficial de HF `hf-bucket-mcp` (`MCP_MEMORY_HTTP_URL`): banco cifrado, memoria de agentes y auditoria.

**Como se conectan los 2 grupos**
1. Solo entra el **Grupo 1** (proxy, 7860) desde router, chat, UI chat y openclaw.
2. El Grupo 1 elige el LLM del modo y llama por HTTPS al **Grupo 2** (7861); si no responde, cae a NVIDIA NIM y luego Groq.
3. El Grupo 2 devuelve la inferencia al Grupo 1; el Grupo 2 tambien llama al Grupo 1 con `ROUTER_BASE_URL` para reportar estado.
4. Los dos grupos escriben en su `/data` y comparten la memoria del bucket: un checkpoint escrito por uno lo ve el otro.
5. Las claves de proveedor **no** estan en HF Secrets: se hidratan del sello cifrado del repo (`fichas/fichas_qwen/sellos/proveedores.sello`) con `HF_VAULT_KEY`.

## Las 10 HTTP del router

| # | ID | Metodo | Ruta | En codigo | Probe vivo | Consumidores |
|---|---|---|---|---|---|---|
| 1 | router_health | GET | `/health` | OK | 503 | router (watchdog), UI chat (index.html: health strip) |
| 2 | control_status | GET | `/control-plane/status` | OK | 503 | router (control plane), UI chat, openclaw |
| 3 | chat_completions | POST | `/v1/chat/completions` | OK | 503 | chat (UI), openclaw, router (fallback chain) |
| 4 | nvidia_direct | POST | `/v1/nvidia` | OK | 503 | UI chat (model-selector.js), chat |
| 5 | groq_direct | POST | `/v1/groq` | OK | 503 | UI chat (model-selector.js), chat |
| 6 | swe_free | POST | `/v1/swe-free` | OK | 503 | UI chat (model-selector.js: swe_code_free), chat |
| 7 | team_qwe | POST | `/v1/team-qwe` | OK | 503 | UI chat (model-selector.js: team_qwe), openclaw |
| 8 | loop_start | POST | `/v1/loop/start` | OK | 503 | UI chat (ui/loop.js), router (loop engine) |
| 9 | frontend_chat | GET | `/chat/` | OK | 503 | UI chat (frontend estatico /chat) |
| 10 | billing_status | GET | `/billing/status` | OK | 503 | router (billing_monitor), UI (panel de coste) |

## Los 10 MCP del router

| # | ID | Auth | Env | En banco | Disponible | Consumidores |
|---|---|---|---|---|---|---|
| 1 | github | bearer | GITHUB_TOKEN | si | si | openclaw/hermes (agents), router (push/clone), chat (commits) |
| 2 | playwright | stdio | - | si | si | UI chat (navegacion), openclaw |
| 3 | context7 | api_key | CONTEXT7_API_KEY | no | NO | chat (documentacion), UI chat |
| 4 | supabase | oauth_pending | SUPABASE_TOKEN | no | NO | chat (persistencia), openclaw |
| 5 | notion | oauth_pending | NOTION_TOKEN | no | NO | chat (handoff/notas), openclaw |
| 6 | stripe | oauth_pending | STRIPE_TOKEN | no | NO | chat (pagos), openclaw |
| 7 | filesystem | stdio | - | si | si | router (fs_tools), chat, UI chat (ficheros) |
| 8 | sentry | oauth_pending | SENTRY_TOKEN | no | NO | router (observabilidad), UI chat |
| 9 | linear | oauth_pending | LINEAR_TOKEN | no | NO | openclaw (tareas), chat |
| 10 | firecrawl | api_key | FIRECRAWL_API_KEY | no | NO | chat (investigacion web), openclaw |

MCP de memoria (no es uno de los 10): `https://comand-center-1-hf-bucket-mcp.hf.space/mcp` -> bucket `COMAND-CENTER-1/yaiwes-memoria-storage`.

## En espera (se ejecutan cuando confirmes saldo)

| ID | Que | Bloqueo | Necesita | Ejecutable por mi |
|---|---|---|---|---|
| P1 | Reiniciar los 6 Spaces del router (2 grupos x 3) + hf-bucket-mcp (infraestructura MCP, no es un grupo del router) | HF 402: 'You must purchase pre-paid credits to host Spaces with paid hardware' | creditos prepago | si, con saldo confirmado por el owner |
| P2 | Convertir el Space destino en el runtime docker | HF 402: Docker en cpu-basic exige PRO | PRO | si, con PRO confirmado por el owner |
| P3 | Reconstruir los 12 datasets + LoRAs con Job de HF (si se quiere rehacer desde cero) | HF 402 en POST /api/jobs (creditos) | creditos prepago | si, con saldo; alternativa YA FUNCIONANDO y gratis: instalacion en local + push por git |
| P4 | Probar Groq de verdad desde un Space vivo | las 6 claves GROQ_KEYS devuelven 404 tambien desde HF; el egress del sandbox esta bloqueado por Cloudflare 1010 | claves Groq validas (owner) | si, con las claves nuevas del owner |
| P5 | Completar las credenciales de los 10 MCP | 7 de 10 sin credencial: context7, firecrawl (api_key) y supabase, notion, stripe, sentry, linear (oauth) | credenciales del owner (no saldo) | si, cuando el owner las aporte |
