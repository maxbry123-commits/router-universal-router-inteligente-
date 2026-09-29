# Índice router inteligente universal
Actualizado: 2026-09-29. Un solo Router. Todo en `main`. Empezar por `Estado y handoff global/HANDOFF.md`.

## Raíces de `main`
1. `router inteligente universal/` — Raíz del Router. Incluye `Banco de claves/` (antes "Chat Mvp"), `Componentes del Router/` (router inteligente software, api, Yaiwes Cognitive Control Plane, dataset Yaiwes, hermes-agent), `scripts/` y los componentes de código abierto. Movible a otro repo.
2. `chat router/` — Raíz del chat (código, plan, agentes del chat, `chat_orders/`).
3. `Motores descarga extracción búsquedas/` — Motores de descarga, extracción y búsqueda.
4. `Readme router inteligente universal/` — Este índice y los readmes de componentes.
5. `Readme arquitectura router inteligente universal/` — Arquitectura.
6. `Claude notas/` — Solo lo en curso.
7. `Estado y handoff global/` — Crazy Wall, bitácora, estado (JSON), handoff global y fichas de tareas T-00..T-09.
8. `Huggingface/` — Hugging Face y GitHub (conexiones, rutas, handoff).
9. `Vercel/` — Chat de Vercel y su handoff.
10. `Documentos del proyecto/` — Archivos markdown subidos, notas del Director, documentos.

## Lo que dejó Opus para el conector MCP y el Router (documentado por Opus; no verificado por mí salvo lo marcado)
- Router único: Job HF cpu-basic 16 GB lanzado por `.github/workflows/riu-router-job-central.yml` (verificado vivo 2026-09-29).
- Conector MCP de Claude: Space `COMAND-CENTER-1/claude-github-mcp-backup`, sin OAuth, dirección secreta, webhook al lanzador único, keep-awake desactivado. Space verificado RUNNING; PROTEGIDO, no tocar.

## Ruta de modelos (orden del Director)
NVIDIA (hasta 4 claves; Kimi K3 o más nuevo) → Groq → DeepSeek V4 Flash al final. Cerebras y OmniRoute eliminados. Sin Anthropic.

## Trazabilidad
Manifiesto de descarga: `Motores descarga extracción búsquedas/Download code router inteligente universal/RESEARCH_DOWNLOAD_MANIFEST.jsonl`.
