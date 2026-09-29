# Índice router inteligente universal
Actualizado: 2026-09-29. Un solo Router. Todo en `main`.

## Objetivo: solo 2 raíces
1. **Raíz del Router**: `router inteligente universal/` (runtime, agentes, componentes). Debe poder moverse a otro repo tal cual.
2. **Raíz del chat**: `chat router/` (código, plan y estado).
Estado de la reorganización: PENDIENTE (falta revisar dependencias antes de mover; ver `chat router/03-ESTADO/HANDOFF.md`).

## Dónde está el registro
`chat router/03-ESTADO/`: `ESTADO.json` (estado), `CRAZY_WALL.json` (nodos N-00..N-09), `BITACORA.jsonl` (solo se añade), `HANDOFF.md` (para quien retome).
Arquitectura de Hugging Face y del Router: `README-HUGGINGFACE.md`.

## Lo que dejó Opus para el conector MCP y el Router (documentado por Opus; no verificado por mí salvo lo marcado)
- Router único: Job HF cpu-basic 16 GB lanzado por `.github/workflows/riu-router-job-central.yml` (verificado vivo 2026-09-29).
- Conector MCP de Claude: Space `COMAND-CENTER-1/claude-github-mcp-backup`, sin OAuth, dirección secreta, webhook al lanzador único, keep-awake desactivado. Space verificado RUNNING; PROTEGIDO, no tocar.

## Ruta de modelos (orden del Director)
NVIDIA (hasta 4 claves; Kimi K3 o más nuevo) → Groq → DeepSeek V4 Flash al final. Cerebras y OmniRoute eliminados. Sin Anthropic.

## Carpetas de la raíz (hoy, antes de reorganizar)
`.github`, `Chat Mvp` (banco de claves cifrado; el runner de agentes lo lee por URL, no mover sin revisar), `Claude notas`, `Notas del Director (verbatim)`, `Documentos proyectos router inteligente universal`, `Download code router inteligente universal`, `Readme arquitectura router inteligente universal`, `Github coneccion`, `coneccion huggueface Github`, `router inteligente software`, `router inteligente universal`, `chat router`, `scripts`, `vercel-chat`, motores de búsqueda y de descarga (carpetas ➡️📂), y otras de apoyo.

## Trazabilidad
Manifiesto de descarga: `Download code router inteligente universal/RESEARCH_DOWNLOAD_MANIFEST.jsonl`.
