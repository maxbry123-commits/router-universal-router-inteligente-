# CIERRE X-RAY — LOOP CODA (8 segmentos)

Ámbito único: `maxbry123-commits/router-universal-router-inteligente-`.
Raíces autorizadas: `router-mvp/` (Router MVP + fichas) y `chat-router/` (Harness DeepSeek, YAIWES, SWE CODE, SWEN, OpenClaw UI).
No crear otra raíz, otro router, GitHub Actions, LFS ni desplegar fuera del repositorio autorizado.

## Estado de verificación
- Base tomada antes de corregir: `fb3437207d5014b0d2ca6101310fe2badbca95f4`.
- Correcciones realizadas:
  1. `e28ac9826b2e802d42f5fe88a6bcc6297f0d0a29`: identidad del proveedor real en YAIWES; reenvío de métricas Router → Harness → `/chat/send`; métricas al reanudar tareas. Prueba añadida: `chat/backend/mvp/test_xray1_trazabilidad.py`.
  2. `0e19e3cddce1c81c88afc014d0506560ecb4ae94`: cancelar HTTP no-stream del bridge con AbortSignal; no rotar claves ni saltar servidor después de Detener.
  3. `d88a8e5735ebbddb6eb23db8949b7540cd6efa20`: detener también el descubrimiento `GET /models`, cerrar failover al cancelar; pruebas nuevas `SWE CODE/web-bridge/test/xray2_cancelacion.test.mjs`.
- Todos los cambios anteriores están dentro de `chat-router/`. Sin cambios al repositorio independiente OpenClaw.
- Auditoría estática: realizada. Pruebas de integración locales y proveedores reales: **NO EJECUTADAS / NO CERTIFICADAS**. Despliegue HF, proxy, Gateway OpenClaw: **NO CERTIFICADOS**.

## Segmentos de cierre

| Segmento | Alcance | Estado | Criterio para PASS real |
|---|---|---|---|
| 1 | Reconstruir diff e instrucciones y descartar GAPS obsoletos | EN PROGRESO | diff por SHA y archivos trazados |
| 2 | Banco, autenticación, secretos y roles | CÓDIGO CORREGIDO PARCIAL; PRUEBAS AÚN SIN EJECUTAR | no secretos en logs/LS; 401/403; operador individual |
| 3 | Fichas y Router MVP, Groq/NVIDIA, SSE, contexto, latencia | CÓDIGO CORREGIDO; PRUEBAS SIN EJECUTAR | pruebas unitarias y llamada real por id |
| 4 | Harness, permisos Tools ON/OFF, tools, MCP, checkpoint | CÓDIGO CORREGIDO PARCIAL; PRUEBAS PENDIENTES | llamada de herramienta y reanudación con recibo |
| 5 | Router SWE, SSE, cancelación, fallback y métricas | PARCHE APLICADO; TEST E2E PENDIENTE | pruebas de cancelación y SSE reales |
| 6 | Frontend YAIWES, modelos vs ejecutores y progreso | PENDIENTE DE E2E | browser: selector, controles, respuesta parcial |
| 7 | Plugin de OpenClaw UI y contrato bidireccional | PENDIENTE DE E2E REAL | Control UI del Gateway ejecutando plugin instalado |
| 8 | Pruebas cruzadas, versión desplegada HF/Vercel y cierre | BLOQUEADO HASTA PRUEBAS | SHA desplegado, contratos API, PASS/GAP/BLOQUEO |

## Pruebas solicitadas (no ejecutadas aquí)
Desde la raíz, con dependencias y PYTHONPATH existentes:
```bash
PYTHONPATH="chat-router/chat/backend/mvp:chat-router/chat/backend:chat-router:router-mvp" python3 -m unittest mvp.test_xray1_trazabilidad mvp.test_xray3_aceleradores
PYTHONPATH="chat-router/chat/backend/mvp:chat-router/chat/backend:chat-router:router-mvp" python3 -m unittest mvp.test_externos_nuevos mvp.test_externos_a5
node --test "chat-router/SWE CODE/web-bridge/test/xray2_cancelacion.test.mjs"
node --test "chat-router/SWE CODE/web-bridge/test/respaldo_stream.test.mjs"
```
No activar GitHub Actions ni cambiar el despliegue para ejecutar estas pruebas.

