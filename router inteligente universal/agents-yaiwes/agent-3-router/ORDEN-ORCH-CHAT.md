# ORDEN ORCH-CHAT → agent-3 (P1) — Director via Sentinela 2026-09-22

**Deadline:** ~19:22 COT | **META:** chat desplegado YA

## CANDADO ABSOLUTO
- Flavor Job HF = **`cpu-upgrade`** (32 GB RAM). Único permitido.
- PROHIBIDO: `cpu-basic`, GPU (T4/A10/A100), cualquier otro.
- Puerto Job: **8000**. Si ves Job ≠ cpu-upgrade → DETÉN y reordena.

## Checklist P1 (solo esto)
1. Reescribe `publish_live.py` SIN strings triples (`'''`/`"""`).
2. Lanza Job Router **cpu-upgrade:8000** (+ `common/router_job_start.py`).
3. GET `/health` → 200 (fail-closed).
4. Static Space **`riu-chat-yaiwes`** con `API_BASE` = endpoint real del Job.
5. Anota en crazy_wall: `space_url` + `router_endpoint`.
6. Smoke: chat público responde.
7. Sin HF_TOKEN o Job ≠ cpu-upgrade → fail-closed.

No P2. No reabrir space_readme/space_index/deploy_script.
