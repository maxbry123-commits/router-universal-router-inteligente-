# RIU-0105 — Chat MVP conectado a proveedores, GitHub multi-cuenta y almacenamiento en 4 sistemas — 2026-09-20

Contrato: `tel.workflow/v3` · `FAIL_CLOSED_LOOP` · autorización P1-P4 (RIU-0098) + "100 % autorizado" del Director.
Instrucción literal: `INPUT-VERBATIM-2026-09-20-chat-mvp.md`. Solo se tocó este repo (P3).
Coordinación: otros chats escribieron en `main` durante el nodo (RIU-0103/0104 LFS/Qdrant, hot-path con `asyncio.to_thread`, workflow verify). Se fusionó sin pisarlos.

## Qué existe ahora (todo bajo `router inteligente universal/`)
| Pieza | Archivo | Estado |
|---|---|---|
| App del chat (une gateway certificado + API del chat) | `integration/chat_mvp/app.py` | EJECUTADO en runner |
| API: proveedores, envío, agentes, documentos, GitHub, almacenamiento, grafo | `integration/chat_mvp/router.py` | EJECUTADO en runner |
| Clientes HF Router / Cerebras / NVIDIA / Groq / API local (BYOK) | `integration/chat_mvp/providers.py` | EJECUTADO en runner |
| GitHub multi-cuenta (etiqueta→variable de entorno, o token por petición) | `integration/chat_mvp/github_tools.py` | EJECUTADO en runner |
| Almacenamiento 4 sistemas: SQL (SQLite), grafo de procedencia, caché, documentos | `integration/chat_mvp/store.py` | EJECUTADO en runner |
| UI de una página (proveedor/modelo, sin agente/con agente, documentos, GitHub, agentes, almacenamiento, claves) | `integration/chat_mvp/chat_ui.html` | Servida y probada por TestClient; NO probada en navegador |
| Selector HF (Kimi K3, MiniMax, DeepSeek V4 Flash/Pro) sin inventar `model_id` | `integration/huggingface/chat_catalog.py`, `chat_executor.py` | EJECUTADO en runner |
| Auth con las 100 keys MAXBRY (1 PBKDF2 por petición) | `integration/huggingface/keystore_auth.py`, `api_key_auth.py` | EJECUTADO en runner |
| Bundle Docker del Space + workflow de despliegue | `chat_space/*`, `.github/workflows/deploy-chat-space.yml` | Bundle ensamblado; despliegue BLOQUEADO (ver flags) |
| Verificación real | `.github/workflows/riu-chat-mvp-verify.yml` | Corre en cada cambio del workflow o por dispatch |

Ejecución local del chat: `cd "router inteligente universal" && uvicorn integration.chat_mvp.app:app --port 7860` y abrir `/chat`
(variables: `RIU_CHAT_ALLOW_PROVIDER_LIVE=1`, `HF_TOKEN_1`, `CEREBRAS_API_KEY_1`, `NVIDIA_API_KEY_1`, `GROQ_API_KEY_1`, `RIU_LOCAL_BASE_URL`, `RIU_GITHUB_ACCOUNTS`, `RIU_DATA_DIR`).

## Evidencia (runner ubuntu, anotaciones del check-run; run `35504526944` commit `abd1696`)
- Tests: 47 passed, 1 failed (la aserción del grafo era mío; corregido en `e6afe76`). Nueva corrida despachada tras el fix.
- E2E por `/chat/send` → hot-path → proveedor: Kimi K3, DeepSeek V4 Flash, DeepSeek V4 Pro y MiniMax M3 respondieron 200 (`finish=stop`, `certified=false`).
- Adjuntar documento: el modelo devolvió la palabra del documento (`contains_zafiro=True`). Modo con agente 200. Caché: primer envío `cached=False`, segundo `cached=True`. Historial persistido (2 mensajes). Almacenamiento tras el flujo: 18 mensajes, 21 aristas de grafo, 1 acierto de caché, 2 documentos.
- Selector de cuenta GitHub: cuentas `ci-a` y `ci-b` (mecanismo probado con el token del workflow para ambas; NO es una segunda cuenta real). Lectura de archivo y adjuntar 200 con ambas; resumen del archivo por el modelo 200.
- Cerebras: catálogo de 2 modelos; la inferencia respondió `402 Payment required` (la cuenta necesita facturación).
- NVIDIA y Groq: sin secret en el repo (`nokey`).
- Token `HF_TOKEN_1`: cuenta `COMAND-CENTER-1`, `fineGrained`, permisos globales `discussion.write,post.write` + 1 recurso acotado; no crea Spaces ni escribe buckets.

