# 🤗 README HUGGING FACE — Memoria de arquitectura YAIWES
Historial vivo de todo lo que tenemos en Hugging Face: cuentas, Spaces, Jobs, MCP, enlaces, reglas y cómo replicarlo.
Se mantiene igual en GitHub (este archivo) y en HF (dataset `COMAND-CENTER-1/yaiwes-hf-memoria`, si HF permite crearlo).
Nunca se escriben claves aquí: solo nombres de secretos.

## Cuenta
- Cuenta HF: **COMAND-CENTER-1** (claves en GitHub: `HF_TOKEN_1`, `HF_TOKEN_MAXBRY123`, `HF_WRITE_TOKEN` → todas son de esta cuenta).
- Límite conocido: crear Spaces por programa devuelve **402 (pago requerido)**. Crear a mano en https://huggingface.co/new-space sí funciona.
- Guía oficial para que una IA cree Spaces: `curl https://huggingface.co/new-space/agents.md` → usa la CLI `hf` + skill `huggingface-spaces` (https://github.com/huggingface/skills/tree/main/skills/huggingface-spaces).

## Spaces
| Space | Qué es | Hardware | Estado / notas |
|---|---|---|---|
| `COMAND-CENTER-1/claude-github-mcp-backup` | Conector MCP de Claude → GitHub | CPU Upgrade, **nunca dormir** | Sin OAuth desde 26-sep. Vive en una **dirección secreta** (`/<MCP_SECRET_PATH>/mcp`, secreto del Space). Ruta extra `/webhook` relanza el Router. |
| `COMAND-CENTER-1/omniroute-1..5` | OmniRoute (gateway OpenAI-compatible multi-proveedor) | CPU basic | En creación 26-sep (ver workflow `hf-crear-spaces-y-memoria.yml`). |

## Jobs
- **Router central**: Job `cpu-upgrade`, 6 h, lo lanza `.github/workflows/riu-router-job-central.yml` o el `/webhook` del conector. URL cambiante en `router inteligente universal/agents-yaiwes/ROUTER_JOB_PAUSE.flag` (`LIVE_URL=`).
- **Keeper 16 GB**: APAGADO por orden del Director (26-sep). No reencender sin autorización.

## MCP
- Conector de Claude: el de arriba. Para añadirlo en otra IA: misma dirección secreta (pedirla al Director; no se escribe aquí).

## Rutas de IA (Router)
NVIDIA (hasta 4 claves; Kimi más nuevo si existe) → Cerebras → Groq → DeepSeek V4 Flash al final. Sin APIs de Anthropic.

## Historial
- 2026-09-25: GPT añade OAuth al conector (causa de las desconexiones).
- 2026-09-26: Space del conector en nunca dormir; OAuth quitado; dirección secreta; keeper apagado; motores mejorados y replicados; OmniRoute en descarga.
