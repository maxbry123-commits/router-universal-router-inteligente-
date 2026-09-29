# HANDOFF — PARCHE DE RECUPERACIÓN (Router Inteligente Universal + Chat) — 2026-09-21

Este archivo es público: NO contiene claves, contraseñas ni correos. Las claves se nombran por su `credential_ref` del banco.
Escrito por Claude a pedido del Director (Max). Instrucciones textuales en `INPUT-VERBATIM-2026-09-2*.md` (misma carpeta).
Complemento técnico: `../Readme arquitectura router inteligente universal/ARQUITECTURA-ROUTER-Y-CONEXIONES.md`.

## 1. Quién manda y cómo se trabaja (reglas del Director, vigentes)
1. El Director (Max) decide. Claude es el cerebro/orquestador: planifica y delega; los modelos ejecutan.
2. Anota cada instrucción del Director TEXTUAL (1 a 1) en `Claude notas/` y en la carpeta de bitácora ANTES de ejecutar, y valida que quedó anotada. Una instrucción nueva espera a que termine lo que está en curso. Lo que no se pueda resolver es un GAP, nunca se inventa.
3. Respuestas al Director: cortas, simples, sin jerga ("respondió 200" no le dice nada). Habla como a una persona.
4. No esperes más de ~1 minuto tras un commit/push/run: sigue con la siguiente tarea, revisa el resultado al final y, si no está, para y pide el OK. En "modo loop": no parar ni escalar; planificar y medir el tiempo.
5. Delegar SIEMPRE con DSL DAG determinista (`DSL-FABLES-yaiwes-node-executor-xray-v2.md`, o un JSON corto `riu.dag/v1` para tareas triviales). El PASS sale de comprobaciones deterministas, nunca de que el modelo lo diga.
6. Claves: NUNCA pedirlas, copiarlas ni escribirlas en archivos/chat. Solo por el banco. "GitHub Secrets es horrible": no añadir más ahí.
7. Solo se escribe en el repo `maxbry123-commits/router-universal-router-inteligente-` (otros repos, como `agentes`, solo lectura).
8. Modelos: NVIDIA es el proveedor principal; MiniMax para código; DeepSeek para tareas menores; en hora pico de DeepSeek, solo MiniMax. Si NVIDIA falla, avisar al Director (él autoriza el cambio), salvo donde la política ya lo autoriza (ver §6).

## 2. Estado real (2026-09-21) — verificado vs no verificado
Código (todo bajo `router inteligente universal/integration/chat_mvp/`): `app.py`, `router.py` (API del chat), `core.py`, `resilience.py`, `route_api.py`, `providers.py`, `github_tools.py`, `store.py` (SQL+grafo+caché+documentos), `usage.py`, `dag.py`, `dag_cli.py`, `jobs.py`, `wordflow_agents.py`, `vault_bridge.py`, `vault_api.py`, `vault_hook.py`, `chat_ui.html`; y en `integration/huggingface/`: `fastapi_gateway.py`, `chat_catalog.py`, `chat_executor.py`, `keystore_auth.py`, `api_key_auth.py`, `router_hot_path.py`.
Evidencia en runner de GitHub:
- Verify completo: 57 passed (run `35523915544`); Kimi K3, DeepSeek V4 Flash/Pro y MiniMax M3 respondieron por el chat y el Router; documento adjunto, modo con agente, caché, historial y cuentas GitHub OK.
- DAG `ORDER-000-smoke` PASS con 3 modelos (`chat_orders/results/ORDER-000-smoke.result.json`).
- Pruebas NVIDIA por clave/modelo (run `35528298793`) y pool de claves (21 passed, run `35528394972`).
- Banco/fleet/jobs: 29 passed, 1 failed (run `35530261916`; el fallo era el ORDEN de las claves del banco, corregido en `0fa2c51`). Resiliencia del Router (`resilience.py`, `test_resilience.py`): probada localmente; su corrida en runner está LANZADA y NO leída.
NO verificado / no hecho: chat abierto en un navegador real; publicado en un servidor; prueba de modelos dentro del Job de Hugging Face (el Job dio ERROR sin log: `riu-hf-job-models.yml`); benchmark de modelos locales (Nanbeige/Qwen 9B); Graphiti real.

