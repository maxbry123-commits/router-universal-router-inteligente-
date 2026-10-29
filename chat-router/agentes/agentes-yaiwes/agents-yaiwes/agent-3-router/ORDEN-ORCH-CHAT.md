# ORDEN ORCH-CHAT → agent-3 (P1) — MICRO 2026-09-29

**META:** PENDING_VERIFY · GOLDEN `private=False` · smoke live · Job 32GB APLAZADO

## Hechos
- Wall paper CLOSED reabierto.
- Probe sin auth: API/PAGE **401**, `.hf.space` **404** → Space muerto o inaccesible.
- TRIGGER root WAITING_GROK (22-sep) **INVALIDADO**.

## Orden
1. **python_exec** `results/publish_live.py` GOLDEN (ya con `private=False` + visibility). **CERO** regen/rewrite.
2. **NO** marques CLOSED. Status = `PENDING_VERIFY`.
3. No Job esta ronda.

## PASS
`space_url` live ≠401/404 + smoke OAuth → orch/Sentinela cierran CLOSED.