## Reglas de cierre
- PASS de código = fuente y rutas inspeccionadas; PASS de ejecución requiere prueba real.
- Los ids de Groq/NVIDIA no se consideran DISPONIBLES hasta consultarlos con las credenciales y permisos reales.
- Ante un fallo después de emitir texto, preservar parcial/checkpoint y nunca duplicar una operación con efectos.
- El usuario no autorizó modificar `maxbry123-commits/openclaw` ni `~/.openclaw/openclaw.json`.
- Mantener este archivo como bitácora de segmentos; no declarar DONE total mientras queden bloqueos.

## Segmento 2 — persistencia de secretos (parche)
- `SWE CODE/web-bridge/src/server.js`: POST/DELETE de claves confirma solo después de escritura cifrada; una inyección autorizada por petición tampoco activa claves cuando falla el banco. Retorna 503 `BANCO_NO_GUARDADO`/`BANCO_NO_BORRADO` sin secretos.
- `chat/frontend/swe-claves.js`: exige `local:true` para confirmar escritura; distingue banco local de respaldo externo `persistido:true`, evitando prometer persistencia tras reinicios del Space.
- Pruebas ampliadas: `SWE CODE/web-bridge/test/seguridad.test.mjs` y `chat/frontend/test/swe-claves.test.mjs`. Aún no ejecutadas en entorno Node real.
- Pendiente: verificar servidor real, caja de claves HF persistente, publicación cifrada en rama exclusiva y permisos del operador. No hay nuevo router ni terceros.

## Segmento 3 — Router MVP, fichas y aceleradores (parche X-Ray)
- Fichas existentes: `router-mvp/fichas/fichas_qwen/fichas/politicas_modelo.json` verificada en lectura; sin mover la ficha ni cambiar las políticas Qwen.
- `chat/backend/mvp/compute.py`: conservar los IDs reales de tool_calls; si NVIDIA/Groq omiten uno, generar un identificador único para que el Harness pueda contestar el resultado. Argumentos vacíos normalizados a `{}`.
- `chat/backend/mvp/externos.py`: no declarar éxito si el stream terminó sin texto ni herramientas; el catálogo `GET /models` de una clave no bloquea automáticamente un modelo permitido para otras claves con permisos distintos. Nunca se cambia el modelo solicitado.
- Prueba nueva: `chat/backend/mvp/test_xray3_aceleradores.py` (sin credenciales reales; simulación).
- Verificado estáticamente: contratos de `politicas_modelo.json`, `compute.py`, `externos.py`, `app.py` y pruebas anteriores. Pendiente: ejecución de las pruebas y test real de proveedor/Space.

## Segmento 4 — Harness DeepSeek / Tools ON-OFF / MCP / Checkpoint
- Cambio solo en GitHub dentro de `chat-router/`; Hugging Face no se tocó, el mirror existente debe sincronizar desde GitHub.
- `chat/backend/deepseek_harness/server.py`: el catálogo ofrecido al modelo excluye `agente`/`loop` sin Tools ON + Agente ON y excluye `llm` sin Tools ON + LLM ON; las herramientas MCP internas conservan su comportamiento y el Router vuelve a comprobar sus permisos.
- Normaliza IDs de tool_calls no streaming, rechaza IDs duplicados antes de efectos y mantiene idéntico ID en assistant/result.
- El diario ahora clasifica como potencialmente mutantes las herramientas MCP externas, acciones de archivos y operaciones LOOP no explícitamente de lectura; antes de ejecutarlas registra INICIADA.
- Si el Router devuelve `error` JSON-RPC o `result.isError`, NO sella CONFIRMADA una operación potencialmente mutante: requiere reconciliación humana para evitar ejecución duplicada.
- Pruebas añadidas `chat/backend/deepseek_harness/test_xray4_harness.py`. E2E, HF y pruebas de agentes reales pendientes, no declarar PASS operativo.

