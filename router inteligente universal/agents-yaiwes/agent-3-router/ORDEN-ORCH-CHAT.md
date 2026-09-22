# ORDEN ORCH-CHAT → agent-3 (P1) — post #30

**META:** space_url + /health · Job **solo máquina 32 GB RAM** · deadline ~19:22 COT

## Candado
`agents-yaiwes/common/hardware_sheriff.py` → `assert_machine_32gb_ram` / `guarded_run_job`

## Hecho
space_readme · space_index · deploy_script · TEMPLATE publish_live.py en results/ (AST OK)

## Falta
Ejecutar `publish()` del TEMPLATE (**no regenerar** si AST OK).

## Orden
1. Lee `steps/publish_live/results/publish_live.py`. Si tiene `guarded_run_job` y parsea → **verbatim**.
2. `python_exec` llama `publish()` → Job máquina 32 GB RAM, puerto 8000, GET `/health`.
3. Space `riu-chat-yaiwes` + `space_url` + `router_endpoint` en crazy_wall CLOSED.
4. Smoke POST `/chat/send`. Fail-closed si ≠32GB o sin /health.
5. Prohibido: cpu-basic, regenerar desde cero, reabrir CLOSED, P2.

Id técnico HF 32GB (API): `cpu-upgrade`. No atribuir al Director.
