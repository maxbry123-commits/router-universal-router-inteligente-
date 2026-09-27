# T06 — CONTEXTO COMPACTO DE EJECUCIÓN

OBJETIVO: integrar Hermes y OpenClaw como asistentes/supervisores del chat y
orquestador usando SOLO nuestro Router/NVIDIA. No tocar el Router principal.

ALCANCE ÚNICO: chat router/05-AGENTES/asistentes

ARCHIVOS:
- hermes_config.yaml
- openclaw_config.yaml
- hermes.md
- arrancar_asistentes.sh
- puente_asistentes.py
- heartbeat.py
- __init__.py
- tests/__init__.py
- tests/test_asistentes.py
- README.md

## EVIDENCIA DE LOS FORKS REALES

Hermes fork:
- repo: https://github.com/maxbry123-commits/hermes-agent
- default branch real: main
- README actual: CLI `hermes`, selector `hermes model`, gateway `hermes gateway`
- soporta endpoints/modelos propios y proveedores OpenAI-compatible.
- el ref literal `v2026.9.24` NO existe como tag en el fork actual.
- pyproject actual usa version dinámica/placeholder 0.0.0; NO inferir versión por eso.
- usar main/commit real del fork, no `git clone --branch v2026.9.24`.

OpenClaw fork:
- repo: https://github.com/maxbry123-commits/openclaw
- default branch real: main
- package.json actual declara version 2026.9.6.
- el ref literal `v2026.9.6` NO existe como tag en el fork actual.
- config runtime nativa: ~/.openclaw/openclaw.json (JSON5), validación estricta.
- custom providers viven bajo models.providers.
- source install: pnpm install + pnpm build; npm install raíz NO soportado.
- gateway real: `openclaw gateway ...`.

## REGLA SOBRE LOS YAML DE T06

`hermes_config.yaml` y `openclaw_config.yaml` son CONFIG DE NUESTRO ADAPTADOR.
NO fingir que son los archivos nativos de los frameworks.
El adaptador debe traducir esos YAML a variables/comandos/config nativa donde haga falta.

## ROLES
Hermes = planner_supervisor:
plan, critique, review, debate, delegate.

OpenClaw = guardian_supervisor:
plan, critique, review, debate, monitor, heartbeat.

## ROUTER
- base OpenAI-compatible: https://integrate.api.nvidia.com/v1
- modelo por env; Kimi K3 por defecto.
- clave por NOMBRE de variable de entorno; jamás escribir secreto.
- nunca Anthropic.
- SIMULADO=1: cero red.

## ORDEN
1. tests/test_asistentes.py primero.
2. puente_asistentes.py + emit() + SIMULADO.
3. heartbeat.py: >30 min sin heartbeat => ALERTA; normal => NO_REPLY.
4. YAML adaptadores.
5. arrancar_asistentes.sh usando comandos REALES:
   - Hermes: main del fork y CLI/gateway Hermes.
   - OpenClaw: main del fork, pnpm, openclaw gateway.
6. hermes.md.
7. README.
8. pytest + bash -n; corregir solo traceback real.

## STATE HUB
No escribir STATE.json a mano.
Si existe API/función State Hub, usarla.
Fallback permitido: append JSONL a chat router/03-ESTADO/BITACORA.jsonl.

## DESVIACIÓN DEL INTENTO ANTERIOR
El run anterior generó archivos bajo:
chat router/chat router/05-AGENTES/asistentes/...
El recuperador viejo además tomó README de .pytest_cache.
Eso ya fue corregido en infraestructura. NO repetir ni buscar archivos por basename.

## PASS
- archivos completos
- SIMULADO=1 pytest exit 0
- bash -n arrancar_asistentes.sh exit 0
- checks independientes de roles/router/gateway/heartbeat
- informe con salida real
