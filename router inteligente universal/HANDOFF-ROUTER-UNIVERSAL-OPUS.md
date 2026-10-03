# HANDOFF — Router Inteligente Universal (banco, laboratorio, memoria, HF) — Opus, 2026-10-03

Para Sonnet o cualquier agente. **No hace falta tocar el código del Router**: todo se conecta desde afuera.
Las claves NUNCA van en archivos ni en el chat: viven en el banco de secretos y en los secretos del Space.

## 1. En palabras simples
- Hay **un solo Router**. Corre 24/7 en un procesador pagado de Hugging Face de 16 GB (Job CPU Basic, 0,01 USD/h), que nunca duerme.
- La **puerta fija** es el Space pagado `COMAND-CENTER-1/claude-github-mcp-backup`, en `https://comand-center-1-claude-github-mcp-backup.hf.space`. Siempre tiene la misma dirección y reenvía todo al Router de turno. El MCP de GitHub de ese Space sigue igual.
- Un **micro-kernel** dentro de la puerta revisa cada minuto. Enciende un Router nuevo **20 minutos antes** de que venza el actual, o tras 3 fallos de salud, o si se pide otro procesador. Espera a que responda, cambia la dirección y solo entonces apaga el anterior.
- El **código** del Router viaja como paquete en el almacenamiento de HF (`code/router-bundle.tar.gz`), así que el Job no necesita GitHub.
- La **memoria** y los datos del Router se copian solos al almacenamiento permanente de HF, cada 60 s. Un Router nuevo los recupera al arrancar.

## 2. Ruta completa (verificada hoy en producción)
Harness DeepSeek → plugin MCP `memoria` → Router (por la puerta fija) → base local del Router → almacenamiento permanente HF (`COMAND-CENTER-1/yaiwes-memoria-storage`) → Router nuevo y vacío lo recupera.

## 3. Cómo se conecta cualquier cosa (sin tocar el Router)
| Qué | Cómo |
|---|---|
| Cualquier app tipo OpenAI | `base_url = <puerta>/v1/router`, `model = auto` (o grupo, o `proveedor:modelo`), clave del Router en `Authorization: Bearer` o `X-API-Key` |
| Agentes por MCP | `<puerta>/mcp/`, con la clave del Router. 13 herramientas: chat, catálogo, fichas, laboratorio, memoria, almacenamiento, cómputo HF |
| Harness DeepSeek | `dsh headless --patch 'chat router/deepseek-harness-chat/plugins/router-provider.cordis.yml' --patch 'chat router/04-MEMORIA/plugin/harness-memoria.cordis.yml' "tarea"`. Variables: `MAXBRY_ROUTER_URL=<puerta>/v1/router`, `MAXBRY_ROUTER_API_KEY`, `RIU_ROUTER_URL=<puerta>`, `RIU_API_KEY`, `DSH_TELEMETRY_MODE=DISABLED` |
| SSH | No existe en HF Jobs. Se cubre con HTTP + MCP |
| Enchufe universal Fables | Los módulos del Router están registrados como plugins: `yaiwes.router.banco`, `laboratorio`, `fichas_maestras`, `puente_hf`, `mcp`, `memoria`, `autoscale` (lista: `GET /chat/fichas`) |

## 4. Banco de secretos
- **Banco activo (único):** almacenamiento HF `claude-github-mcp-backup-storage/repos/router-universal-router-inteligente-/secret_bank/vault.db.gz.b64`, cifrado con la clave maestra del Director.
- **Copias:** `vault.db.gz.b64.bak-*`. Un banco viejo de otra clave está en `archivo-bancos-viejos/` (no se usa).
- **Al arrancar:** el Router lo descarga y lo abre solo (`/vault/autounlock`).
- **Contenido hoy (33 claves):** openai 14 · groq 6 (la groq-1 se borró por inválida) · github 5 · nvidia 5 · huggingface 2 · router 1.
- **API nueva:** se guarda la clave en el banco y su `base_url` en `secret_bank/providers.json`, y se relanza el Router con `POST /hf/hardware {"flavor":"cpu-basic","relaunch_now":true}` (el kernel cambia sin corte). El catálogo y las fichas la ven solos. Guía: `router inteligente universal/CONECTAR-SDK-NUEVO.md`.

## 5. Laboratorio
- **Rutas:** `POST /lab/run` (o la herramienta MCP `lab_run`); `GET /lab/last`.
- **Numeración:** cada API o SDK lleva un número (N01, N02…) y una huella. Nunca se muestra la clave.
- **3 pruebas por clave:** modelos disponibles, respuesta y herramientas. Estado: OK, PARCIAL o FALLA. Incluye la lista de modelos de cada API.
- **Registro:** tabla `lab_runs` en la base del Router (se copia a HF) y `lab/latest.json` en el almacenamiento HF.
- **Inventario de SDK:** openai, anthropic, groq, huggingface_hub, mcp y httpx están instalados en el Router.

