# RIU-0125 — Instrucción (r): estado de los agentes, auditor, watchdog, Muse Glimmer, Vercel — 2026-09-21

Instrucción textual: `INPUT-VERBATIM-2026-09-21-r-auditor-meta-agents-watchdog.md`. Handoff con URLs: `router inteligente universal/agents-yaiwes/HANDOFF-AGENTES-Y-WATCHDOG.md`.

- Estado de la ronda anterior (13:06): agentes 1 y 3 CERRADOS 3/3; agentes 2 y 4 BLOQUEADOS. Causa registrada: Groq 1.ª clave inválida (401), NVIDIA 500/503, Cerebras 402, MiniMax M3 504.
- Sonda de claves del banco (workflow `RIU Probe Keys`, 13:08): Groq 6/7 sirven; NVIDIA 5/5 autentican pero 503; Cerebras 5/5 autentican pero 402 con `gpt-oss-120b`.
- Correcciones de ruta (autorizadas por el Director: "corriges rutas"): `agents-yaiwes/ROUTE.json` central (Groq → NVIDIA → Cerebras); los SmolAgents recorren todas las claves útiles de cada proveedor (`common/routes.py`); las rondas retoman solo los pasos pendientes.
- Paso 1 (auditor): `agent-5-auditor` = copia de SmolAgents (`auditor_agent.py`) con herramientas forenses de solo lectura; 4 pasos de auditoría sobre paquetes con las palabras literales del Director (`common/audit_pack.py`); el Sheriff exige citas textuales y evidencias existentes; informe determinista `AUDIT-CHECKLIST.md`. Ronda despachada: run `35604219274`. NOTA: los 4 pasos cubren cada uno un cuarto de las notas (las 4 juntas = una pasada completa); "auditar 4 veces" pide 4 pasadas completas: pendiente de confirmar con el Director.
- Watchdog: `RIU Watchdog` cada hora (cron), determinista, sin modelos; README de notas de Claude en `agents-yaiwes/WATCHDOG/`.
- Muse Glimmer 30B: repo y archivos verificados (Q4_K_M 16.8 GB, borrador `dflash` 1.6 GB, `mmproj` 1.4 GB). NO se lanzó el Job (cuesta) ni se creó el DSL DAG de los agentes de Meta todavía.
- Vercel: solo lectura (403 al crear despliegue, variables y claves de AI Gateway). Puente con Jev bloqueado hasta que el Director dé permiso de escritura o cree la clave.
- Pendiente (no iniciado): repetir la auditoría para LLM locales; usar el motor de descarga para los 4 agentes de Meta y sus repos; DSL DAG loop META AGENTS.
