# CÓMO ACTIVAR CÓMPUTO CON WEBHOOK (sin GitHub Actions) — HANDOFF

Estado: **diseño listo, todavía no probado de verdad.** Te lo digo así para no inflarlo — es la instrucción exacta, pendiente de crear el
Webhook en GitHub y el Space receptor en HF.

## Cómo funciona (a diferencia de GitHub Actions)
- **GitHub Actions:** GitHub prende su propia máquina, corre el código, se apaga. El cómputo es de GitHub.
- **Webhook:** GitHub NO prende nada. Solo manda un mensaje HTTP ("esto pasó") a una URL. Quien prende el cómputo es quien RECIBE ese
  mensaje — en este caso, un Space de Hugging Face, siempre despierto, escuchando.

## Piezas
1. **Webhook en GitHub** (Settings → Webhooks → Add webhook): URL = la del Space receptor; evento = "push".
2. **Space receptor en HF** (siempre despierto, hardware mínimo): recibe el aviso y, si corresponde, lanza o mantiene vivo el Job del Router.
3. **El Job del Router** (`common/router_job_persistent.py`, ya construido y probado): el cómputo real.

## Cómo lo activa Opus o GPT, sin tocar Hugging Face
1. Hace commit/push a un `chain.yaml` de cualquier agente, en `router inteligente universal/agents-yaiwes/agent-<N>/`.
2. Ese push dispara el Webhook (paso 1) — GitHub lo manda solo, no hace falta ningún token ni acción extra de Opus/GPT.
3. El Space receptor en HF se entera y actúa.
4. Opus/GPT NUNCA necesita una clave de Hugging Face para esto — solo permiso de escribir en GitHub.

## Dónde está el Router y cómo se conecta un agente nuevo
- La URL viva de hoy: leer la línea `LIVE_URL=` en
  `router inteligente universal/agents-yaiwes/ROUTER_JOB_PAUSE.flag` (cambia si el Job se relanza — siempre leer ahí, nunca guardarla fija).
- Un agente nuevo se conecta hablándole como a cualquier API: `POST <LIVE_URL>/chat/route`, `POST <LIVE_URL>/chat/jev`, `GET <LIVE_URL>/health`.
- Para que quede REGISTRADO como conectado: al terminar su tarea, debe hacer un `GET <LIVE_URL>/health` y anotar el resultado en su propio
  `crazy_wall.state.json` bajo la clave `"router_connected"` (así lo hacen ya los demás agentes, ver `common/boot.py::ping_router`).

## Lo que falta, sin inventar que ya está
- Crear el Webhook de verdad en GitHub (necesita el token de administración del repo).
- Construir el Space receptor en HF (hoy no existe; solo existe el Job del Router al que apunta).
- Probar el ciclo completo una vez, de punta a punta.
