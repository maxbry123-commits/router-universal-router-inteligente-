# memoria.md — Contexto completo para handoff entre Devins
# Cableado con HANDOFF.md (misma raíz: chat router/Workflow Loop code Yaiwes/03-ESTADO/)
# Fecha corte: 2026-10-01 · Sesión: resumen para retomar en 3 días.

## Dónde está el trabajo
- Repo: maxbry123-commits/router-universal-router-inteligente- · Branch: devin/1790824641-chat-agent-plan
- PR: https://github.com/maxbry123-commits/router-universal-router-inteligente-/pull/6 (DRAFT)
- Repo fuente agentes (referencia local): /home/ubuntu/referencia-agentes/src/agentes (sparse checkout: Motores, Claude notas, Core kernel inventarios, wordflow raíz emoji)
- Raíz wordflow real copiada: `chat router/Workflow Loop code Yaiwes/_copias-anteriores/wordflow loop code Yaiwes/` (397 archivos vía motor_3, VERIFIED_CLOSED)
- Estado vivo: `chat router/Workflow Loop code Yaiwes/03-ESTADO/` (STATE.json, CHECKPOINT.json, CRAZY_WALL.json, BITACORA.jsonl, HANDOFF.md, este memoria.md)
- Plan/auditoría: `chat router/Workflow Loop code Yaiwes/01-PLAN/PLAN-ACCION-XRAY.md` (incluye MAPA NODO→ESTADO de los 4 objetivos + INPUT-BLOCK verbatim)
- ROOT-MAP: `chat router/Workflow Loop code Yaiwes/01-PLAN/ROOT-MAP-T11.yaml`

## Reglas del Director (verbatim clave)
1. Wordflow loop code Yaiwes = AUTORIDAD canónica del workflow (mecanismo), NO su staff de 18 agentes. El staff propio es `router inteligente universal/agents-yaiwes/agent-*`.
2. deepseek-harness (plugins con el chat) = BASE que conecta todo el wordflow — NO eliminar. Hermes + OpenClaw = base permanente del chat (asistente+sentinelas) con o sin wordflow.
3. Motores canónicos para descarga/extracción/copia/movimiento (hash+read-back). Solo motor_2 queue con GITHUB_TOKEN publica; motor_3 copia física (nunca mirror/move); motor_5 zip_root blob canónico 2516d85d.
4. No GitHub Actions como aceptación. Hugging Face cómputo cpu-basic 16GB (Job Router COMAND-CENTER-1 está RUNNING).
5. 🚩 flag PENDIENTE sin stop ni escalar; nunca PASS sin evidencia; no modificar tests upstream stale.
6. Frontend bloqueado hasta cerrar backend.
7. Checkpoints cada ~30 min: python 'chat router/Workflow Loop code Yaiwes/03-ESTADO/watchdog_checkpoint.py' --summary "..."
8. Capacidades agentes integradas (NO staff): opencode=writer, openhands=fixer, codex=auditor, mirothinker=reasoning (ya cableado como ThinkingSystem), muse_glimmer=micro-loop, research_agent_lab=research, goose=acquisition, mimo_code=writer barato, aider=git patch, kimi_k=research alt. NO integrar: cline/qwen/opendev/agent_zero/smolagents/claude_code (solapados).

## Estado técnico real (verificado)
- Suite loop: 267 passed / 3 stale (g009, g021, ficha loader sys.modules — upstream).
- Suite seals_core: 44/45 (test_ejecutor inexistente contradice fix SIM-01 — stale upstream).
- Hecho: recovery tipado (FAILURE_POLICY 7 kinds en recovery/engine.py), stuck detector, agent_router FAIL_CLOSED→AgentFleetAdapter, LayerRunner (cadena gobernanza), ThinkingSystem, dedup task_runtime canónico (loop core + shim integration), SealsWorker(TaskContract)->NodeResult + agent-45 staff dir, orchestrator_contracts (Mission/Task/ResultEnvelope/Evidence/OracleVerdict), orchestrator_adapters (ComponentAdapter fail-closed + capability map + EvidenceLedger + oracle_verdict + input_shark + create_global_goal solo hermes), O4-19 E2E test, skills_schema/ 24 .dag.yaml, seals_motors toolset (6 motores, manifest verificado), descargas motor_2: munder-difflin, archify, anthropic-skills, scrapling, scrapegraph-ai, agent-reach (VERIFIED_CLOSED, publicados).
- dag_schema.yaml de Seals tiene sección ejecutable steps/edges (engine la requiere fresca).

