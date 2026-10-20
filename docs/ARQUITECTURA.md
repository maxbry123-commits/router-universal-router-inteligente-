# Arquitectura: dos edificios

## Edificio 1: Router + fichas + system-prompt/SDK
Carpetas `router/` y `fichas/`. Decide a quien le toca cada trabajo, guarda el banco de claves y arma el prompt de cada ficha. No ejecuta el chat.

## Edificio 2: Harness DeepSeek + plugins
Carpeta `plugins/`. Ejecuta el trabajo: chat-router (pantalla del chat), workflow-loop-yaiwes (bucle de trabajo), agentes, memoria/almacenamiento y motores de descarga.

## Regla entre edificios
Solo HTTP: `POST /plugins/<id>/call/<accion>`. Un edificio no importa codigo del otro.

## Circuito
Router -> fichas/prompt (system-prompt, reglas) -> HTTP -> plugins del Harness -> chat (respuesta al usuario).

## Plugins y carga
Cada plugin tiene `ficha.json` con `ejecucion.entry_point` (`plugins.<id>.plugin:handle`). El cargador (`router/integration/plugin_host/host.py`) solo acepta entry_points que empiezan por `integration.` o `plugins.`, y busca los plugins en `plugins/` de la raiz (o en `RIU_PLUGINS_DIR`).

## Protegido (no tocar)
plugins/memoria, hf_storage, hf_datasets, hf_skills, hf_compute, motores, motores-descarga, deepseek_harness, router/banco y todo `componentes/`.