## 3. Cómo conectar las APIs (todas OpenAI-compatibles: `POST {base}/chat/completions`, `GET {base}/models`, `Authorization: Bearer <clave>`)
| Proveedor (id en el código) | Base URL | Estado / evidencia |
|---|---|---|
| `nvidia` (principal) | `https://integrate.api.nvidia.com/v1` | 5 claves autentican (82 modelos). `nvidia/nemotron-3-super-120b-a12b` responde (claves 3, 4, 5; 1 y 2 dieron 503). `deepseek-ai/deepseek-v4-flash-0731` responde de a una petición; con 10 a la vez se agota el tiempo. `moonshotai/kimi-k3` y `z-ai/glm-5.3-flash` se agotan con carga. `moonshotai/kimi-k2.6` no existe (404). `minimaxai/minimax-m2.7` retirado (410). |
| `hf` (router de Hugging Face) | `https://router.huggingface.co/v1` | Funciona con la cuenta `COMAND-CENTER-1` (con método de pago, no PRO): `moonshotai/Kimi-K3`, `deepseek-ai/DeepSeek-V4-Flash`, `deepseek-ai/DeepSeek-V4-Pro`, `MiniMaxAI/MiniMax-M3`. Los modelos no certificados solo se intentan con `RIU_CHAT_ALLOW_PROVIDER_LIVE=1` y salen como `certified:false`. |
| `cerebras` | `https://api.cerebras.ai/v1` | Autentica pero responde 402 (falta facturación). |
| `groq`, `deepseek`, `moonshot`, `minimax` (APIs directas) | ver `providers.py` | Sin claves todavía. DeepSeek y Moonshot tienen caché de contexto nativa (más barato). |
| `local` | `RIU_LOCAL_BASE_URL` | Listo en código, sin URL: no hay servidor local (contrato: solo inferencia remota). |
Modelos a probar que pidió el Director: DeepSeek V4, Kimi K3, Kimi K2.6, GLM, MiniMax — solo los disponibles (ver tabla).

## 4. Qué clave usar (por `credential_ref`, nunca el valor)
- Banco maestro (12 claves): `huggingface/primary`, `huggingface/maxbry123`, `nvidia/digi-maxbry`, `nvidia/digi-briseida` (inestable, va última), `nvidia/movistar-briseida`, `nvidia/wow-maxbry`, `nvidia/wow-brisa`, `github/maxbry123` (repo principal), `github/maxbry123-classic-1`, `github/maxbry123-classic-2`, `github/planeta123` (nuevo, sin probar), `github/abc1tienda-web` (nuevo, sin probar). Cerebras no está en el banco.
- NVIDIA: pool de 4 (`digi-maxbry`, `movistar-briseida`, `wow-maxbry`, `wow-brisa`); el Router prueba primero la clave más sana y cae a la siguiente.
- Kimi K3 / DeepSeek V4 / MiniMax M3: por `hf` con `huggingface/primary` (cobra a `COMAND-CENTER-1`).
- GitHub: escribir con la cuenta que indique el Director (selector en el chat): `github/maxbry123` para este repo.
- Dónde vive el banco: fuera del repo, en el almacenamiento privado de Hugging Face de `COMAND-CENTER-1` (espacio del MCP `GitHub_Backup_HF`, ruta `secret_bank/vault.db.gz.b64`). La contraseña maestra la tiene SOLO el Director. Otro equipo recibe un banco APARTE con las claves mínimas (kit: `KIT-EQUIPO-NVIDIA/`); nunca el maestro.
- Uso: abrir el banco con la contraseña en `/vault` del chat (queda solo en memoria, 1 h); las claves del banco entran primero al pool de cada proveedor y los tokens GitHub aparecen en el selector. Ver `BANCO-SECRETO-README.md`.
- Las claves que se pegaron en el chat quedaron expuestas: recomendar al Director rotarlas.

## 5. Cómo está hecho el Router (resumen; detalle en la arquitectura)
`Cliente/agente (API key MAXBRY-001..100 o RIU_AGENT_API_KEYS) → FastAPI → Enchufe Gate → RedUniversal → ejecutor del proveedor`, siempre por el hot-path certificado. Encima de eso: caché de respuestas (por defecto), prefijo estable de prompt, presupuesto de historial, registro de tokens/costo (`/chat/usage`), DAG (`/chat/dag/run`), trabajos en paralelo por agente con commit real a GitHub (`/chat/jobs/run`), enrutado por políticas (`/chat/route`, `/chat/router/status`), banco (`/vault/*`).
Para agregar un proveedor: añadirlo en `PROVIDERS` (`providers.py`, con sus nombres de variable), en `PROVIDER_MAP` (`vault_bridge.py`) y en una cadena de `DEFAULT_POLICY` (`resilience.py`); añadir pruebas.

## 6. Picos y problemas → respuesta del Router (`resilience.py`)
- NVIDIA lenta con carga → concurrencia adaptativa 3 → 10 espacios y, si sigue saturado, error rápido `ROUTER_SATURATED` (no se cuelga).
- Una clave lenta/caída (timeout, 401/402/403/429, 5xx) → cortacircuitos por clave (3 fallos → 120 s fuera) y orden de la más sana a la menos sana. Errores de petición (400/404/410/422) no cambian de clave.
- Hora pico de DeepSeek (01-04 y 06-10 UTC, lunes a viernes; fuente `Chat Mvp/router_policy/peak.py`) → en `minor`, solo MiniMax; DeepSeek se omite.
- Cadenas por grupo (regla del Director para el grupo 2: NVIDIA → Cerebras → API local → DeepSeek V4 Flash): `g2`, `code` (MiniMax → NVIDIA), `minor` (DeepSeek → NVIDIA → MiniMax) TIENEN respaldo autorizado. `default` NO cae a otro proveedor: responde `NEEDS_DIRECTOR_AUTH` (HTTP 409) para que Claude avise al Director.
- Los proveedores sin clave/modelo configurado se omiten y se anotan en el `trace` de la respuesta.

