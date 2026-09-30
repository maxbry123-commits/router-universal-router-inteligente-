# CLAUDE PRIMARY DIRECT — Vercel -> HF -> GitHub

Estado: preparado. Esta es la ruta PRINCIPAL cuando Claude tenga disponible el conector oficial de Vercel.

## Prioridad

1. Vercel oficial -> Sandbox/direct bridge.
2. HF Router directo.
3. MCP personalizado de Anthropic solo como respaldo.

## Flujo

```text
Claude
  -> Vercel MCP oficial
  -> Vercel Sandbox persistente / riu-jev-bridge
  -> /api/direct
       |-> mode=router -> LIVE_URL dinamica -> HF Router 16 GB
       |-> mode=mcp    -> HF MCP directo -> 14 tools -> GitHub
```

La ruta Vercel no depende del registro del MCP personalizado de Anthropic.

## Bridge

Proyecto Vercel: `riu-jev-bridge`

Endpoint preparado:
- `POST /api/direct`
- `GET /api/health`

El bridge resuelve la direccion actual del Router leyendo `ROUTER_JOB_PAUSE.flag`; no depende de que `RIU_ROUTER_URL` se actualice manualmente.

### mode=mcp

Body:
```json
{"mode":"mcp","tool":"connection_status","arguments":{}}
```

Herramientas permitidas: las 14 herramientas del MCP de GitHub.

### mode=router

Body:
```json
{"mode":"router","method":"GET","path":"/health"}
```

Para una llamada de chat:
```json
{"mode":"router","method":"POST","path":"/chat/send","body":{"message":"ping","provider":"auto","model":""}}
```

## Variables privadas

No guardar valores en GitHub.

- `RIU_DIRECT_BRIDGE_KEY` (puede reutilizarse temporalmente `RIU_CHAT_PASSWORD`)
- `RIU_ROUTER_API_KEY`
- `HF_CONTROL_JOBS_TOKEN` para la ruta del HF Job
- `HF_MCP_DIRECT_URL` para la ruta MCP directa completa

Compatibilidad temporal: `HF_TOKEN` / `HF_TOKEN_1` solo si siguen siendo validos.

## Regla para Claude

Si el custom MCP aparece como "reconnect" o desaparecen sus tools:
- NO tocar/reiniciar Hugging Face.
- NO rotar claves.
- Usar Vercel como ruta principal.
- Probar primero `/api/health`.
- Ejecutar la tarea por `mode=mcp` o `mode=router`.
- Solo si tambien falla Vercel, diagnosticar HF.

## Sandbox

Nombre recomendado: `yaiwes-direct`.

Usar Sandbox persistente. Si la sesion se apaga por timeout, reanudar el mismo sandbox por nombre; no crear uno nuevo para cada llamada.
