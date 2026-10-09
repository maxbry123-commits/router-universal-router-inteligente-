# ROUTER-FINGERPRINT — yaiwes.router-fingerprint/v1

Generado: 2026-10-01T16:14:46Z (hechos verificados; sin secretos)

## Componentes
- **State Hub eventos v2 + chain** — `ACTIVE` sha:4c13ed73f4d34ffe tests:6 passed in 0.79s (router inteligente universal/integration/chat_mvp/ui_bridge.py)
- **Runtime T-11 (lease/STUCK/policy/checkpoint/bootstrap)** — `ACTIVE` sha:f4fdff71b14f9028 tests:12 passed in 0.03s (router inteligente universal/integration/chat_mvp/task_runtime.py)
- **Skill runtime v1** — `ACTIVE` sha:03dc35ba1d81922e tests:4 passed in 0.02s (router inteligente universal/integration/chat_mvp/skill_runtime.py)
- **Tool contracts Hermes/OpenClaw** — `ACTIVE` sha:2c1adc44ac4344a4 tests:4 passed in 0.02s (router inteligente universal/integration/chat_mvp/tool_contracts.py)
- **Gobierno Sheriff/Judge/Sentinel/Mirror** — `ACTIVE` sha:8da41ce31ef31e28 tests:41 passed in 0.14s (chat router/Workflow Loop code Yaiwes/05-AGENTES/gobierno/sheriff.py)
- **Evidencia gate (buscadores/verificador/puerta)** — `ACTIVE` sha:d50e6f73175b4134 tests:30 passed in 0.15s (chat router/Workflow Loop code Yaiwes/11-EVIDENCIA/puerta.py)
- **Checkpoint guard + watchdog** — `ACTIVE` sha:35b0dee238e3d5de tests:sin tests (chat router/Workflow Loop code Yaiwes/03-ESTADO/watchdog_checkpoint.py)

## Externos / gaps
- Router permanente HF Job: RUNNING cpu-basic 16GB /health 200 verificado 2026-10-01
- CI GitHub Actions verify: BLOCKED — billing lock de cuenta, el job nunca arranca
- E2E GitHub público: BLOCKED — rate limit sin GITHUB_TOKEN
- Graphiti/Graphify runtime: CONFIGURED — código descargado, sin probe activo
- Redis/Postgres/FalkorDB: CONFIGURED — componentes descargados, sin runtime conectado
- T-06 visual: PARTIAL — agente de pruebas sin cupo; sin capturas ni segunda pasada
- Vercel: UNKNOWN — sin acceso autenticado en esta sesión
- OpenAI real response: UNKNOWN — sin clave provista en esta sesión
