# 🔵 PROTOCOLO ÚNICO DE ACTIVACIÓN DE AGENTES — DIRECTOR

Así, paso por paso:

**1. Escribo la tarea del agente.** Llamo a una función que guarda un archivo en GitHub (`create_or_update_file`), con la ruta `agents-yaiwes/<agente>/chain.yaml` y el texto de la tarea adentro. Eso ya es un commit.

**2. Aprieto el botón de "correr ahora".** Llamo a otra función (`github_api`, método POST) a esta dirección:

`/repos/maxbry123-commits/router-universal-router-inteligente-/actions/workflows/riu-agents-run.yml/dispatches`

con:

```json
{"ref":"main"}
```

Eso enciende la máquina de GitHub.

**3. Ahí, sola, esa máquina hace esto** (código ya guardado en el repo, no se escribe cada vez):
- Lee el `chain.yaml` del agente.
- Le manda la tarea a DeepSeek (por la cuenta HF del Director).
- Revisa la respuesta con el Sheriff.
- Si pasa, guarda el resultado y hace commit/push solo.

**4. Yo leo dónde respondió.** Se consulta:
- `crazy_wall.state.json` → dice si quedó CLOSED o BLOCKED y qué modelo usó.
- `steps/<paso>/results/output.txt` → contiene el texto real producido.

## REGLA ABSOLUTA

- Activar agentes por GitHub, usando el POST de `workflow_dispatch`.
- NO usar Hugging Face Jobs para activar agentes.
- HF Jobs solo intervienen si el resultado final de una tarea necesita explícitamente encender/probar un modelo en Hugging Face.
- Sol no responde por el agente: lee el resultado real escrito por el runtime.
- Este protocolo REEMPLAZA cualquier protocolo anterior de activación escrito en este README.