## Pendientes (DSL-DAG de próximos pasos, en orden)
P1. O4-07..14 invocación real de adapters: faltan command_env de cada componente (rowboat/msaf/orca/omniroute/deepseek_harness/munder_difflin/dagu_dbos/mcp) — configurar runtimes locales (los repos YA están materializados en Componente open soure/ y kernel) y re-test contra sus CLI/SDK reales.
P2. S-07B cableado: anthropic-skills/scrapling/scrapegraph-ai/agent-reach ya descargados — integrar como tools/capabilities (NO subagentes) vía contracts.
P3. S-11: prueba real 3 instancias Seals desde Wordflow (3 workers aislados, evidence por worker). S-12 completion audit.
P4. O4-17 Archify projection (usar runtime/src/core/graph_visual_projection.build_crazy_wall_projection → proyección desde ledger). O4-20 completion audit.
P5. N-2.2: copiar 3 skills frontend desde 'Wordflow loop code Yaiwes/skills' (big-AGI, en repo agentes) a 'Skills agente/' con motor_3 — fuente aún no sparse-fetched.
P6. N-2.3: unificar raíces (renombrar big-AGI requiere OK Director FLAG-6). N-2.11 biblioteca RAG (13 subcarpetas).
P7. Flags externos: N-1.1/N-1.3/N-1.4 (Actions/NVIDIA/gitlinks), N-2.13 (4 archivos nunca adjuntados), N-2.12+frontend gate.
P8. Suite completa ordenada final + evidencia global + README-ARQUITECTURA.

## Gotchas VM/repo
- venv: source ~/.venv-riu/bin/activate para pytest.
- PYTHONPATH loop: raíz+runtime+runtime/src+wordflow_loop (conftest ya lo hace).
- Seals tests: PYTHONPATH=seals_core desde backend/Seals team YAIWES.
- git commit -F falla → usar git commit -m "$(cat file)".
- No commitear checkpoints.sqlite3/watchdog.log (ya en .gitignore).
- gh CLI autenticado (token para motor_2 publish: GITHUB_TOKEN="$(gh auth token)").
- HF: HF_TOKEN_1_NEW (secreto sesión) — token publicado en chat, rotar al terminar.
- Vercel: límite diario histórico en riu-jev-bridge; no usar como aceptación.
- GitHub Actions billing bloqueado → no usar para aceptación (regla Director).


## Regla nueva del Director (verbatim, 2026-10-01)
- "Todo lo que sea del Api y almacenamiento y procesador de cómputo persistencia que necesite el wordflow se va a conectar a router principal."
- "Coloca tu lo que haga falta... si vez que algo falta ustedes complementan." (los 4 archivos N-2.13 NO existen — el siguiente Devin puede complementar si aparecen o registrarlos como cubiertos por materiales equivalentes).

## LOTE SKILLS-UI (descarga en curso, motor_2 cola `chat router/Workflow Loop code Yaiwes/11-EVIDENCIA/motor2-skills-ui/queue.json`, 28 repos)
- Raíz de destino en repo: `router inteligente universal/Componente open soure router inteligente universal/<slug>/` (commit pins + `code/` extraído, publicado por motor_2 en branch devin/1790824641-chat-agent-plan).
- 🚩 TODA LA LISTA = "por verificar integración" (descargar ≠ integrado): npxskillui, recordly, rare-ui, shadcn-skills, firecrawl, firecrawl-cli, firecrawl-mcp-server, firecrawl-skills, emilkowalski-skills, impeccable, getdesign, open-design, headroom, ponytail, find-skills, superpowers, get-shit-done, claude-mem, context-mode, local-ultra-review, one-skill-to-rule-them-all, motionsites, caret-desktop, onlook, plasmic, webstudio, taste-skill, magic-mcp.
- Ya existían (no repetidos): frontend-design, skill-creator, web-design-guidelines, react-best-practices, image-to-code, ui-ux-pro-max, design-to-code, frontend-design-codex, hyperframes×8, cinematic-scroll/web-design-studio, awesome-design.
- Tarea de integración pendiente: tras veredicto motor_2, cablear las que apliquen como skills_schema + tool contracts (capacidades, no staff); web crawlers/context compressors entran como tools del wordflow conectados al router principal.