## FLAGS 🚩 (no bloquean lo hecho; requieren al Director o una decisión)
1. 🚩 Despliegue del chat en Hugging Face: falta el secret `HF_WRITE_TOKEN` (token HF con escritura en Spaces y en el bucket `COMAND-CENTER-1/yaiwes-v54`). Con él, correr `Deploy Chat MVP Space` (dispatch) crea el Space `COMAND-CENTER-1/riu-chat-mvp`, sube el bundle, pone los secrets y variables y monta el bucket en `/data` (si la API de volúmenes no está disponible, montarlo a mano en Settings del Space).
2. 🚩 NVIDIA: falta `NVIDIA_API_KEY_1`. Groq: falta `GROQ_API_KEY_1`. Cerebras: 402, activar facturación.
3. 🚩 Segunda cuenta de GitHub real: pasar el token de la otra cuenta como secret (`GITHUB_TOKEN_2`) o pegarlo en la pestaña Claves; el Space solo recibe el PAT completo si el dispatch usa `include_github_token=true`.
4. 🚩 APIs locales: falta `RIU_LOCAL_BASE_URL` (URL OpenAI-compatible de llama.cpp/Ollama/vLLM). No hay modelos locales instalados en este repo y el contrato es `REMOTE_INFERENCE_ONLY`; el proveedor `local` queda listo pero sin URL.
5. 🚩 Graphiti real (grafo temporal con extracción por LLM sobre Neo4j/FalkorDB): NO implementado. Hay un grafo de procedencia en SQLite con `valid_at`, compatible como capa inicial.
6. 🚩 Pool de agentes: el Director dará el pool. Hay 2 agentes semilla editables desde la pestaña Agentes (`orquestador-g0`, `seals-team-yaiwes-001`); el router por grupos 0/1/2 y el salto Nvidia/Cerebras → local → DeepSeek V4 Flash son del Paso 3 y NO se hicieron.
7. 🚩 Benchmark Nanbeige4.2-3B (Q4_K_M vs Q5_K_M) y Qwen3.5-9B (Q4_K_M, llama.cpp, 8 hilos, 10 ejecuciones de 500 LOC): NO ejecutado. El runner gratuito de GitHub tiene 4 vCPU, no 8; las cifras no representarían la máquina objetivo. Necesita una máquina de 8 vCPU / 32 GB.
8. 🚩 Sincronización a bucket HF (`/chat/storage/sync`): implementada y probada con un sistema de archivos simulado; NO probada contra el bucket real por falta de token de escritura.
9. 🚩 Contrato `tel.workflow/v3` vs `v4`: sigue sin decidir (GAP-CONTRACT-VERSION-V3-V4-001).
10. 🚩 Cifras de los análisis pegados por el Director (tokens/s, benchmarks de Nanbeige, etc.) no verificadas por Claude.

## Estado del nodo
`CHAT_MVP_EJECUTADO_EN_RUNNER; DESPLIEGUE_HF_BLOQUEADO_POR_CREDENCIAL_DE_ESCRITURA`. `global_closed=false`.
No se tocaron STATE.json, CHECKPOINT.json, PLAN-TAREAS.md ni Handoff (siguen desfasados; ver `00-LEEME-PRIMERO.md` §4.1).

## Próximo delta seguro
1. Leer el resultado de la corrida verify posterior a `e6afe76` (debe dar 48 passed).
2. Con `HF_WRITE_TOKEN`: despachar `Deploy Chat MVP Space` y anotar la URL del Space.
3. Con las claves NVIDIA/Groq: repetir el E2E y anotar catálogos.
4. Paso 3 del Director (router por grupos 0/1/2 con fallback) solo cuando el chat esté desplegado.
