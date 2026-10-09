# T05 — Funciones del chat

Backend determinista de funciones solicitadas para el chat. En `SIMULADO=1` no realiza llamadas de red.

| Botón/comando | action_id | función |
|---|---|---|
| Watchdog | watchdog.start/stop | Action Registry |
| /run, /loop | workflow.run | Action Registry |
| /schedule | task.schedule | Action Registry |
| /rewind | rewind | checkpoints |
| /compact | compact | compactación |
| /council | council.ask | council paralelo |
| /archify | archify | Mermaid |
| WORK | /work | RUNNING/PAUSED/CANCELLED/DONE |

Rutas FastAPI: `POST /acciones/{action_id}`, `POST /council`, `POST /rewind`, `POST /compact`, `POST /archify`, `GET/POST /work`.

Aceptación:
```bash
SIMULADO=1 python -m pytest "chat router/Workflow Loop code Yaiwes/10-CHAT-FUNCIONES" -q
```
