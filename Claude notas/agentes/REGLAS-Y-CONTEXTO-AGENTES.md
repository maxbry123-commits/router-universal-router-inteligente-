# REGLAS Y CONTEXTO COMÚN PARA LOS AGENTES — 2026-09-29 ~21:55 (Bogotá)

Lo escribe Claude (coordinador). Las órdenes textuales del Director están en `Readme arquitectura router inteligente universal/INPUT-BLOCK-VERBATIM-2026-09-29-director-parte-5.md` (léelas primero, son 7 KB).

## Reglas de trabajo (obligatorias)
- Español simple. Tu respuesta final: máximo 10 líneas, sin código ni nombres de archivo salvo lo imprescindible.
- Solo el conector de GitHub y Hugging Face (herramientas `mcp__HF_Gith_Allow_Access__*`; cárgalas con ToolSearch: `select:mcp__HF_Gith_Allow_Access__create_branch,mcp__HF_Gith_Allow_Access__create_or_update_file,mcp__HF_Gith_Allow_Access__get_file,mcp__HF_Gith_Allow_Access__github_api`). No uses otras fuentes ni herramientas de web.
- Repo: `maxbry123-commits/router-universal-router-inteligente-` (público: nunca escribas claves ni valores secretos, solo NOMBRES de secretos).
- Trabaja SOLO en tu rama (créala desde `main`). No escribas en `main`. Commits con `[skip ci]`.
- Mínimo cambio: sin sobre-ingeniería, sin reescribir lo que ya funciona, sin borrar componentes (se reubican), sin ejecutar código de terceros, sin tocar Vercel, el Space MCP ni el Job vivo del Router.
- NO quemar tokens: haz tu tarea, sube a tu rama, escribe un handoff corto en tu rama (`Claude notas/agentes/<tu-nombre>.md`), responde y PARA. Sin polling, sin esperar CI, sin releer archivos grandes sin necesidad. Si algo exige esperar (CI, otra rama, una descarga), termina y escribe `RELANZAR EN N MIN: motivo` con N = 5, 10 o 20.
- Marcas: 🟡 hecho sin probar · 🔴 pendiente · ⛔ bloqueado. Nunca ✅. No inventes: lo que no verificaste, dilo.
- Arquitectura: 90% código determinista, 10% LLM. Nuevas APIs, SDK y agentes se conectan como PLUGINS (carpeta con `ficha.json` + `plugin.py`, función `handle(action, payload)`), sin volver a tocar el código del Router.
- Si dudas de algo, no lo adivines: anótalo como pregunta para el Director y sigue con lo demás.

## Mapa del repo
- `router inteligente universal/integration/chat_mvp/` → políticas de cadenas (`resilience.py`), rutas (`route_api.py`, `router.py`, `openai_route.py`), `app.py`.
- `router inteligente universal/integration/plugin_host/` → `host.py`, `api.py` (contrato `plugin_host/v1`, `entry_point` = `plugins.<id>.plugin:handle`; solo prefijos `integration.` y `plugins.`).
- `router inteligente universal/plugins/` → plugins (hoy `chat` y `thinking-modes`).
- `chat router/05-AGENTES/` → agentes (puente Hermes/OpenClaw, colmena, gobierno).
- `Motores descarga extracción búsquedas/` → motor de descarga y extracción.
- Router vivo: Job HF `6abc32754c46ef1987032c93` (no tocar). La dirección viva está en `router inteligente universal/agents-yaiwes/ROUTER_JOB_PAUSE.flag`.
- Lo de la rama `bloque2-agentes` (puerta OpenAI `/v1/router`, grupo `assistants`, DAG con `route`+`loop`, espejo del equipo, puente de asistentes) puede NO estar todavía en `main`: verifícalo antes de usarlo y trae a tu rama solo lo que falte.

## Decisiones confirmadas por el Director (21:13 a 21:49)
1. Se quiere un Router que crezca por plugins (Fables `enchufe` + envoltura del harness de DeepSeek) sin volver a editar su código: nuevas APIs, SDK, agentes, puente de almacenamiento de Hugging Face y puente de cómputo de Hugging Face.
2. Conexión especial (solo chat, Hermes y OpenClaw): claves de NVIDIA, solo Kimi K3 → GLM 5.3 → DeepSeek V4, con plazo de 1,5 min por modelo. Nombre del grupo: `chat_nvidia`. Nemotron sale de la cadena del chat.
3. Todos los demás agentes y conexiones: las SDK "sol gpt" (10 o más, el Director las entregará después). Grupo: `sdk` (lista configurable, vacía por ahora). Groq Qwen 3.8 va como última cola de emergencia del Router.
4. El chat, Hermes y OpenClaw también podrán usar las SDK con un selector. NVIDIA queda como selector del chat y como consulta extra de Hermes y OpenClaw.
5. Cada mensaje que entra al chat, Hermes, OpenClaw, Rowboat o Ruflo (los orquestadores) genera una consulta DOBLE en paralelo: la misma consulta va a NVIDIA como asesoría tipo Ask Consul (1 Kimi K3, 2 GLM 5.3, 3 DeepSeek V4, 4 Kimi decide y junta). El consejo llega con latencia y se INYECTA en el agente que sigue trabajando, sin detener su tarea. Si falla, se ignora. No importa que gaste el doble: son 4 llaves NVIDIA que rotan.
6. Las ramas de los agentes las prueba y une Claude; los agentes no unen a `main`.

## Nombres de ramas
`bloque3-plugins-base`, `bloque3-harness`, `bloque3-ruta-nvidia`, `bloque3-agentes-chat`, `bloque3-almacenamiento`, `bloque3-asesores-doc` (repo del Router) y `bloque3-equipo4-router` (repo `agentes`).
