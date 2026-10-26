---
name: cli-anything-memoria
description: Orquestador determinista de memoria y almacenamiento (graphiti, agentdb, graphify, memanto, falkordb, postgresql). Sin LLM.
---
Uso: python3 -m cli_anything.memoria --json <grupo> <comando>
- motores estado: CONNECTED o GAP de cada motor.
- memoria guardar SCOPE KEY DATA_JSON: guarda en los motores conectados que permiten escribir.
- memoria cargar SCOPE KEY: lee del primer motor que lo tenga.
- memoria buscar SCOPE QUERY --k N: busca en todos y fusiona sin repetidos.
Entorno: RIU_<MOTOR>_URL de cada motor (ver memoria/motores/levantar_motores.sh). Salida siempre JSON con --json.
