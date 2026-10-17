# 🔵 PROTOCOLO OFICIAL DE ACTIVACIÓN — CHAT YAIWES

## PASO 1 — ESCRIBIR LA TAREA DEL AGENTE

Llamar a `create_or_update_file` para guardar/actualizar:

`router inteligente universal/agents-yaiwes/<agente>/chain.yaml`

El texto de la tarea queda dentro de `chain.yaml`. Ese write ya crea el commit/push en GitHub.

## PASO 2 — ACTIVAR "CORRER AHORA"

Llamar a `github_api` con método **POST** a:

`/repos/maxbry123-commits/router-universal-router-inteligente-/actions/workflows/riu-agents-run.yml/dispatches`

Para un agente concreto, el body correcto según el workflow ACTUAL es:

```json
{
  "ref": "main",
  "inputs": {
    "only": "<carpeta-del-agente>"
  }
}
```

Para Agent 14:

```json
{
  "ref": "main",
  "inputs": {
    "only": "agent-14-orchestrator-msaf"
  }
}
```

**IMPORTANTE:** el workflow actual define `only` con default vacío. Si se manda solo `{"ref":"main"}`, `ONLY` queda vacío y se ejecuta TODO el swarm. Para enviar un mensaje a un solo agente es obligatorio `inputs.only`.

## PASO 3 — GITHUB EJECUTA SOLO

La máquina temporal de GitHub:
- lee `chain.yaml`;
- manda la tarea al modelo configurado;
- valida la respuesta con Sheriff;
- si pasa, guarda el resultado;
- hace commit/push de vuelta al repositorio antes de apagarse.

No se escribe ese runtime cada vez: ya está guardado en el repo.

## PASO 4 — LEER DÓNDE RESPONDIÓ

Usar `get_file`/lectura GitHub sobre:
- `crazy_wall.state.json` → CLOSED/BLOCKED + provider/model/route;
- `steps/<paso>/results/output.txt` → texto real producido;
- `README-DIRECTOR.md` cuando el nodo tenga `append_output_to` para responder al Director.

## REGLA ABSOLUTA

`escribir chain.yaml → commit GitHub → github_api POST workflow_dispatch → runner GitHub → Sheriff → commit/push resultado → leer state/output`

- No usar Hugging Face Jobs para activar agentes.
- HF Jobs solo pueden aparecer dentro de una tarea final que expresamente necesite cómputo/modelos HF.
- No activar todo el swarm para hablar con un solo agente.
- No responder en nombre del agente.
- No declarar PASS sin evidencia real.
- Este protocolo REEMPLAZA cualquier protocolo anterior de activación escrito en este README.
