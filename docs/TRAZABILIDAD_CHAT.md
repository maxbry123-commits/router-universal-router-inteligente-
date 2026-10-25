# Trazabilidad del chat — frontend y backend

Base: `1b916a587c` (23-oct). Rango: hasta `7b2430c8e8` (25-oct).
Commits en backend (`mvp/`, Harness, `router_api_cliente.py`) desde el 15-oct: **106** (Maxbry 57, Claude 45, Code 1: 2, maxbry123-commits 2).
Frontend: ver `docs/AUDITORIA_FRONTEND_XRAY.md` (40 commits, daños D1–D10).
Cambio neto backend desde la base (solo `.py` de mvp, Harness y cliente): 40 archivos, +2260 / −112.

## 1. Flujo de una petición de chat (frontend → backend)

| # | Capa | Archivo | Qué hace |
|---|------|---------|----------|
| 1 | UI | `enviar-mensaje.js` | arma el mensaje, modo, modelo, adjuntos |
| 2 | HTTP | `api.js` | `POST /chat/send` (clave en cabecera) |
| 3 | Router | `mvp/app.py` `_chat_ficha` | capas: formato, system prompt (si ON), modo, constitución/yaiwes/pendientes, anclas, **identidad justo antes del último mensaje** |
| 4 | Permisos | `mvp/control.py` | IA, Agentes, Prompt, pendientes, salas, conexiones (servidor decide) |
| 5 | Modelo | `mvp/app.py` `_llamar_modelo` | Qwen (`compute.py`) o Groq/NVIDIA (`externos.py`) |
| 6 | Herramientas | `plugins/deepseek_harness/server.py` | lista permitida; argumento inválido vuelve al modelo |
| 7 | Cliente | `plugins/router_api_cliente.py` | 403 conserva el motivo (ia=false) |
| 8 | Persistencia | `mvp/hf_store.py`, `mvp/memoria.py`, `mvp/trabajos.py` | historial, pestañas, trabajos (HF) |
| 9 | Resultado | `/chat` (resultado) | incluye `herramientas_usadas`, `finish_reason` |

## 2. Historial backend por tema

| Tema | Commits | Autor | Estado |
|------|---------|-------|--------|
| MVP, auth, bank, Token Plan | 2a42c501b4, d7a2f08db1, 5af8740f06, cfa02a82c1 | Maxbry | OK |
| Autopull / arranque | 1d23427bf0, a8b89b4752, 8d485acab8 | Maxbry, Claude | OK (deshace commit roto) |
| Harness HTTP + almacén | 08fd345e78, a250af6432, c3fc16d487, d0bfa14db8, e680fbfae4, 4865742284 | Maxbry, Code 1 | OK |
| HF store / bucket | 2ef322ed02, 73de741ada, 34910f57ec, b91fe2b572 | Maxbry, Claude | OK (lectura sin caché vieja) |
| MCP JSON-RPC | e2de2b5bc8, b4eb4cdf5a, 4a0fad37b1, 8923a7fd36, 584bca1071 | Maxbry, Claude | OK; clave `?key=`; `salud` nueva |
| Permisos en servidor | 1b916a587c, 62fbb681c4, 8ffec72cd7, cbd1647056 | Claude | OK; `quitar` conexión |
| Capas del prompt | 748db5a6e5, 959d400165, b659f36cd5, c28df985d0 | Claude | OK |
| SDK Qwen / multimedia | 62c3e0d1ee, dd833d5160, 17f382f6a9, 6b48272e65, 35f664f91e | Claude | OK (23 modelos) |
| Identidad del modelo | 0963d2622c, 6d79e78b25 | Claude | OK (antes la tapaba el historial) |
| Groq / NVIDIA | 6d79e78b25, 7b2430c8e8 | Claude | código OK; claves del Space sin verificar en vivo |
| Escalado | 63c588b3cf | Claude | OK |
| Pruebas reales (`pruebas_vivo`) | 2ee2f1ff3a, 9b9f626933, ebdeb5505c, e960e04110, 893b45736c | Claude | OK; t4 necesita IA ON |
| Diagnóstico | e0cc451b2b, c8991a2b93 | Claude | OK |

## 3. Qué se rompió y se arregló en backend

| Fallo | Causa | Arreglo | Prueba |
|-------|-------|---------|--------|
| Modelo respondía «Soy deepseek» | identidad antes del historial | mensaje de identidad justo antes del último | test_app |
| Harness 500 | argumento inválido de herramienta | vuelve al modelo | test_harness |
| 403 sin motivo | cliente perdía la causa | conserva «ia=false» | test_tools_chat |
| `ficha-qwen38max` rechazado | alias antiguo | `canonico()` | test_alias |
| Falsos FAIL de pendientes | mismo `request_id` devolvía resultado guardado | id distinto por corrida | test_pruebas_vivo |
| `/memoria` pisaba historial | lectura fallida | no guarda si falla la lectura | test_memoria |
| Lectura HF vieja | caché | sistema de archivos nuevo | test_hf_store |
| t6 KeyError | tarea sin clave | FAIL controlado | test_pruebas_vivo |

## 4. Lo que falta en backend

1. **Narración en vivo** («el modelo iba diciendo lo que hacía»): no existe progreso por pasos; hay que emitirlo desde el Harness/`_llamar_modelo` (el frontend ya lo espera como `nunca` visible, ver D4).
2. t4 (delegación LLM) exige `permisos.ia=true`, lo activa el Director en el chat.
3. Claves GROQ/NVIDIA en el Space: sin confirmar (sandbox sin red a HF).
4. Modelos de texto restantes y medios sin probar en vivo (Sol/GPT/Grok).
5. Rama por defecto de GitHub sigue en `reorganizacion`.

## 5. Evidencia

- `python -m pytest mvp -q` → 221 passed (última corrida completa).
- Batería e2e: `plugins/chat-router/e2e/todo.sh`.
- Frontend dañado / pendiente (Salida 2): D1 simulador, D2 Detener, D3 selectores, D5 etiquetas de modo, D8 Nuevo proyecto, D9 RUI = 22.
