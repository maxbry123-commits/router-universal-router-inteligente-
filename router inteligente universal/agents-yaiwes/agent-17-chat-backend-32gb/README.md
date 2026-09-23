# ⛔ CONTRATO ÚNICO DE ACTIVACIÓN DE AGENTES — CHAT YAIWES

**Regla obligatoria del Director.**

La ÚNICA vía autorizada para activar estos agentes es:

`GitHub commit/push de la tarea → GitHub Actions workflow_dispatch → runner temporal de GitHub → agente ejecuta → commit/push del resultado al repo`

## Flujo obligatorio

1. Sol/Director escribe o actualiza la tarea del agente en `chain.yaml` (o su archivo de instrucciones autorizado) y hace commit/push en GitHub.
2. Sol activa el workflow guardado mediante **GitHub Actions `workflow_dispatch`**, apuntando únicamente al agente solicitado.
3. El runner temporal de GitHub ejecuta el runtime del agente.
4. El agente usa el Router/LLM configurado, ejecuta su tarea y genera evidencia/resultado.
5. El runner hace commit/push del resultado de vuelta al repositorio antes de finalizar.

## Prohibiciones

- **PROHIBIDO usar Hugging Face Jobs para activar un agente.**
- **PROHIBIDO sustituir el dispatch de GitHub por HF Jobs.**
- HF Jobs solo pueden participar cuando la tarea final del agente requiera expresamente encender/probar un modelo o cómputo en Hugging Face.
- No activar todo el swarm cuando el Director pidió un solo agente.
- No responder en nombre del agente.
- No declarar PASS sin resultado/evidencia real commiteada por el agente.

## Regla para Sol

Si el Director dice “activa Agent X”:
`escribir tarea → commit GitHub → workflow_dispatch solo Agent X → esperar resultado → leer commit/evidencia`.

No inventar otro mecanismo.
