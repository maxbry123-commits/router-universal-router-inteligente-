# ORDEN ORCH-CHAT → agent-3 (P1) — 2026-09-22

**Deadline ~19:22 COT · META: chat desplegado**

## Hardware (verbatim Director + Revisor)
- Requisito Director: Jobs en procesador HF **32 GB RAM** (8 vCPU / 32 GB).
- `cpu-basic` = incumplimiento (no es 32 GB). **PROHIBIDO.**
- Flavor HF que cumple 32 GB hoy: **`cpu-upgrade`**. Úsalo. No digas «el Director nombró cpu-upgrade»; di «cumple 32 GB».
- Puerto **8000**. Job ≠ 32 GB → DETÉN.

## STOP actual (Revisor)
`steps/publish_live/results/publish_live.py` L30 tiene `flavor="cpu-basic"` + SyntaxError (triples). **Reescribe el archivo completo.**

## Checklist P1
1. `publish_live.py` válido (ast.parse OK), sin `'''`/`"""` rotos.
2. Job `cpu-upgrade`, expose 8000, start via `common/router_job_start.py`.
3. GET `/health` → 200.
4. Static Space `riu-chat-yaiwes` con `API_BASE` = endpoint real.
5. crazy_wall: `space_url` + `router_endpoint` + `hardware_flavor=cpu-upgrade`.
6. Smoke chat público. Fail-closed sin HF_TOKEN.

No P2. No redeploy con cpu-basic.
