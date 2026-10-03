# README ARQUITECTURA — YAIWES Router (watchdog 2026-10-03T08:44:22Z)

Generado por watchdog_checkpoint.py — SOLO hechos verificados; lo no comprobado queda UNKNOWN/BLOCKED.

## Estado verificado
- Suite local: UNKNOWN
- ROOT-MAP-T11: FAIL
- Router permanente HF: RUNNING cpu-basic 16 GB, /health 200 (verificado 2026-10-01)
- CI GitHub Actions verify: BLOCKED (cuenta con billing lock; job nunca arranca — no es código)

## Capas activas (con tests)
- integration/chat_mvp/ui_bridge.py — State Hub: eventos v2 + chain_prev + CAS append (6 tests)
- integration/chat_mvp/task_runtime.py — claim/lease, STUCK, failure policy, crash/resume, WorkerBootstrap, workspaces, run ledger (12 tests)
- integration/chat_mvp/skill_runtime.py — yaiwes.skill-runtime/v1 (4 tests)
- integration/chat_mvp/tool_contracts.py — tools Hermes/OpenClaw con rutas verificadas (4 tests)
- chat router/05-AGENTES/gobierno/ — Sheriff, Judge, Sentinel, MirrorManager, MirrorFactory (41 tests)
- chat router/11-EVIDENCIA/ — buscadores (timeout duro), verificador, puerta, evidence_pack

## Pendientes (🚩)
- E2E GitHub público (rate limit sin token)
- Autenticación real de reviewers externos; integridad criptográfica de eventos (hash local, no firma)
- T-06 visual: agente de pruebas sin cupo (sin capturas ni segunda pasada)
- Runtimes Graphiti/Graphify/Redis/etc. descargados pero sin probe activo
- Vercel: sin acceso autenticado; límite diario no verificable
