# ORDEN ORCH-CHAT → agent-3 (P1)

**Deadline:** 19:15 America/Bogota 2026-09-22

1. Reescribe `steps/publish_live/results/publish_live.py` **sin** strings triples (`'''` / `"""`). Causa del BLOCK: SyntaxError línea ~83.
2. Arranca Job Router: `cpu-basic`, puerto `8000`, `router_job_start.py`.
3. `GET /health` → 200 (fail-closed si no).
4. Deploy Static Space `riu-chat-yaiwes` con `API_BASE` = endpoint real del Job.
5. Anota `space_url` + `router_endpoint` en `crazy_wall.state.json` y `HANDOFF.md`.
6. Sin `HF_TOKEN` → fail-closed. No reabrir space_readme / space_index / deploy_script.
