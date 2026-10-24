# Router (Edificio 1) — arquitectura

Router ➡️ ficha única ➡️ motores (modo, formato, constitución) ➡️ system prompt ➡️ Harness ➡️ modelo.

| Pieza | Dónde | Qué hace |
|---|---|---|
| Puerta | `mvp/app.py` | `/chat`, `/chat/send`, `/almacen`, `/plugins/{plugin}/call/{accion}`, `/mcp` (clave por `X-API-Key`, `Bearer` o `?key=`) |
| Permisos | `mvp/control.py` | IA, Agentes, System prompt, herramientas, conexiones y salas; el servidor decide, `/mcp` y `/chat` devuelven 403 si está OFF |
| Banco | `mvp/bank.py` | claves cifradas (Fernet); el valor nunca vuelve al navegador ni al modelo |
| Ficha | `mvp/modelos.json`, `mvp/modelos.py` | 23 modelos Qwen del Token Plan; texto por `/compatible-mode`, imagen/voz/ASR/video por `mvp/multimedia.py` |
| Prompt | `mvp/prompt.py`, `mvp/prompts/`, `mvp/system-prompt/` | formato de salida siempre; system prompt completo solo con el botón ON (apagado por defecto) |
| Motores | `mvp/herramientas/modos/` | `mode_router` resuelve el modo y arma el bloque system; el resto está movido y sin conectar |
| MCP | `mvp/mcp_route.py`, `mvp/mcp_cliente.py` | salida: herramientas del chat; entrada: servidores MCP externos con Bearer del banco |
| Salas | `mvp/sala_turno.py` | un turno de ROOM CONFERENCIAS: cada agente o modelo responde en la sala |

Arranque en HF: `boot.sh` del Space clona `main` de GitHub y ejecuta `python -m mvp.run`. El Space solo trae `Dockerfile`, `boot.sh` y `README.md`.