## 7. Agentes y trabajo en paralelo
- 14 agentes espejo del fleet Wordflow LOOP Yaiwes (`wf-opencode`, `wf-openhands`, `wf-openclaw`, `wf-claude-code`, `wf-mimo-code`, `wf-codex`, `wf-hermes`, `wf-aider`, `wf-muse-glimmer`, `wf-kimi-k-code`, `wf-smolagents`, `wf-qwen-code`, `wf-cline`, `wf-goose`) + `orquestador-g0` y `seals-team-yaiwes-001`. Es un espejo de ROLES (personas con el contrato executor); no ejecuta los binarios de OpenHands/Aider/etc.
- `/chat/jobs/run`: N trabajos en paralelo (tope 8), cada uno = un agente + un modelo + commit opcional a una cuenta GitHub. Solo se confirma en GitHub un resultado con `PASS` (o sin `expect` si el trabajo lo permite expresamente).
- Pool de agentes Seals Team YAIWES (50+): el Director dará la lista; router por grupos 0/1/2 completo: pendiente (base en `Chat Mvp/groups.yaml`).
- Enchufe Universal de Fables (adjuntos del 2026-09-20): parte 2 (`ficha_contract_v2`) pasa sus pruebas; parte 1 (bus) pasa las pruebas 1-5 y falla la 6 por un defecto de su propia prueba (falta `activacion` en la ficha). No integrados. `MAX-SYSTEM-100X`, `MAVIS-PARALLEL-100X` y el JSON DSL del enchufe: sin leer a fondo.

## 8. GAPs abiertos (en este orden de utilidad)
1. Publicar el chat: Hugging Face exige PRO para Spaces Docker; el Codespace `riu-chat-mvp-…` se quedó en "Provisioning"; el conector de Vercel está `connect_incomplete` y solo lee (sin desplegar). Hoy corre en cualquier máquina: `pip install -r "router inteligente universal/chat_space/requirements.txt"` y, dentro de `router inteligente universal/`, `uvicorn integration.chat_mvp.app:app --port 7860`.
2. Claves que faltan: Groq, DeepSeek, Moonshot, MiniMax directas; Cerebras necesita pago.
3. Probar `github/planeta123` y `github/abc1tienda-web` (nuevos). `GH_ACCOUNT_1/2` viejos dan 401.
4. Modelos locales: sin servidor y sin pruebas. Benchmark Nanbeige/Qwen 9B: necesita máquina de 8 núcleos.
5. Prueba de modelos en el procesador HF (Job `cpu-upgrade`): el Job dio ERROR; falta capturar el log y corregir.
6. Plantilla fija (YAML reglas + JSON indicaciones + Python motor) y Crazy Wall permanente dentro del chat.
7. Graphiti real (hoy hay un grafo de procedencia en SQLite).
8. STATE/CHECKPOINT/PLAN/Handoff antiguos siguen desfasados; la bitácora grande no se reescribió (se añaden archivos nuevos).
9. Contrato `tel.workflow/v3` vs `v4` sin decidir.

## 9. Trazabilidad (dónde está cada cosa)
- Instrucciones textuales: `INPUT-VERBATIM-2026-09-20-*` (chat-mvp, b, c, d, e, f) e `INPUT-VERBATIM-2026-09-21-g-h-*`.
- Resultados: `RIU-0105` (chat), `RIU-0106` (caché, DAG, banco de claves), `RIU-0111` (GitHub, cobro HF, NVIDIA), este handoff (RIU-0116).
- Método: `DSL-FABLES-yaiwes-node-executor-xray-v2.md`, `CONSEJOS-CONTINUIDAD-Y-RECUPERACION.md`, `00-LEEME-PRIMERO.md`.
- Banco: `BANCO-SECRETO-README.md`, `KIT-EQUIPO-NVIDIA/`; diseño en `PLAN-ANEXO-A-SECRET-BANK.md` (otro chat) y código base en `Chat Mvp/secret_bank/`.
- Otro chat trabaja en paralelo (numeración RIU-0107 a 0110, carpeta `Chat Mvp/`): leer `RIU-0110-estado-y-trucos-para-el-siguiente-chat.md` antes de tocar nada.
- Workflows de evidencia: `riu-chat-mvp-verify.yml`, `riu-dag-run.yml`, `riu-nvidia-matrix.yml`, `riu-nvidia-pool-test.yml`, `riu-hf-job-models.yml`, `deploy-chat-space.yml` (bloqueado por PRO).

## 10. Primer día (checklist)
1. Leer este archivo, `INPUT-VERBATIM-2026-09-21-g-h-*` y `RIU-0110-*`.
2. Comprobar el HEAD de `main` y las últimas corridas antes de escribir.
3. Anotar la primera instrucción del Director textual y validar.
4. Pedir al Director la contraseña del banco SOLO si hay que abrirlo; nunca escribirla.
5. Trabajar en cadena, delegando por DSL DAG; informar en corto.
