# HANDOFF — Raíz BACKEND del chat

**Carpetas:** `mvp/` (Router FastAPI) · `plugins/deepseek_harness/server.py` (Harness, herramientas) · `plugins/router_api_cliente.py` (cliente HTTP con el motivo del 403).
**Índice con commits por archivo:** `chat/docs/backend/INDICE.md` · **Todos los cambios:** `chat/docs/backend/CAMBIOS.md`
**Instrucciones · daños · pendientes:** `docs/INSTRUCCIONES_DANOS_PENDIENTES.md` · **Trazabilidad:** `docs/TRAZABILIDAD_CHAT.md`

## Rutas del Router (`mvp/app.py`, `mvp/memoria.py`, `mvp/mcp_route.py`)
`GET /health` · `POST /chat` · `POST /chat/send` · `POST /almacen` · `GET /chat/providers[/{id}/models]` · `GET /chat/agents` · `GET /chat/github/accounts` · `POST /plugins/{plugin}/call/{accion}` · `POST /memoria/save` · `GET /memoria/load|search` · `POST /mcp` (JSON-RPC, 13 herramientas, incluida `salud`).

## Flujo de un mensaje
`/chat/send` → `_chat_ficha` (formato, system prompt, modo, constitución/yaiwes/pendientes, anclas, **identidad justo antes del último mensaje**) → permisos en `control.py` → `_llamar_modelo` (Qwen `compute.py` · Groq/NVIDIA `externos.py`, pool de claves del `bank.py`) → Harness (lista permitida de herramientas; argumento inválido vuelve al modelo) → resultado con `herramientas_usadas`.
Persistencia: `hf_store.py` (HF bucket, lectura sin caché), `memoria.py`, `trabajos.py`. Arranque: `run.py` (autopull que deshace un commit roto).

## Verificación
```
python -m pytest mvp -q                          # 221 passed
python3 chat/e2e/cableado.py      # imports, rutas sin prueba, herramientas MCP sin prueba
python3 -m mvp.pruebas_vivo.guion                # pruebas vivas MCP para Sol/Grok/GPT (docs/PRUEBAS_MCP.md)
```

## Pendiente / sin verificar en vivo
D4 pasos en vivo del modelo · claves Groq/NVIDIA del Space · t4 (requiere IA ON) · modelos de texto y medios restantes · rutas `/chat/agents` y `/chat/github/accounts` y módulos `mcp_cliente.py`, `sala_turno.py` sin prueba propia.
