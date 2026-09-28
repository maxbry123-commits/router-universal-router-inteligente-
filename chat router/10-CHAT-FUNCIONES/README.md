# T05 — Funciones del chat

Backend independiente para las funciones solicitadas del chat YAIWES.

```text
UI/Comando → Action Registry / FastAPI → Council | Rewind | Compact | Archify | WORK → JSON
```

| Botón/comando | action_id | función |
|---|---|---|
| Watchdog iniciar/parar | `watchdog.start/stop` | controla watchdog |
| Run / Loop | `workflow.run` | inicia workflow |
| Pause / Resume | `workflow.pause/resume` | pausa/reanuda |
| Schedule / Cancel | `task.schedule/cancel` | agenda/cancela |
| Pool | `pool.dispatch` | envía al pool |
| Documento | `document.attach` | adjunta referencia |
| Comando | `command.execute` | registra comando |
| Memoria | `memory.search` | consulta memoria |
| Browser | `browser.open` | abre URL |
| Council | `council.ask` | consejo paralelo |
| Rewind | `rewind` | vuelve a checkpoint |
| Compact | `compact` | crea parche de recuperación |
| Archify | `archify` | genera Mermaid |

Rutas: `POST /acciones/{action_id}`, `/council`, `/rewind`, `/compact`, `/archify`, `GET/POST /work`.

```bash
SIMULADO=1 python -m pytest "chat router/10-CHAT-FUNCIONES" -q
```
