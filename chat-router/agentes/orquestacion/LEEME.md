# agentes/orquestacion
Movidos desde `plugins/`: `orquestador/` y `parallel/` (con su `ficha.json`).
`plugins/orquestador` y `plugins/parallel` son enlaces simbólicos relativos a esta carpeta: el cargador (`router/integration/plugin_host/host.py`) descubre por nombre de carpeta y los entry_points `plugins.orquestador.plugin:handle` / `plugins.parallel.plugin:handle` siguen resolviendo. No borrar los enlaces.
