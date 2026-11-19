# Chat en Vercel (funcion serverless) — el trigger que despierta el router

Por que: los Spaces de HF se duermen y mientras duermen HF devuelve **404**.
La UI no puede vivir en un Space dormido, asi que:

    movil -> Vercel (estatico, sin CPU) -> /api/chat (funcion) -> Space del router

`/api/chat` es el TRIGGER: llama al Space del Grupo 1 y, si esta dormido o
reiniciandose (404/503), espera y reintenta hasta que despierte. La primera
visita lo despierta (HF despierta al primer visitante).

## Despliegue (1 comando)

```bash
cd vercel
export VERCEL_TOKEN=<tu token>          # nunca en el repo
npx vercel --prod --token "$VERCEL_TOKEN" \
  --build-env ROUTER_API_KEY="$UNIVERSAL_KEY" \
  --env ROUTER_API_KEY="$UNIVERSAL_KEY" \
  --env ROUTER_BASE_URL=https://comand-center-1-space-grupo-1-router-mvp-1.hf.space
```

Variables de entorno del proyecto (Vercel > Settings > Environment Variables):

| Variable | Valor |
|---|---|
| `ROUTER_API_KEY` | la clave del router (la misma que va en `x-api-key`) |
| `ROUTER_BASE_URL` | `https://comand-center-1-space-grupo-1-router-mvp-1.hf.space` |
| `ROUTER_MIRRORS` | los 3 espejos del Grupo 1 separados por coma (opcional) |
| `TRIGGER_INTENTOS` | reintentos mientras el Space despierta (def. 14) |
| `TRIGGER_PAUSA_S` | pausa entre reintentos (def. 5 s) |

## Ficheros

- `api/chat.py` — la funcion serverless (solo libreria estandar).
- `build_public.py` — copia `chat-router/chat` a `public/`.
- `public/` — el chat estatico (lo genera `build_public.py`).

El chat detecta el host: en `*.vercel.app` usa `/api/chat`; en el Space, el proxy directo.
