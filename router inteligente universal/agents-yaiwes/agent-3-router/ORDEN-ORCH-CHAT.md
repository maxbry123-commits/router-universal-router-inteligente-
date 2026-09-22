# ORDEN ORCH-CHAT → agent-3 (P1) — Director 2026-09-22 ~19:22 COT

**Resultado obligatorio:** Static Space HF + Job Router con GET /health 200 y chat vivo.

## Candado HARD (Director)
- El Job SOLO puede usar el procesador **32 GB RAM activo** (8 vCPU / 32 GB).
- PROHIBIDO: cpu-basic, T4, A10G, A100 u otro CPU/GPU distinto.
- Si el modelo propone otro flavor → RECHAZAR y reordenar al 32 GB.
- Si ya hay un Job 32 GB activo del Director → reutilizar ese endpoint; no montar hardware nuevo distinto.

## Pasos
1. Reescribe `steps/publish_live/results/publish_live.py` **sin** `'''` ni `"""` (SyntaxError línea ~83).
2. Job Router puerto 8000 en hardware 32 GB; arranque vía `common/router_job_start.py`.
3. Esperar GET `/health` → 200 (fail-closed).
4. Deploy Static Space `<cuenta>/riu-chat-yaiwes` con `API_BASE` = endpoint real del Job.
5. Anotar `space_url` + `router_endpoint` en `crazy_wall.state.json` y este HANDOFF.
6. Sin `HF_TOKEN` → fail-closed. No reabrir space_readme / space_index / deploy_script.
