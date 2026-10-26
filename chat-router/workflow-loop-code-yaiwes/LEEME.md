# Workflow Loop Code Yaiwes
Destino: `plugins/workflow-loop-yaiwes` (code, contratos) y sus skills (`componentes/skills/workflow-loop-yaiwes`: ECC, frontend, calidad), `plugins/hf_skills`.
Los skills de code y frontend se quedan DENTRO de esta raíz (decisión de Antonio).

## Estado de la reorganización
- `workflow-loop-yaiwes/` (code, contratos): movido desde `plugins/workflow-loop-yaiwes`. Enlace simbólico en la ruta vieja (lo referencian mirror_repos.py, mirror_room.py, programas.json, prompt_rules.yaml, protegidos).
- `hf_skills/` (ficha.json, plugin.py): movido desde `plugins/hf_skills`. Sigue siendo hijo directo de `plugins/` mediante enlace simbólico.
- NO movido: `componentes/skills/workflow-loop-yaiwes` (componentes/ no existe en esta copia).
