# union2 (2026-09-30)
- Merge en main de bloque4-banco, -recarga, -salvavidas, -ssh: sin conflictos. Quitados 18 __pycache__/pyc que colo recarga (quedan 2 pyc previos de main, no tocados).
- Hallazgo: host marcaba invalid lifeguard y hf_storage/datasets/skills/compute (I09 runtime_type, I13 sandbox none con permisos). Corregido en sus ficha.json.
- Pruebas por grupo (sandbox Vercel): vault 29 ok, plugin_host 22, plugins_sync 4, plugins_bloque3 12 (incluye fables_enchufe, pasa), puentes 17, lifeguard 19, ssh 15, policy 8, resilience 12, openai_route 3, chat_mvp_app 13.
- Smoke TestClient con RIU_AGENT_API_KEYS: /health 200, /plugins lista 13 (incl. lifeguard, ssh_bridge), POST /plugins/sync 200 sin invalid, /v1/router/models 200.
- Falso positivo del grep de claves: una lista de needles en un test. Sin claves reales.
- Pendiente: guardian en vivo, ssh real, paramiko en requirements.
