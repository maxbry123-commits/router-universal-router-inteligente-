# CHECKPOINT 2026-09-30 ~01:10 (Bogotá) — auditoría de las últimas 12 h y lista de los 3 objetivos
Marcas: 🟡 hecho/probado a medias · 🔴 pendiente · ⛔ bloqueado. NADA está ✅ (faltan 3 rondas limpias + 4 pasadas).
Fuente: solo conector MCP_SECRET_HF (GitHub + HF). El conector HF_Gith_Allow_Access se cayó (needs_reconnect); MCP_SECRET_HF sí responde (14 herramientas, GitHub maxbry123-commits, storage /data/repos).

## Orden del Director (00:59)
Actualizar los documentos del repo (Readme arquitectura, Crazy Wall, estado JSON, handoff, Claude notas); entender el motor de descarga/extracción leyendo lo que hizo Opus, para descargar lo que falta (harness de DeepSeek); sacar de los archivos 3 objetivos y una lista de pasos de cada uno: 1) Router, 2) equipo de 4 objetivos (repo `agentes`), 3) Chat y agentes.

## Verificado hoy (solo lectura)
- Router en `main`: cadena de chat + Plugin Host unidos (merge babd02e, 21:48). Lanzador pasa HF_TOKEN_1 (d578f53). LIVE_URL = Job 6abc32754c46ef1987032c93 (flag 668a9c4, 21:52). No pude llamarlo en vivo desde aquí.
- 🔴 CORRECCIÓN: `integration/chat_mvp/openai_route.py` NO existe en `main` (404). Solo está en la rama `bloque2-agentes` (commits e983efd puerta, 23f941b montaje en app.py, 6308b44 grupo assistants, 017b05d tests, 69b302e guía). Un "handoff final" de otra sesión decía que estaba en main: es falso. `bloque2-agentes` sigue SIN unir a main.
- Workflows temporales SIGUEN en main: `tmp-nvidia-diag.yml` (blob d31a2238), `tmp-bloque2-verify.yml` (blob 309c383b). Además siguen `prueba-groq`, `prueba-chat-e2e`, `diagnostico-router-job`, `riu-router-smoke`.
- Repo `agentes`: 0 commits en las últimas 12 h (el equipo de 4 objetivos no se movió; PR #23 y #24 abiertas desde 2026-09-21).
- Actividad en `main` en 12 h de OTROS agentes (no de este hilo): agent-7 y agent-10 (instalar modelo en la máquina de 32 GB, reabren pasos "cerrados sin evidencia"), orch-chat P1 (reabierto tras humo FAIL), rondas "riu-agents" (Crazy Wall + HANDOFF), y CI del Space MCP (publicación por OIDC, ahora solo manual y en serie: 6c65718, d2df19b, 354bad4).
- Notas mías ya en main: input verbatim del Director parte 5 (fc852f2) y reglas comunes de agentes (74d218f).
- NVIDIA (medido, run 36637738796): Nemotron 0,5–2,7 s; GLM 5.3 17–34 s; Kimi K3 44–52 s. Con plazo de 30 s Kimi casi siempre falla y GLM la mitad. Decisión del Director (21:13/21:28): orden Kimi→GLM→DeepSeek V4 se mantiene, plazo hasta ~90 s, Nemotron fuera; Groq Qwen 3.8 solo como cola de emergencia; luego las SDK "sol gpt" (10+) para los demás. Aún no aplicado en código. 🔴

## Motor de descarga y extracción (cómo funciona; leído en main)
- Workflow canónico: `.github/workflows/riu-agent11-canonical-download.yml`. Se dispara con `workflow_dispatch` o al subir un JSON en `router inteligente universal/agents-yaiwes/agent-11-download-extraction/COMPONENT_REQUESTS/*.json`.
- Antes de correr verifica por `git hash-object` que los 2 archivos del motor sean los canónicos (motor_2_queue_download_extract.py = 84d566e2…, hf_download_extract_engine.py = 91e6e448…). Motor en la carpeta "Motores descarga extracción búsquedas/…/📂Motor descarga de componentes y extracción de zip/".
- Formato de la petición (ejemplo real de Opus, openclaw-hermes-latest.json): `{"queue":[{"id","component","source_repo","source_ref","slug","dest_repo","dest_branch","dest_root","publish":true}]}`.
- Resultado: el motor publica en main `<slug>/code/` + `<slug>/DOWNLOAD_EXTRACT_MANIFEST.json` (source_commit, árbol sha256, extraction_verified, reconstruction_verified); el workflow lo relee y exige ambos en true.
- Otro workflow, `riu-download-agents.yml`: baja "donantes" (Meta, SmolAgents, PocketFlow) con `common/download_donors.py`; sin LLM.
- Por qué falló el harness antes (agent-38, rama backup): pidió `SOURCE_REF: main` y el repo `deepseek-ai/deepseek-harness` solo tiene la rama `master` → git 128. Para descargarlo: petición con `source_repo: deepseek-ai/deepseek-harness`, `source_ref: master`. Licencia MIT, Developer Preview; se revisa antes de usarlo, no se ejecuta código de terceros sin revisión.
- Las 2 copias que pidió el Director: una petición con `dest_root` para la base del chat y agentes, otra para conectar al Router (dos slugs distintos del mismo componente). 🔴 No creadas todavía.

## OBJETIVO 1 — Router
1. 🔴 Aplicar la ruta decidida: grupo `chat_nvidia` (solo chat, Hermes, OpenClaw): Kimi K3 → GLM 5.3 → DeepSeek V4, 90 s c/u, sin Nemotron; grupo `sdk` (10+ SDK, lista pendiente del Director); Groq Qwen 3.8 al final como emergencia.
2. 🔴 Unir `bloque2-agentes` a main (puerta /v1/router, grupo assistants, DAG con loops, espejo del equipo, estado restaurado) tras CI.
3. 🔴 Extensión ÚNICA del Plugin Host para no volver a tocar el Router: transporte http en la ficha, ruta `POST /plugins/{id}/call`, recarga en caliente (`/plugins/sync`); plugins nuevos arrancan APAGADOS. Hoy solo acepta Python en el mismo proceso, máx 120 s, y carga solo al arrancar.
4. 🔴 Plugin `deepseek_harness` (regla de envoltura degraded ya existe en `PluginHost.call`) + las 2 copias del componente por el motor de descarga.
5. 🔴 Puente de almacenamiento (HF bucket) y puente de cómputo con Hugging Face como plugins (apagados).
6. 🔴 Borrar workflows temporales (tmp-nvidia-diag, tmp-bloque2-verify y los de prueba) con [skip ci].
7. 🔴 Añadir test_plugin_host al CI permanente; token HF solo de inferencia (hoy HF_TOKEN_1 entra al Job).
8. 🔴 Relanzar el Job UNA vez con todo, verificar /health, /chat/router/status, /plugins, /chat/send y /v1/router.
9. 🔴 Vercel: RIU_ROUTER_URL a la URL definitiva y UN solo deploy, solo cuando el Director lo ordene.

## OBJETIVO 2 — Equipo de 4 objetivos (repo `agentes`)
Es un loop de GitHub Actions (`plan-opus-loop.yml`, runner `Claude notas/PLAN-OPUS/runner/plan_opus_loop.py`), 5 agentes-CLI en grupos G1..G4. Estado: 0 de 4 entregados. Todas las llamadas a modelos son DIRECTAS (NVIDIA/Cerebras/Groq); ninguna pasa por el Router.
1. 🔴 Rama `bloque3-equipo4-router` en `agentes`: cambiar `chat()` para llamar al Router (`/chat/route` o `/v1/router`), quitar `resolve_key`, la sonda directa y los secretos CEREBRAS/GROQ/RIU_TEAM_BANK del workflow.
2. 🔴 Apuntar Codex, OpenCode y OpenHands al Router (requiere la puerta /v1/router en main).
3. 🔴 Secretos nuevos en `agentes`: HF_TOKEN y RIU_ROUTER_API_KEY (solo el Director puede ponerlos).
4. 🔴 Plugin `equipo_4_obj` en el Router (acciones status y groups). Grupos: Claude Code/Codex/OpenHands/Consul→default; Open Code/Meta Code→code; sentinela plan4→minor.
5. 🔴 Decidir PR #23 y #24 (mergear o cerrar) y la regla "sin APIs de Anthropic" para Claude Code.
6. 🔴 Corrida corta de prueba: `max_nodos=1` por grupo, verificar en /chat/router/status.

## OBJETIVO 3 — Chat y agentes
1. 🔴 Hermes y OpenClaw al Router por grupo `chat_nvidia`/`assistants` (config y puente ya escritos en `bloque2-agentes`; falta unir y probar).
2. 🔴 Rowboat y Ruflo (orquestadores) conectados igual.
3. 🔴 Consulta doble: cada mensaje va normal y en paralelo a NVIDIA como asesoría estilo Ask Consul (Kimi, GLM, DeepSeek V4, Kimi decide); el consejo se inyecta en el agente sin frenarlo mediante un buzón por conversación (plugin `asesoria`).
4. 🔴 Equipo de asesores: 12 metas de entrada/salida, 3 refutaciones, Ask Consul de 12 pasos, Kimi decide, 2 simulaciones. El Director debe VER las preguntas antes de ejecutarlas.
5. 🔴 Puente de almacenamiento chat↔agentes (verificar si ya existe en el Router; si no, plugin).
6. 🔴 UI de chat apiladas y espejo (mirror) del equipo: parcial en `bloque2-agentes`.
7. 🔴 Pendientes previos: conversaciones/caché se pierden al relanzar el Job; aislamiento por proceso de plugins; streaming en /v1/router; X-API-Key vs Bearer para Hermes/OpenClaw.

## Bloqueos y decisiones del Director
- Lista de las 10+ SDK "sol gpt" y sus nombres de secreto.
- Autorizar el cambio único al Plugin Host (ya dijo "si con eso resolvemos lo haces").
- Secretos HF_TOKEN y RIU_ROUTER_API_KEY para `agentes`.
- Reconectar HF_Gith_Allow_Access o dejar MCP_SECRET_HF como conector oficial (este sí funciona).
- Rotar las 7 llaves Groq (acción del Director).

## Regla de estos documentos
Faltan por actualizar con estas mismas entradas (archivos grandes, se reescriben completos): `Estado y handoff global/CRAZY_WALL.json`, `BITACORA.jsonl`, `ESTADO.json`, `HANDOFF.md` y `Readme arquitectura router inteligente universal/`. Este archivo es el checkpoint de referencia mientras tanto.
