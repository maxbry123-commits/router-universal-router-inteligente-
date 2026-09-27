# T06 — CONTEXTO COMPACTO DE EJECUCIÓN

OBJETIVO: Hermes y OpenClaw como asistentes del orquestador/chat usando SOLO
nuestro camino NVIDIA/OpenAI-compatible, sin Anthropic.

ALCANCE ÚNICO:
chat router/05-AGENTES/asistentes

ARCHIVOS:
- hermes_config.yaml
- openclaw_config.yaml
- hermes.md
- arrancar_asistentes.sh
- puente_asistentes.py
- heartbeat.py
- tests/__init__.py
- tests/test_asistentes.py
- README.md

## Evidencia verificada en los forks

Hermes fork:
- repo: https://github.com/maxbry123-commits/hermes-agent
- main observado: ca16be564d0a95f86bd6da44bb41d39cde9db089
- README actual: CLI hermes, hermes model, hermes gateway.
- docs/providers: provider NVIDIA oficial usa NVIDIA_API_KEY.
- también soporta endpoint OpenAI-compatible con OPENAI_BASE_URL/base_url.
- config admite variables ${VAR_NAME}.

OpenClaw fork:
- repo: https://github.com/maxbry123-commits/openclaw
- main observado: 038b10b48de03f67c191ec6db15b484aebae8a9c
- Gateway = plano de control.
- config real: ~/.openclaw/openclaw.json (JSON5).
- configuración tiene validación estricta; claves desconocidas impiden arrancar.
- provider NVIDIA oficial: id nvidia, auth NVIDIA_API_KEY.
- custom providers se declaran en models.providers con baseUrl/api/model list.
- source install actual: pnpm workspace; no asumir npm install en raíz.

## GAP de refs de la tarea
Los refs escritos originalmente:
- Hermes v2026.9.24
- OpenClaw v2026.9.6
NO existen como refs en los forks actuales (GitHub devuelve 404).
NO inventar tags. Usar main del fork o un SHA real comprobado. El script debe
permitir HERMES_REF/OPENCLAW_REF por env, con main como fallback.

## Configuración preferida
Hermes:
- provider: nvidia
- NVIDIA_API_KEY por env
- modelo por env, Kimi K3 por defecto si está disponible en catálogo.
- no guardar ninguna clave.

OpenClaw:
- provider/model compatible mediante configuración oficial.
- NVIDIA_API_KEY por env.
- config debe ser JSON5/esquema válido; no inventar root keys.
- validar config/doctor antes de arrancar cuando no esté en SIMULADO.

## Roles
Hermes = planner_supervisor:
plan, critique, review, debate, delegate.

OpenClaw = guardian_supervisor:
plan, critique, review, debate, monitor, heartbeat.

## Orden
1. Escribir tests/test_asistentes.py primero (SIMULADO=1, cero red).
2. hermes_config.yaml + openclaw_config.yaml.
3. puente_asistentes.py + emit().
4. heartbeat.py.
5. arrancar_asistentes.sh.
6. hermes.md + README.md.
7. Ejecutar aceptación completa; corregir solo traceback real.

## Estado/eventos
- Nunca escribir STATE.json a mano.
- Si existe State Hub usarlo.
- fallback permitido: append JSONL a chat router/03-ESTADO/BITACORA.jsonl.
- heartbeat >30 min sin actividad => ALERTA; sano => NO_REPLY.

## Reglas
- NO Anthropic.
- NO claves hardcoded.
- NO escribir fuera del ALCANCE, salvo emit() runtime al fallback declarado.
- NO duplicar "chat router/".
- NO copiar README de .pytest_cache u otra tarea.
- Máximo 500 líneas/archivo.
- PASS solo con pytest real exit 0 + bash -n + checks independientes.
