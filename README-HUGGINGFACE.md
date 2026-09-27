# 🤗 README DEL ROUTER — Estado real y memoria de arquitectura YAIWES
Actualizado: 2026-09-27. Cómo está montado hoy el Router, dónde vive cada pieza y cómo se usa. Sin claves: solo nombres de secretos.

## Cómo está montado (lo que se usa hoy)
| Pieza | Dónde vive | Costo | Notas |
|---|---|---|---|
| **Router** (FastAPI) | Job HF **cpu-basic 16 GB de pago**, siempre encendido, vida 48 h y se relanza | ~$0.01/h (~$7/mes) | Lo lanza `.github/workflows/riu-router-job-central.yml`. Al lanzar uno nuevo apaga el anterior. Dirección actual en `router inteligente universal/agents-yaiwes/ROUTER_JOB_PAUSE.flag` (`LIVE_URL=`). |
| **OmniRoute** v3.8.51 | **Dentro de la misma máquina** del Router, en `127.0.0.1:20128` | incluido | Arranca con `router inteligente universal/keeper/start_omniroute.sh`. El Router lo expone en `/omniroute/*` (`/omniroute/status`, `/omniroute/v1/models`, `/omniroute/v1/chat/completions`). Prueba: `.github/workflows/prueba-omniroute-router.yml`. |
| **Conector MCP de Claude** | Space `COMAND-CENTER-1/claude-github-mcp-backup` | $0 (CPU basic) | Sin OAuth. Dirección secreta `/<MCP_SECRET_PATH>/mcp`. Pendiente: moverlo dentro de la máquina del Router con letrero fijo en Vercel. |
| **Chat** (pantalla) | Vercel `riu-jev-bridge` → https://riu-jev-bridge.vercel.app | $0 | Función `/api` reenvía al Router con las claves de Vercel. Pendiente: base Open WebUI/chat descargado con skills del Director. |

## Cómo llamar al Router
- Cabeceras: `Authorization: Bearer <HF_TOKEN>` (entrada al Job) + `X-API-Key: <RIU_ROUTER_API_KEY>`.
- Rutas: `/health`, `/chat/send`, `/chat/providers`, `/chat/agents`, `/chat/documents`, `/chat/conversations`, `/chat/dag/run`, `/control/*`, `/groups`, `/workflows`, `/omniroute/*`.

## Rutas de IA
NVIDIA (hasta 4 claves; Kimi más nuevo si existe) → Cerebras → Groq → DeepSeek V4 Flash al final. Sin APIs de Anthropic. OmniRoute añade sus proveedores gratuitos por `/omniroute/v1`.

## Agentes y motores
- Loop del plan de 4 objetivos: `.github/workflows/mini-router-plan-4-objetivos.yml` (cada hora; resultado como rama + PR en repo agentes, con copia de respaldo).
- Descargas (motor canónico mejorado): cadenas `agents-yaiwes/agent-40..44`. Replicador de motores a todos los repos: `.github/workflows/replicar-motores.yml`.

## Cuenta HF
`COMAND-CENTER-1` (secretos: `HF_TOKEN_1`, `HF_WRITE_TOKEN`, `HF_TOKEN_MAXBRY123`). Crear Spaces gratis por API → 402; con hardware de pago en la misma llamada → OK.
Spaces `omniroute-1..5`: PAUSADOS (no cobran); OmniRoute vive ahora dentro del Router.

## Planes y handoff
`chat router/PLAN-DSL-DAG-CHAT-AGENTES-INFRA.yaml` · `chat router/HANDOFF-MAESTRO.md` · instrucciones del Director: `chat router/INPUT-BLOCK-VERBATIM-*.md`.

## Historial
- 2026-09-25: GPT añade OAuth al conector (causa de desconexiones).
- 2026-09-26: OAuth quitado, dirección secreta; motores mejorados y replicados; Router pasa a 16 GB de pago.
- 2026-09-27: OmniRoute dentro de la máquina del Router; limpieza de piezas sueltas (keeper, Spaces de prueba, agentes 24–39 sin uso, vercel-ui viejo).
