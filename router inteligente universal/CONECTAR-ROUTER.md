# Conectar CUALQUIER repo, MCP o herramienta al Router único
Actualizado: 2026-09-29. Regla del Director: **un solo Router, todo centralizado**. No se crea un Router por repo. El Router es un servicio web; los demás son clientes que le hablan.
Solo hechos verificados. Lo que no se probó dice SIN VERIFICAR.

## 1. Encontrar la dirección (no se copia a mano)
La dirección del Router vive en un archivo público del repo, línea `LIVE_URL=`:
`https://raw.githubusercontent.com/maxbry123-commits/router-universal-router-inteligente-/main/router%20inteligente%20universal/agents-yaiwes/ROUTER_JOB_PAUSE.flag`
- Si el Job se relanza, la dirección cambia y el lanzador actualiza ese archivo (verificado en `riu-router-job-central.yml`). Por eso cada cliente lo lee cada vez que lo necesita.
- Una dirección copiada a mano (por ejemplo la variable `RIU_ROUTER_URL` de Vercel) se queda vieja al relanzar. Mejor leer el archivo.
- Ese mismo archivo trae `PAUSED=true/false`: con `true` el Router contesta 503 (menos `/health`). Es el interruptor de pausa remoto.

## 2. Cómo se le habla
- `POST <LIVE_URL>/chat/send` con cuerpo JSON `{"message": "...", "max_tokens": 1200}`.
- Cabeceras: `Authorization: Bearer <token de Hugging Face>` y `X-API-Key: <clave del Router>`.
- La respuesta es JSON; el texto viene en `response`, `content`, `text` o `message`.
- Comprobación de vida sin gastar modelos: `GET <LIVE_URL>/health`.
- Verificado en vivo (smoke 2026-09-29): `/health`, `/chat/models`, `/chat/router/status`. SIN VERIFICAR en vivo: `/chat/send` sin `provider` (el smoke solo probó `provider=hf`, que falla; no usar `provider=hf`).

## 3. Qué necesita cada repo cliente (solo nombres, nunca valores)
- Un secreto con el token de Hugging Face (en el Router se llama `HF_TOKEN_1`; el cliente existente lo lee como `HF_TOKEN`).
- Un secreto `RIU_ROUTER_API_KEY`.
- Opcional: `RIU_LIVE_URL` para fijar la dirección a mano (solo pruebas).
- Los valores nunca van en el repo (es público): van en GitHub Secrets del repo cliente.
- Para repartir esos secretos a los repos del Director ya existe el workflow `.github/workflows/riu-propagate-auth-secrets.yml` (usa `router inteligente universal/scripts/propagate_actions_secrets.py`). No se probó en vivo tras la reorganización.

## 4. Sin código nuevo: el cliente ya existe
`chat router/05-AGENTES/colmena/router_cliente.py`, clase `RouterCliente`:
- Lee `LIVE_URL` del archivo público (o de `RIU_LIVE_URL`), llama `/chat/send`, reintenta 3 veces, antepone `[ROL=…]` al mensaje.
- Uso: `RouterCliente().chat(prompt, rol)`. Con `SIMULADO=1` no toca la red (para pruebas).
- Para usarlo desde otro repo se copia ese archivo tal cual (es de una sola pieza, solo usa la librería estándar).

## 5. MCP u otra herramienta
Cualquier cosa que pueda hacer una llamada web usa el mismo contrato: leer el archivo de dirección, luego `POST /chat/send`. No hace falta otro Router ni otro servidor.
- SIN VERIFICAR: que exista un envoltorio MCP del Router. Si se necesita uno, es una tarea aparte y se arma cableando lo ya descargado, no escribiendo desde cero.
- El conector MCP de Claude (Space `claude-github-mcp-backup`) es otra cosa y está protegido: no se toca.

## 6. Reglas
- Nadie relanza el Job del Router salvo el lanzador único y por orden del Director (relanzar apaga el anterior).
- Ningún cliente guarda ni imprime claves.
- Modelos solo por el Router: NVIDIA (hasta 4 claves; Kimi K3 o el más nuevo) → Groq → DeepSeek V4 Flash al final. Sin Cerebras, sin OmniRoute, sin APIs de Anthropic.

## 7. Si el Router se mueve a otro repo
Cambian dos direcciones: `FLAG_URL` en `router_cliente.py` y `REPO_URL` en `agents-yaiwes/common/router_job_persistent.py` (línea 20), más el `git clone` y la URL de la API del archivo de dirección dentro de `.github/workflows/riu-router-job-central.yml`. Los clientes que lean `LIVE_URL` del archivo nuevo siguen funcionando sin más cambios.
