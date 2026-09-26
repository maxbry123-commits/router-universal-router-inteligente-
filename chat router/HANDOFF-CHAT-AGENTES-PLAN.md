# HANDOFF — CHAT, AGENTES Y PLAN (para la siguiente sesión de Claude u otra IA)
Actualizado: 2026-09-26 por Opus. Director: Max. Leer COMPLETO antes de tocar nada.

## 0. Reglas del Director (obligatorias)
- Anotar cada instrucción del Director 1 a 1 (input block verbatim) ANTES de ejecutar. Lo no resuelto = GAP, nunca inventar.
- No cambiar instrucciones, diseño ni herramientas del Director sin su autorización expresa.
- Respuestas cortas, sin jerga. Delegar con DSL DAG. Sin claves en repos (son públicos).
- Rutas de IA: NVIDIA (4 claves) → Cerebras → Groq → DeepSeek V4 Flash al final. Sin APIs de Anthropic.

## 1. Instrucciones del Director (fuente de verdad)
- `chat router/INPUT-BLOCK-VERBATIM-CHAT-Y-PANEL.md` (parte 1), `-PARTE-3.md`, `-PARTE-4.md`. La PARTE 2 (documentos completos) NO se llegó a subir: está completa en el chat de Opus del 25–26 sep; GAP.

## 2. URGENTE — conector MCP de Claude (se desconecta y pide "Allow Access")
- Space: https://huggingface.co/spaces/COMAND-CENTER-1/claude-github-mcp-backup (CPU Upgrade, NUNCA DORMIR ya fijado).
- Causa: el 25-sep GPT añadió login OAuth (HuggingFaceProvider de FastMCP). Cada reinicio pide volver a autorizar.
- Intento de Opus: sesiones OAuth en disco (`.github/workflows/mcp-oauth-persist-once.yml`, aplicado OK), pero la prueba de reinicio (`mcp-restart-test-once.yml`) mostró que SIGUE pidiendo "Allow Access".
- Solución propuesta, pendiente de autorización del Director: quitar el OAuth y usar una dirección secreta larga (token en la URL, guardado solo en Claude) → cero pantallas de autorización. Alternativa: revisar si /data del Space es persistente (si no, el disco se borra en cada reinicio).
- NO reiniciar el Space sin necesidad.

## 3. Chat
- Publicado en Vercel: https://riu-jev-bridge.vercel.app (pantalla propia de Opus + puente a Router). El Director NO lo aprueba: pidió Open WebUI o un chat open source descargado, con sus skills y diseños, cada botón probado. GAP principal.
- Instrucciones completas del chat y del panel: sección 1.
- Backend: Router (FastAPI) en HF Job; URL en `router inteligente universal/agents-yaiwes/ROUTER_JOB_PAUSE.flag`. Rutas nuevas de Opus: `integration/chat_mvp/ui_bridge.py` (control, órdenes, grupos, workflows).
- Space alternativo preparado pero NO creado (HF 402 al crear Spaces por API): `chat router/space/`.

## 4. Agentes — plan de 4 objetivos (repo agentes)
- Plan: https://github.com/maxbry123-commits/agentes/blob/main/Claude%20notas/PLAN-MAESTRO-4-OBJETIVOS.md
- Handoff del loop: https://github.com/maxbry123-commits/agentes/blob/main/Claude%20notas/PLAN-OPUS/HANDOFF-PLAN-OPUS.md
- Mini router (este repo): `.github/workflows/mini-router-plan-4-objetivos.yml` — corre el loop con Cerebras/NVIDIA/Groq (sin DeepSeek), cada hora, resultado como rama+PR en agentes.
- Estado: vuelta 1 trabajó 45 min pero perdió el resultado (arreglado 26-sep 07:34). Vuelta 2 lanzada 07:34 → revisar su rama/PR.
- Staff decidido: Rowboat (orquestador), Ruflo (flujo), Claude Code (diseña/revisa, vía router), Grok (ejecuta), 4 de Meta en `agents-yaiwes/donors/` (Muse Code, Muse Glimmer, MetaCua = navega y hace capturas, CUA+MCP), apoyo Hermes/MSAF/Codex/MiMo, memoria Memanto+Graphiti+Graphify. Aún NO conectados al Router.

## 5. Descargas (motores)
- Cadenas: `agents-yaiwes/agent-40-motor-frontend-a`, `agent-41-motor-frontend-b`, `agent-42-motor-router-agentes`.
- BLOQUEADAS: el motor rechaza repos con enlaces simbólicos (SOURCE_SPECIAL_FILE_GAP: assistant-ui, ruflo) y el ejecutor se detiene en el primer fallo. Arreglo propuesto (necesita autorización porque el motor es "inmutable"): que el motor salte los enlaces simbólicos y los registre.
- Otra IA también está montando componentes en el repo frontend (commits "Motor1+Motor3 … no GHA no HF", 26-sep) — coordinar para no pisarse.

## 6. Apagado en HF por orden del Director
- `keep-mcp-space-awake.yml` DESACTIVADO. Keeper Job apagado (0 corriendo). No volver a encenderlos sin autorización.

## 7. Siguiente orden sugerida
1) Conector sin fricción (sección 2). 2) Motor: saltar enlaces simbólicos (con autorización) y relanzar 40/41/42. 3) Chat sobre Open WebUI / chat descargado con skills del Director. 4) Conectar el staff al Router. 5) T-3000 (ver su handoff).
