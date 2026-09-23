# 🔵 PROTOCOLO OFICIAL DE ACTIVACIÓN — CHAT YAIWES

## FLUJO ÚNICO AUTORIZADO

**1. Escribir la tarea del agente.**  
Guardar/actualizar en GitHub el archivo:

`router inteligente universal/agents-yaiwes/<agente>/chain.yaml`

Eso crea el commit/push con la tarea.

**2. Activar "correr ahora" por GitHub Actions.**  
Hacer un POST a:

`/repos/maxbry123-commits/router-universal-router-inteligente-/actions/workflows/riu-agents-run.yml/dispatches`

Para un agente concreto, usar:

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

**IMPORTANTE:** el workflow actual define `only`; si se envía únicamente `{"ref":"main"}`, `ONLY` queda vacío y se ejecuta TODO el swarm. Para una conversación con un agente debe enviarse `inputs.only`.

**3. El runner temporal de GitHub ejecuta solo.**  
El código ya está guardado en el repo. El runner:
- lee `chain.yaml`;
- ejecuta el runtime del agente;
- envía la tarea al modelo configurado;
- valida la salida con Sheriff;
- si pasa, guarda resultados;
- hace commit/push de vuelta al repo.

**4. Leer la respuesta real.**  
Consultar:
- `crazy_wall.state.json` → CLOSED/BLOCKED, proveedor/modelo/ruta;
- `steps/<paso>/results/output.txt` → salida real producida;
- cuando aplique, `README-DIRECTOR.md` → canal Director ↔ Orquestador.

## PROHIBICIONES

- No usar Hugging Face Jobs para activar agentes.
- No sustituir el POST de `workflow_dispatch` por otro mecanismo.
- HF Jobs solo pueden ser usados por una tarea final que necesite expresamente cómputo/modelos HF.
- No activar todo el swarm para una conversación de un solo agente.
- No responder en nombre del agente.
- No declarar PASS sin evidencia real del runner y del Sheriff.

## REGLA PARA SOL

`Director → escribir chain.yaml/orden → commit GitHub → POST workflow_dispatch con inputs.only → runner GitHub → Sheriff → commit/push resultado → leer estado + output`

Este protocolo reemplaza cualquier protocolo anterior de activación escrito en este README.
