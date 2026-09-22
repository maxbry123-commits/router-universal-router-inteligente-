# ORDEN ORCH-CHAT → agent-3 (P1) — post #33 CRITICAL

**META:** space_url + /health · Job **solo 32 GB RAM** · deadline ~19:22 COT

## Causa #33
El modelo envolvió `publish_live.py` en fence markdown y lo truncó → SyntaxError L1.

## TEMPLATE restaurado
`results/publish_live.py` ya es el TEMPLATE bueno (AST OK, guarded_run_job).

## Orden (OBLIGATORIO)
1. Abre `results/publish_live.py`. Si empieza con docstring/`import` y parsea → respuesta = **exactamente esos bytes** (cero markdown, cero fences).
2. PROHIBIDO: regenerar, resumir, envolver en fences, truncar.
3. `python_exec` → `publish()` → Job máquina 32 GB RAM, puerto 8000, GET `/health`.
4. Escribe `space_url` + `router_endpoint` en crazy_wall CLOSED.
5. Fail-closed si ≠32GB.

Id técnico HF 32GB (API): `cpu-upgrade`. No atribuir al Director.
