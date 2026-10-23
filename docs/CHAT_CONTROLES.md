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
- **En el Router MVP**: desde esta rama `mvp/app.py` (`_chat_ficha`) llama a `mode_router.route_request` con el `mode_request` del frontend: el system block del modo viaja como primer mensaje `system` (salvo en el modo por defecto, que no envuelve para no contradecir las tools autorizadas), el `/modo` se quita del texto y un modo autónomo responde 501 (bucle sin conectar). Ver «Motores» abajo.

## Maxbry UI (skill `componentes/skills/workflow-loop-yaiwes/fromted-yaiwes-frontend-factory`)

Incorporado en `plugins/chat-router/frontend/chat-maxbry.css` (se carga el último) y `maxbry-ui.js`: tokens gris V07 (ya en `shell.css`), geometría tarjeta 12 / botón 10 / sheet 28, iconos de línea del skill (sprite `i-*`), composer con divisor y chips (`tool-btn`), `mode-option` para las filas de selector, `tag-status`/punto de señal (verde en curso, azul encendido, rojo alerta, gris pendiente), `toast` para `#notice` y bandeja «Agregar al chat» (patrón de las referencias Grok/Claude de `frontend/yaiwes/original/FOTOS-REF`).
Composer: fila principal ＋ · 📎 · 🎤 … Enviar; chips Auto · Pensar · IA; el resto de botones (archivos, anclar, sandbox, copiar, conexiones, ROOM, pendientes) viven en la bandeja. Los mismos nodos se reubican, no se clonan. Editor desde 84 px (140 en escritorio) que crece hasta 38 dvh y se amplía con ⤢ (70 dvh); la salida ocupa el 100 % del ancho y el código ajusta línea; si la respuesta se corta aparece **Continuar**.

## Verificación cruzada frontend ↔ backend (acciones que llama el frontend)

| Acción / ruta | Estado en `mvp/` |
|---|---|
| `agent_access_lock`, `tools_lock`, `conexiones`, `checklist`, `salas` | OK (`control.py`) |
| `status`, `estado`, `herramientas_estado` | OK (antes 400: «Probar conexión» y Seguimiento fallaban) |
| `archivos`, `subir`, `archivo_borrar`, `sandbox`, `handoff_texto`, `proyecto` | OK; el contenido va por `/almacen`; anclados, handoff y sandbox viajan al modelo (los `secreto:` nunca) |
| `thinking_mode` (chip Pensar) | OK: `enable_thinking` solo en `qwen3.8-max` (único con interruptor, `modelos.extra_body`) |
| Ficha heredada `nv-*`/`hf-*`/`ask-consil*` sin selector Qwen | usa el modelo por defecto (antes: error «modelo no permitido») |
| `/chat/send`, `/chat/providers…`, `/chat/agents`, `/chat/github/accounts`, `chat_async`, `resultado` | OK |
| `notas`, `pendientes` (organizador LLM), `groq_agentes`, `agente_enlazar`, `tools_estado`, `recurso_probar`, `mirror_*`, `handoff`, `xray`, `descargas`, `mover_raiz`, `auditor_code`, `/memoria/search`, `/chat/org/*`, `/chat/documents`, `/control/*` | NO existen en el MVP (400/404 «accion no soportada»); la UI oculta el organizador y la ventana de staff, el resto muestra el error real |

## Motores que envuelven el system prompt (Router → ficha única → motores → system prompt)

Movidos con `git mv` desde `fichas/fichas_qwen/` a `mvp/herramientas/` (sin código nuevo; solo cambió una ruta en `motor_objetivo.py` y el `cwd` de sus pruebas):
- `modos/`: `mode_router` (resuelve el modo y arma el system block), `validate_modes`, `prompt_layouts` (gobernanza en `system`, tarea sola en `user`), `prompt_import` (prompt importado tras el system block), `objective_store`, `loop_controller` (bucle externo con topes), `motor_objetivo` (vueltas hasta cumplir el objetivo), `mythos_engine`, `validate_contract*`, `modes_registry.json` (el mismo que el selector del frontend) y sus pruebas.
- `instrucciones/`: `rules_engine` + `prompt_rules.yaml` (87 reglas → bloques de sistema).
- `yaiwes_motor.py` junto a `motor_cli.py` (ejecutor JSON con recibos).
- System prompt: `mvp/system-prompt/` (copia con el mismo SHA que `fichas/system-prompt/`).

Conectado en vivo: solo `mode_router` (modo → system block) en `_chat_ficha`. Movidos pero SIN conectar: `prompt_layouts`, `prompt_import`, `loop_controller`, `motor_objetivo`, `mythos_engine`, `rules_engine` y `yaiwes_motor`; los bucles piden un objetivo fijado (`objective_store`) que el chat aún no envía, y el system prompt largo (`mvp/system-prompt/perfiles`) solo lo usan esos bucles. Quedan en su sitio, sin tocar: `programador.py`, `apply_addon.py`, `check_integration.py`, `convert_instrucciones.py`, `qwen_blender_adapter.py`, `test_dsl_cableado.py` y `plugins/puente_chat/plugin.py` (`_prompt_lib`/`_core_render`/`_bloques_capas` están dentro de un módulo de 3.6k líneas).
Efecto visible: Auto solo envuelve cuando una regla del clasificador acierta (agenda, plan, investigación, tool) o cuando eliges un modo; sin regla queda `m05_respuesta_rapida` y NO se añade su texto («sin herramientas»), porque pisaría las tools de GitHub/HF.