## Segmento 5 — Bridge SWE CODE (solo backend)
- `SWE CODE/web-bridge/src/server.js`: señales de cancelación unificadas para Groq/NVIDIA/local HF; la asesoría Groq transmite streaming real y no mezcla respuestas de otros modelos si entregó un parcial.
- `SWE CODE/web-bridge/src/respaldo.js`: Retry-After y backoff cancelables; la cancelación no rota claves ni arranca otra llamada.
- `SWE CODE/web-bridge/src/retomar_local.js`: no inicia/reanuda checkpoint de una petición cancelada, incluida la espera de cerrojo y otra vuelta.
- Pruebas añadidas: `SWE CODE/web-bridge/test/xray5_backend.test.mjs`; no se han ejecutado (Node y servicios reales pendientes).
- ALCANCE: solo GitHub `chat-router/`; FRONTEND NO TOCADO, Hugging Face NO TOCADO (mirror existente).

## Segmento 6 — OpenClaw BACKEND exclusivamente; frontend reservado para Claude Code
- X-Ray detectó bypass de autorización del operador en `sala:contexto`: estaba declarada como lectura, pero `mvp/control.py` escribe el contexto de ROOM. Eliminada de `lectura` en `SWE CODE/web-bridge/src/openclaw.js`; el operador individual es obligatorio para cambiarlo.
- `SWE CODE/web-bridge/src/swe_rutas.js`: respuestas HTTP 200 con `status=degraded/error`, `ok=false` o error en resultado ahora devuelven `ROUTER_PLUGIN_ERROR`, sin suponer éxito ni reflejar secretos.
- Pruebas de regresión incorporadas en `SWE CODE/web-bridge/test/swe_rutas.test.mjs`: operador para sala.contexto, lectura permitida y error de plugin detrás de HTTP 200. No ejecutadas en servidor vivo.
- No se tocó frontend, Hugging Face ni OpenClaw independiente. Cierre de UI YAIWES/OpenClaw queda explícitamente reservado hasta terminar Claude Code.

## Segmento 7 — X-Ray de tool_calls inválidas (backend; frontend no tocar)
- Claude Code incorporó en paralelo el control de idempotencia de `swe_iniciar` (contrato completo, índice huérfano); se auditó y no se duplicó.
- `SWE CODE/web-bridge/src/retomar_local.js`: los `tools_invalidas` del proveedor bloquean ejecución, dejan error tipado en el checkpoint y no generan `WAIT_TOOLS` ejecutable.
- `SWE CODE/web-bridge/src/server.js`: tool_calls inválidas no se entregan a OpenClaw ni al Harness, tampoco tras fallback. Error tipado `TOOL_CALL_INVALIDA`; sin ejecutar herramientas.
- Prueba añadida en `SWE CODE/web-bridge/test/retomar_local.test.mjs` con argumentos JSON incompletos y verificación de cero efectos. No ejecutada; pendiente runner Node real.
- Nada de frontend, Hugging Face, OpenClaw independiente ni nuevas raíces. Guardado GitHub main; mirror externo NO certificado.

### X-Ray 7B — checkpoint legado
- Se detectó que un `WAIT_TOOLS` previamente guardado podía pasar directamente a `resolverLote` sin volver a validar los argumentos JSON. El preflight del lote ahora bloquea `TOOL_CALL_INVALIDA` ANTES de cualquier efecto, anota `RECONCILIAR` y evita ejecución parcial.
- Prueba `X-Ray 7B` añadida en `test/retomar_local.test.mjs` con dos tools (primera válida, segunda corrupta): exige **cero** efectos. Prueba sin ejecutar en entorno Node.

## Dos objetivos — X-Ray corrección del cableado YAIWES + OpenClaw (sin agentes)
- **Incidente real:** `enviar-mensaje.js` tenía `if (fichaGroq === "")` sin comprobar el selector activo; al elegir Groq se bloqueaba y otros flujos podían quedar mal dirigidos. Se restringió el guard al selector Groq.
- Groq y NVIDIA seleccionados ya pasan al bridge `/web/v1/chat/completions` por el **ID exacto elegido**, igual que los cuatro modelos locales HF. Nada de envío por otra ficha Qwen accidental.
- Selector NVIDIA ya conserva el modelo elegido en `RIU_NVIDIA.modelo` y en el chat; dejó de depender de un `RIU_FICHA.elegir` que podía no existir.
- `fichas-externas.js` consulta prioritariamente el banco real y el `GET /models` del bridge, no solo el banco del Router MVP. Disponibilidad real o SIN VERIFICAR; sin clave, NO CONFIGURADO. Sin exponer claves en navegador.
- Los selectores priorizan la verificación del bridge sobre el estado de agentes del Harness en modo chat sin agentes; optgroup/option simplificados para móvil.
- Pruebas nuevas en `chat/frontend/test/enviar-modelo.test.mjs` y `test/swe-central.test.mjs`; ejecución real y mirror NO certificados. Solo GitHub `chat-router/`; sin modificaciones Hugging Face ni agentes.