## 6. Memoria
- **Plugin del harness:** `chat router/04-MEMORIA/plugin/memoria_mcp_server.py` (6 herramientas: health, save, load, search, estado y sync del almacenamiento).
- **Rutas del Router:** `/memoria/save|load|search|health`, `/chat/storage`, `/chat/storage/sync`. Las mismas funciones existen como herramientas MCP en `<puerta>/mcp/`.
- **Permanente:** `yaiwes-memoria-storage/riu-chat/riu_chat.sqlite3`, con copia automática cada 60 s y recuperación al arrancar.
- Los motores de memoria (graphiti, graphify, AgentDB) los conecta Sonnet en `chat router/04-MEMORIA/motores/`.

## 7. Fichas maestras vivas (control maestro)
- **Rutas:** `GET /fichas/catalog`, `POST /fichas`, `GET /fichas/{id}`, `POST /fichas/{id}/run`.
- **Modos:** single, cola, paralelo y consejo con juez. De 1 a 20 modelos por ficha, de cualquier API del banco o de modelos locales en HF.
- **Configuración:** system prompt de anclaje, plantilla y dataset de HF como texto de anclaje.
- **Espejo:** cada ficha nueva creada con `base_id` es un espejo de la anterior (versión + padre).
- **Catálogo vivo:** se actualiza solo cuando entra una API nueva al banco.

## 8. Puente Hugging Face
| Ruta | Para qué |
|---|---|
| `/hf/status` | Cuenta, Router actual, registro |
| `/hf/hardware` | Cambiar el procesador del Router a distancia (el kernel lo relanza) |
| `/hf/models`, `/hf/local/serve` | Modelos guardados en HF; servir uno con vLLM en GPU y enchufarlo como proveedor `local` |
| `/hf/datasets`, `/hf/datasets/file` | Puente con los datasets |
| `/hf/skills` | Biblioteca de skills de HF |
| `/hf/compute/run`, `/hf/compute/{id}?logs=40`, `DELETE /hf/compute/{id}` | Cómputo pagado para cualquier cosa conectada, con registros |

Todos los Jobs se crean en la org `COMAND-CENTER-1`.

## 9. Más cómputo automático (autoscale)
- **Cuándo:** si el Router pasa del 85 % de CPU o RAM durante 30 s, enciende un procesador de relevo. Con presión de RAM usa uno de 32 GB (cpu-upgrade); con presión de CPU, uno de 16 GB. Hasta 10.
- **Apagado:** los relevos se apagan tras 5 min sin uso. El Router principal nunca se apaga.
- **Arreglo de hoy:** se mide el contenedor del Router (no la máquina de HF) y hay 3 min de gracia al arrancar. Antes encendía relevos sin carga.
- **Estado:** `GET /control/hf/status`.

## 10. Router de respaldo (solo en HF, no en GitHub)
- **Dónde:** dentro de la puerta fija, en `<puerta>/mini/...`. Ver su handoff aparte: `secret_bank/LEEME-HANDOFF.md` en el almacenamiento HF y la sección "Router" del README del Space.

## 11. Índice de guías
- `Readme arquitectura router inteligente universal/ADENDA-RIU-0111-ROUTER-24-7-HARNESS-BANCO-LAB-FICHAS-MCP.md` — guía completa
- `router inteligente universal/HANDOFF-CABLEADO.md` y `README.md` — apuntan aquí
- `router inteligente universal/CONECTAR-ROUTER.md` — conectar otros repos o herramientas
- `router inteligente universal/CONECTAR-SDK-NUEVO.md` — meter una API o SDK nueva en el banco
- `router inteligente universal/Banco de claves/README.md` — banco de secretos
- `chat router/deepseek-harness-chat/plugins/router-provider.cordis.yml` — harness → Router (sin DeepSeek API)
- `chat router/04-MEMORIA/plugin/` — plugin de memoria del harness
- `chat router/11-EVIDENCIA/equipos/EQUIPO-1/S1-30-…md`, `S1-31-…md` — evidencias
- HF Space `claude-github-mcp-backup`: `door.py` (puerta + kernel), `mini.py` (respaldo T4/L4), README sección Router

## 12. Estado verificado (2026-10-03, noche)
- **OpenAI:** las 14 claves son válidas (ven 127 modelos), pero responden "credit_balance_exhausted" (sin saldo). Se confirmó también con el SDK oficial.
- **Groq:** 6 de 6 responden. La groq-1 se borró del banco (era inválida).
- **NVIDIA:** 5 de 5 válidas. En 2 de ellas el modelo devolvió vacío en la prueba de herramientas; es el modelo, no la clave.
- **HF:** los 2 tokens guardados dentro del banco son inválidos (401). El token propio del Router sí funciona.
- **Harness → memoria → Router → HF → reinicio:** OK.
- **MCP por la puerta:** OK (13 herramientas; sin clave responde 401).
- **Kernel:** OK (LAUNCH → SWITCH → CANCEL).
- **Mini T4:** OK (0,10 USD gastados de 5).
- **Pruebas del código:** 332 pasan. Las 11 que fallan ya fallaban antes de estos cambios (les faltan archivos en esta copia parcial).

## 13. Pendiente del Director (no es código)
- Cargar saldo en OpenAI.
- Crear tokens HF nuevos para el banco.
- Revocar y cambiar los tokens de GitHub y HF que se usaron en las sesiones.
