# Controles del chat (Router MVP)

## C0 · Inventario (estado tras esta rama)

| Control | Backend (servidor decide) | Frontend (solo muestra) |
|---|---|---|
| IA y agentes ON/OFF | `agent_access_lock` → `Control.d["ia"]`; `decidir()` en `mvp/control.py`; `/chat` y `/mcp` devuelven 403 | `tools-ventana.js` (🧰) y `panel-chat.js` (🔒) comparten `window.RIU_IA` |
| Herramientas ON/OFF | `tools_lock` (lista, `{tool, locked}`); `/mcp tools/list` solo muestra las ON y `tools/call` revalida | ventana 🧰 (clic derecho / mantener pulsado) |
| Conexiones | acción `conexiones` (agregar, activar, descubrir); secretos en `mvp/bank.py` como `CONN_<SERVICIO>_<id>` | `controles-ventana.js` 🔑 (selector, ＋, ON/OFF) |
| Pendientes | acción `checklist` + herramienta `pendientes` | `pendientes-panel.js` 📋 (sección 0) |
| ROOM CONFERENCIAS | acción `salas` + herramienta `sala` (niveles lectura/escritura/admin) | `controles-ventana.js` 🗣 |
| MCP salida | `POST /mcp` (JSON-RPC), 7 herramientas previas + `pendientes` + `sala` + las externas encendidas | — |
| MCP entrada | `mvp/mcp_cliente.py` (HTTPS, Bearer desde el banco, bloquea redes privadas) | conexión de servicio «Servidor MCP» |
| Persistencia | `/almacen` destino `hf`, archivo `chat_estado/control.json` (sin secretos) | aviso si no se puede guardar |
| Banco | `bank.py`: Fernet; el valor nunca vuelve al navegador ni al modelo | campo contraseña, se borra al enviar |
| Ya existían | `tools/agente_tool/llm_tool` en `/chat`, `finish_reason`, `/chat/agents`, `/chat/github/accounts` (listas vacías), `/almacen` | aviso de respuesta cortada en `panel-chat.js` |

Tres permisos separados (`Control.decidir`): **conexión ON** (servicio con al menos una conexión ON), **herramienta ON** (las externas MCP nacen apagadas) y **delegación IA ON** (solo `agente*`/`llm*`; además exige `tools` y el flag del cliente). Una conexión activa no autoriza por sí sola las herramientas.

Límites conocidos: el estado se guarda por `/almacen` (HF); con HF caído se sigue en memoria y la UI lo avisa. Si la lectura inicial falla y luego la escritura funciona, el estado remoto se sobrescribe con el de memoria. Pruebas en vivo en el Space: NO VERIFICADO (Space pausado).

## C9 · ✨ Auto (solo lectura del código existente; no se modificó)

- **Frontend** (`plugins/chat-router/frontend/mode_selector.js`): «✨ Auto» es la fila inicial del selector de modos y el valor por defecto (`localStorage chat.mode_lock.panel`; un id inválido guardado vuelve a Auto). Cada envío lleva `mode_request = {mode_id:"auto", source:"auto"}`; con un modo fijado lleva `{mode_id, source:"button"}`. El front solo propone.
- **Resolución** (`fichas/fichas_qwen/modos/mode_router.py`, `resolve_mode`): precedencia `button_lock > slash_command > auto_classifier > default_mode` (`m05_respuesta_rapida`). En Auto: `/auto` en el mensaje se quita del texto y `classify_auto` aplica las reglas por regex del registro (`modes_registry.json`); sin coincidencia usa el modo por defecto. Auto **nunca** elige un modo autónomo (`AUTO_FORBIDDEN`); esos exigen botón, slash o palabra de gate (`INICIA`, `RUN`, `IMPUTA`).
- **En el Router MVP**: `mvp/` no importa `mode_router` ni lee `mode_request` (solo aparece como campo del esquema MCP `chat`). El selector y el campo viajan, pero hoy el MVP los ignora; el enrutado de modos lo consume `fichas/fichas_qwen/plugin.py`.