### X-Ray II — disponibilidad local y consulta paralela
- `SWE CODE/web-bridge/src/respaldo.js`: consultas Groq + NVIDIA ahora se realizan en paralelo en `GET /v1/modelos/disponibilidad`; antes podían tardar 20 s y exceder el timeout del frontend (15 s), induciendo falso «sin conexión».
- `SWE CODE/web-bridge/src/server.js`: respuesta del endpoint incluye `locales`, con **SIN VERIFICAR** si hay al menos un URL S1..S3 y **NO CONFIGURADO** si ninguno; no anuncia modelos locales como DISPONIBLES sin inferencia real.
- `chat/frontend/fichas-externas.js`, `swe-selectores.js`, `swe-directo.js`: misma disponibilidad del bridge para modelos locales y APIs, sin depender de la detección de agentes por otro equipo. Frontend Groq/NVIDIA locales selectores reparados.
- Pendiente: ejecución real del bridge y credenciales; un estado de catálogo no demuestra respuesta real. Sin cambios en Hugging Face ni infraestructura.

### X-Ray III — pruebas de integración sin agentes
- `chat/frontend/test/fichas-externas.test.mjs`: se agregaron pruebas de catálogos y conteos del bridge, modelos SIN VERIFICAR frente a NO CONFIGURADO y visibilidad local.
- `SWE CODE/web-bridge/test/respaldo_stream.test.mjs`: prueba que Groq + NVIDIA se consultan simultáneamente, sin demorar ambas sondas secuencialmente.
- NVIDIA conserva `riu_nvidia_modelo` en almacenamiento del navegador (solo ID, nunca credenciales), restaurando la selección tras recarga.
- No se ejecutaron aún las pruebas completas ni se certificó respuesta real de proveedor; todo el código va por GitHub y el mirror existente, sin cambios en HF.

### X-Ray IV — precisión de estados
- El selector ahora diferencia **verificado disponible** frente a **sin verificar**; no declara «publicado» un modelo cuyo catálogo no se pudo consultar. La prueba de paralelo falla si NVIDIA debe esperar el timeout de Groq.
- Verificación local aislada con funciones reales de `enviar-mensaje.js` y `fichas-externas.js` evaluadas sobre dobles: 3/3 rutas de chat (Groq, NVIDIA, HF local) enviaron ID exacto al puente, 2/2 estados de banco correctos. **No es un E2E con proveedores**.

### X-Ray V — contrato cruzado entre dos chats
- Prueba `SWE CODE/web-bridge/test/xray_modelos_ambos_chats.test.mjs`: OpenClaw y YAIWES comparten los 5 identificadores Groq/NVIDIA y los 4 locales HF; la ruta YAIWES llega al mismo bridge OpenAI-compatible con el modelo exacto.
- La verificación dinámica aislada anterior mostró 3/3 rutas UI correctas (Groq, NVIDIA, HF local) y 2/2 casos de banco simulado. **No** equivale a respuestas API en producción ni prueba que el Gateway haya instalado el provider.

### X-Ray VI — Selector de modelos OpenClaw nativo (sin agentes)
- El backend del plugin OpenClaw `SWE CODE free/openclaw-ui/src/bridge.ts` ahora fusiona (en paralelo) las capacidades del Harness (solo agentes/workflows) con `/v1/modelos/disponibilidad` y `/v1/claves` del mismo bridge que hace inferencia. Corrige falsos NO CONFIGURADO por tener las claves en el banco del bridge y no en el Harness.
- El catálogo del bridge declara los 5 modelos de API y 4 locales HF: disponible real, sin clave, no publicado, o sin verificar; los locales con URL NO se declaran disponibles sin responder. Sin exponer claves al navegador.
- Prueba de fusion con Harness caído, bridge antiguo, banco sin claves y modelos de 2 proveedores en `SWE CODE free/openclaw-ui/test/plugin-sdk.test.mjs`. Sin tocar la lógica de agentes, workflow, ni su instalación.
- Ejecución plugin del Gateway y respuestas API reales: PENDIENTE DE E2E con configuración del usuario.

