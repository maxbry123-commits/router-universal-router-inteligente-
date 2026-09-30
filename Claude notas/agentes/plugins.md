# Agente plugins (Bloque 3, paso 3) - rama bloque3-plugins

Todo en `router inteligente universal/plugins/<id>/` (ficha.json + plugin.py, enabled_default false). Nucleo (host.py/api.py) NO tocado: se reutiliza host.call y POST /plugins/{id}/call/{action}.

- deepseek_harness (status, invoke): invoke hace POST a RIU_DEEPSEEK_HARNESS_URL + RIU_DEEPSEEK_HARNESS_PATH (def /invoke), clave opcional RIU_DEEPSEEK_HARNESS_API_KEY. Sin URL o sin plugin: degraded con reason.
- fables_enchufe (status, validate): envuelve enchufe/validator_v2.py via repo_validator() del host. Solo lo existente.
- parallel (status, run): N calls {plugin,action,payload,timeout_s} por host.call, max 8 en vuelo, max 32 calls, no se llama a si mismo.
- connectivity (status sin red, check con sondeo): fastapi (/health en RIU_SELF_URL o 127.0.0.1:$PORT), http saliente (allowlist en plugins/connectivity/config.json, override RIU_HTTP_ALLOWLIST), mcp (off si no hay RIU_MCP_URL / RIU_MCP_CONFIG / .mcp.json; no se inventa cliente). Cada transporte: ok/degraded/off.

HALLAZGO: plugins/remote_router (GPT) estaba INVALIDO en el host (I09_runtime_type, I13_none_sin_permisos de enchufe/validator_v2.py). Corregido en su ficha.json (runtime_type compute, sandbox egress-allowlist). Sin eso no cargaba.

Arranque: host.py carga plugins/*/ficha.json; una ficha mala solo marca ese plugin invalid (test test_bad_plugin_does_not_break_startup).
Tests: tests/test_plugins_bloque3.py; workflow temporal tmp-plugins-verify.yml (borrar al cerrar).
Pendiente: URL real del harness DeepSeek; cliente MCP real; activar plugins (enabled_default false).
