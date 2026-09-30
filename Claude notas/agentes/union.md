# union (2026-09-30)
Unidas a main, sin conflictos: bloque2-agentes, bloque3-cadena, bloque3-plugins, bloque3-puentes, bloque3-secretos (resilience.py fusionado automatico con ambos cambios).
Borrados los workflows tmp-*.yml (todos).
Fix: el grupo assistants faltaba en policies.json; se agrego (igual que el fallback en codigo).
Tests en maquina temporal: 97 pasados, 13 omitidos, 0 fallados (policy_config, resilience, model_pool, plugin_host, plugins_bloque3, puentes_plugins, openai_route).
Nota: integration.chat_mvp.app importa huggingface_hub; instalarlo para arrancar.
CI de GitHub Actions sigue bloqueado por facturacion: nada corrido en Actions.