## Cierre de compatibilidad Space (solo lectura HF)
- El Dockerfile y boot.sh **existentes en HF** ya instalan Node.js y arrancan el bridge :7870 en background, con proxy.py :7860. Son distintos de los archivos `respaldo_space/` del clon GitHub; no asumir que ese Dockerfile de GitHub se despliega automaticamente.
- `chat/backend/mvp/run.py` reconoce `/proxy.py` del Space existente y no inicia un segundo bridge, para evitar `EADDRINUSE` y fallos intermitentes. En un contenedor independiente sin `/proxy.py` mantiene el arranque propio.
- No se escribió nada en Hugging Face. Prueba `test_xray_boot_bridge.py` añadida; prueba real/estado HF pendientes.

## Cableado definitivo del modelo — backend primero, frontend después (2026-11-01)
**Objetivo:** Chat YAIWES y UI OpenClaw → plugin HTTP Harness DeepSeek → Router MVP (APIs externas) / Router SWE CODE (locales y web) → NVIDIA/Groq/HF. Sin construir otro router, sin modificar agentes y sin acceso de escritura a Hugging Face.
- **Backend**: `chat/backend/deepseek_harness/server.py` monta `/modelos/v1/{models,disponibilidad,chat/completions}` bajo `/plugins/deepseek_harness`; valida clave de acceso del chat, preserva modelo elegido; API externa por `router-mvp/mvp` (symlink existente a `chat/backend/mvp`) → `POST /chat`; HF/web por `SWE CODE/web-bridge` → `POST /v1/chat/completions`. No usa herramientas en el canal de conversación normal; los agentes siguen en `/invoke` y `/chat/swe`.
- **Banco compartido**: corregido `chat/backend/mvp/externos.py`; el Router MVP debe leer las claves del bridge en `/tmp/state/banco-swe.bin` por defecto (el `BRIDGE_STATE_DIR=/tmp/state` solo estaba definido en el proceso Node). No crear ni copiar bancos.
- **OpenClaw**: `SWE CODE/web-bridge/src/openclaw.js` actualiza solo el provider `swecode` del gateway a `http://127.0.0.1:7861/plugins/deepseek_harness/modelos/v1`, con `RIU_API_KEY` interna, respetando pairing, otros providers y modelo por defecto. `SWE CODE free/provider-openclaw.json` refleja la misma ruta.
- **Frontend último**: `chat/frontend/swe-directo.js` envia todos los modelos por el plugin de Harness; `selector-modelos.js` consulta disponibilidad por Harness; `api.js` respeta timeout más largo para modelos. No tocar otros selectores ni agentes.
- **PASS estático**: 12 archivos modificados, todos bajo `chat-router/` (incluyendo enlace simbólico existente de `router-mvp/mvp`), sin archivos nuevos en raíz del repositorio; análisis estático JS y comparación de rutas realizados.
- **GAP de runtime no oculto**: GLM 5.3 = HTTP 410 reportado en capturas, aunque NVIDIA publica `z-ai/glm-5.3` como identificador correcto; necesita verificación de permisos en GET /models / prueba con cuenta real. Locales S1/S2/S3 = HTTP 503 (Space/servidores remotos fuera de servicio). OpenClaw aún necesita prueba real tras autopull. No se tocó Hugging Face; no declarar DONE funcional sin probar servicios.
- **Pruebas añadidas**: `chat/backend/deepseek_harness/test_modelos_harness.py`, `chat/backend/mvp/test_externos_multi_api.py`, `SWE CODE/web-bridge/test/openclaw_modelos_config.test.mjs` y `chat/frontend/test/selector-api-sdk.test.mjs`. Los runners no se ejecutaron: el repositorio no es clonable en la terminal sin conectividad; NO inventar PASS.
