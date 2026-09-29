# HANDOFF PROVISIONAL — Router inteligente universal
Actualizado: 2026-09-29 (05:00 Bogotá). Provisional: vale hasta que el chat se termine y se mueva a otro repo.
Alcance: SOLO el Router, sus conexiones, sus claves (solo nombres), Hugging Face y Vercel. Nada del chat, de las tareas en curso ni del equipo de agentes: eso vive aparte (`Estado y handoff global/`).
Regla: solo hechos verificados. Lo no verificado dice SIN VERIFICAR.
Guía para conectar otros repos/MCP: `CONECTAR-ROUTER.md` (misma carpeta). Radiografía del Router: `Readme arquitectura router inteligente universal/HUELLA-DIGITAL-ROUTER.md`. Palabras textuales del Director: `Readme arquitectura router inteligente universal/INPUT-BLOCK-VERBATIM-2026-09-29-director.md` (02:06 y 02:35) y `…-parte-2.md` (03:26, 03:27 y 04:41 con los 5 puntos de Fables). Arquitectura detallada de fichas: `Readme arquitectura router inteligente universal/ARQUITECTURA-ROUTER-FICHAS-FABLES.md`.

## 0. Tareas del Router (todas las que tienen que ver con el Router viven aquí)
| # | Tarea | Estado |
|---|---|---|
| T-00 | Auditar el Router y dejar uno solo | PASS |
| T-01 | Limpieza de Hugging Face (la parte de Vercel queda para después, por orden del Director) | PASS (HF) · Vercel pendiente |
| T-03 | Quitar Cerebras del Router y poner Groq | PASS · Router relanzado con el código nuevo y Groq Qwen 3.8 en la cadena g2 (smoke run 36528065394) |
| T-10 | Conectar cualquier repo/MCP al Router único sin crear otro Router | DOCUMENTADO (`CONECTAR-ROUTER.md`) · sin probar desde otro repo |
| T-11 | IA local en máquina de 32 GB (DFlash 2, MTP, etc.) | PLANIFICADO · DESPUÉS de terminar Router y pendientes (orden del Director). Hoy NO hay ninguna IA local corriendo (solo existe la puerta `local`) |
| T-12 | Cadenas del chat con NVIDIA: Kimi K3 → GLM-5 → DeepSeek V4 Flash | PENDIENTE (hoy el chat solo tiene Nemotron; los agentes ya priorizan así). Orden 04:41: Nemotron pasa a ÚLTIMA opción → ver T-20 |
| T-13 | Prioridad de claves: chat + Hermes + OpenClaw en NVIDIA 1–3; si ocupadas → 4 o Groq | PENDIENTE (`run_policy` hoy usa siempre la llave 1) |
| T-14 | Autoescalado 16→32 GB (sube al 80 %, duerme a los 5 min) | NO EXISTE · PENDIENTE |
| T-15 | Plugin abierto en el Router (enchufe) para no tocar más el Router | DISEÑO HECHO: "Plugin Host" = contrato/registro/failover/salud de Fables + regla del harness DeepSeek (quitable, sin dependencia dura, degradado no bloquea). Espera aprobación (arquitectura §8) |
| T-16 | Selector de grupos/combinaciones + subrouters + thinking, sin romper el principal | DISEÑO en arquitectura §9 (thinking = modos de ejecución de una ficha). ZIP de otra IA sigue SIN VERIFICAR |
| T-17 | Verificación cruzada contra lo que hizo Opus | EN CURSO (resultado parcial abajo) |
| T-18 | Prueba del Router y conectar al equipo del plan 4 objetivos (= T-04 global) | PENDIENTE |
| T-19 | Revisar aceleradores HF y qué se puede usar en máquinas de 16 y 32 GB | PENDIENTE (inventario de otra IA recibido, SIN VERIFICAR) |
| T-20 | Lista de modelos disponibles + Nemotron último + salto de llaves NVIDIA→Groq (orden 04:41) | DISEÑO en arquitectura §6 · espera aprobación de la cadena |
| T-21 | Sistema paralelo (documento de Mavis / MiniMax) para hasta 1000 procesos mientras haya API o IA local | DISEÑO en arquitectura §10 · pregunta abierta: qué es exactamente "1000" |
| T-22 | Fichas de Fables: registro + validación + compilador ficha→flujo + mini-chat operador + detección automática de conexiones | DISEÑO en arquitectura §4, §5, §7 · espera aprobación |
| T-23 | Conectar la Run UI al Router (ejecución real, lista real de modelos, quitar modelos de Anthropic) | PENDIENTE · faltan `css/` y `js/` de `fgh.html` e `index.html` |
| T-24 | Cablear dataset Yaiwes + plano de control Yaiwes como anclajes de ficha | PENDIENTE (plugin ya existe, cableado reservado al último nodo) |

## Órdenes 2026-09-29 (Director, 02:06 y 02:35) — plan de 4 pasos
Regla: se planea todo y se sube UN SOLO Job a Hugging Face al final. Nada se instala antes.
- Paso 1 (anotar textual): HECHO — `INPUT-BLOCK-VERBATIM-2026-09-29-director.md` (+ parte 2 con los mensajes de las 03:26, 03:27 y 04:41). Fidelidad: los textos del Director están copiados tal como llegaron; lo pegado de otras IAs va marcado SIN VERIFICAR.
- Paso 2 (motores de descarga): PENDIENTE — primero leer los commits de Opus sobre el motor de descarga y extracción; usar ese motor, no otro.
- Paso 3 (archivos de Fables 5): LEÍDOS. El Director los subió en el commit `2f5c111e` a `Documentos del proyecto/Documentos proyectos router inteligente universal/` (~37 archivos: Run UI, paneles v1–v5, resumen v6, enchufe v2, bus de plugins, Mavis, etc.). Resultado y qué falta: `ARQUITECTURA-ROUTER-FICHAS-FABLES.md` (§2 y §13). Faltan los `css/` y `js/` de `fgh.html` e `index.html`.
- Paso 4 (integrar y probar): PENDIENTE hasta que el Director conteste las preguntas de la arquitectura (§15).

## Órdenes 2026-09-29 (Director, 03:26 / 03:27 y 04:41)
- 03:26–03:27: poner Qwen 3.8 en Groq (HECHO, T-03); NVIDIA Kimi K3 / GLM 5 / DeepSeek V4 (probados en vivo, ver `EVIDENCIA-2026-09-29-NVIDIA-Y-COMPONENTES.md`; falta ponerlos en la cadena del chat, T-12/T-20); qué hay de proveedor local (respondido: solo la puerta, ninguna IA corriendo); reproche por no revisar archivos subidos ni componentes (revisado después).
- 04:41: (1) Nemotron como última opción si los demás no aparecen disponibles → T-20. (2) El Router debe pedir la lista de modelos disponibles y no bloquearse si uno no responde, aunque haya latencia; el Router ya sabe la prioridad → T-20. (3) Revisar el plugin de Fables y el harness de DeepSeek y, si hace falta, generar una versión mejorada con los dos → T-15. (4) Integrar el dataset con el sistema "thinking" que dio el Director → T-16 y T-24. (5) Añadir el sistema paralelo de MiniMax para 1000 procesos paralelos mientras exista API o IA local → T-21. (6) Los 5 puntos de Fables (textuales en la parte 2 del input block) → arquitectura de fichas, T-22 y T-23. (7) "¿Hay IA local disponible en Hugging Face?" → explicado en arquitectura §11 (no hay ninguna corriendo). (8) Revisar los archivos y hacer las preguntas ANTES de continuar → hecho, preguntas enviadas; no se implementó nada.

### T-11 IA local (después)
- Ajustes pedidos: DFlash 2, MTP, Flash Attention ON, caché KV K/V en Q8, Batch 256 (?), uBatch 128 (?). Los dos números con "?" NO están confirmados por el Director.
- Dónde: un Job aparte de 32 GB. El Router ya tiene un proveedor `local` (variables `RIU_LOCAL_BASE_URL` y `RIU_LOCAL_API_KEY`), así que se conecta sin cambiar el código del Router; solo hay que dar dirección y modelo a la entrada `local` de la cadena.
- Modelo: buscar uno de 1B–10B en Q4/GGUF (Qwen 3.8 si existe así); "faltan varios modelos" y se decide después. Según el inventario adjunto (SIN VERIFICAR por mí): DFlash 2 necesita el modelo base y su borrador compatibles; MTP solo sirve si el modelo trae cabezas MTP.
- Nota de hardware: el Router de 16 GB no ejecuta modelos; no se instala nada ahí.

### T-12 / T-13 Cadenas y claves NVIDIA
- Verificado: no se tocaron las claves NVIDIA. En `agents-yaiwes/common/routes.py` yo solo cambié `EXCLUIDOS` (Cerebras); las prioridades Kimi K3 → GLM-5 → DeepSeek V4 ya estaban (hasta 4 claves NVIDIA y 7 Groq; si una no responde o está ocupada se prueba la siguiente; sondeo cacheado 15 min).
- Ese orden vale para los agentes. La cadena del chat (`resilience.py`) hoy es solo Nemotron (y Groq en g2). Falta ponerle Kimi K3 y GLM 5.3 y la regla "NVIDIA 1–3, luego la 4 o Groq". Se hace con un ajuste de configuración, no reescribiendo el Router.
- Prueba en vivo 2026-09-29 (NVIDIA, 4 llaves): `moonshotai/kimi-k3` 200 en 0,8 s; `z-ai/glm-5.3` 200 en 1,3 s (no existe "glm-5" a secas); `z-ai/glm-5.3-flash` y `deepseek-ai/deepseek-v4.1-flash` sin respuesta en 25 s en las 4 llaves (arranque en frío sin confirmar).

### T-14 Autoescalado (Director)
- Regla dada: el Router de 16 GB corre 24/7 (con el conector MCP) y es el que despierta a los demás; el siguiente procesador se enciende al llegar al 80 %; el de 32 GB se duerme a los 5 min sin llamadas. Hermes, chat y OpenClaw usan procesadores de 16 GB y saltan al siguiente según necesidad; los de 32 GB son para IA local, generar código y correr workflows por llamada.
- Verificado en el código: NO está construido. `hf_scheduler.py` solo elige entre HF1/HF2/HF3 con tope de 95 % de RAM y nadie lo llama; `hf_jobs_compute.py` puede lanzar un Job pero solo si se lo piden. Opus lo dejó como pendiente B2.6 (con 80 %/85 % y 15 min; el Director ahora dice 80 % y 5 min: manda el Director).

### T-15 Plugin abierto
Candidatos leídos el 2026-09-29: (a) `ruflo-deepseek-harness` (Node; aporta 3 reglas: quitable, sin dependencia dura, si falla devuelve estado degradado; llama directo a la API de DeepSeek, cosa que NO se copia porque los modelos solo van por el Router), (b) bus de plugins de Fables + Kimi (`universal_plugin_bus_v2_integrated.py` y `ficha_contract_v2.py`; contrato, registro, failover, salud, presupuesto, evidencia; límites: `trigger_plugin` no ejecuta nada, exige aprobación de "tribunal", el intercambio en caliente usa `exec` con una revisión de seguridad por texto), (c) el validador y el esquema v2 que ya están en `enchufe/` y `domain/schemas/`. Decisión propuesta: "Plugin Host" que junta lo mejor de los dos sobre `RedUniversal` (que ya invoca conectores) — ver arquitectura §8.

### T-16 Selector / subrouters / thinking
El ZIP de otra IA (`yaiwes_subrouters_modulares.zip`) trae 4 subrouters (instant, thinking, council, code), perfiles en un JSON y `GET /chat/subrouters/catalog`, apagado por defecto. SIN VERIFICAR (sus pruebas eran simuladas), no aplicado. El Router de hoy no envía parámetros de razonamiento a los proveedores (`providers.py` manda solo model, messages, max_tokens, temperature). Propuesta: los modos de thinking son plantillas de ficha (arquitectura §9).

### T-17 Verificación cruzada con Opus (resultado parcial)
- Los documentos de Opus (`chat router/03-ESTADO/OPUS-PENDIENTE.md` y `RECUPERACION-OMNIROUTE.yaml`, 2026-09-27) ya no están en main: la limpieza general del 2026-09-29 (orden del Director) los quitó. Existen en la rama `backup-antes-limpieza-20260929`.
- No creé un Router nuevo. Sobre el Router de Opus solo hice: quitar Cerebras, poner Groq Qwen 3.8, corregir la ruta del banco tras la reorganización (`vault_bridge.py`) y fijar una variable en el lanzador. Pruebas: 168 pasan, 8 fallan (ya fallaban), 0 errores.
- Construido por Opus y todavía presente (según su nota, no re-probado por mí hoy): chat con Kimi K3, Groq con las claves 2–7.
- Pendiente de la lista de Opus que NO está construido: autoescalado, OmniRoute como proveedor (además el Director eliminó OmniRoute: esos puntos quedan CANCELADOS), aviso de modelos en el chat, montar módulos de los espejos, puente de almacenamiento HF. Nota: `app.py` todavía intenta montar `omniroute_proxy`, que no existe; el `try` lo tolera.
- Falta: comparar archivo por archivo el código actual contra la rama de respaldo (solo la carpeta del Router) para confirmar que no se perdió nada con la reorganización.

## T-00 a T-10 — detalle
### T-00 — Auditar el Router y dejar uno solo (PASS)
Un solo Router vivo: un Job de Hugging Face. Rutas probadas con el smoke (secciones 2 y 3). Incidente del vigilante de 32 GB en la sección 8. Evidencia: BITACORA B-0001, B-0002, B-0003, B-0007.

### T-01 — Limpieza de Hugging Face (PASS; Vercel pendiente)
Borrados `omniroute-1..5` (run 36518718390). Queda el Space del conector MCP (protegido), el Job del Router y el dataset de memoria. Sentinelas y mini-router pausados/borrados. Pendiente solo Vercel: las variables del proyecto no se borraron (son secretas e irrecuperables); "después borramos lo de Vercel" es decisión del Director. Evidencia: B-0003…B-0008, B-0011.

### T-03 — Quitar Cerebras y poner Groq (PASS)
Hecho, con pruebas (commits 7fa21739 y 3744d9b4):
- Cerebras quitado de: `integration/chat_mvp/providers.py`, `resilience.py` (cadena g2), `vault_bridge.py`; `agents-yaiwes/common/{routes,probe_keys,boot}.py`; `agent-microkernel/kernel/{dag_loader,dispatcher}.py`; `gateway/hf_chat_mvp/app.py`; `Banco de claves/{accounts,groups}.yaml`; 68 archivos `chain.yaml`/`workflow.dag.yaml` de agentes; los workflows `deploy-chat-space`, `riu-chat-mvp-verify`, `riu-dag-run`, `riu-validate-provider-keys`. Tests ajustados (Cerebras → Groq).
- Se dejó a propósito: el patrón `csk-` en `riu-secret-scan.yml` (detecta filtraciones), las notas textuales del Director y el historial/evidencias.
- Modelo de Groq: Qwen 3.8 (decisión del Director 2026-09-29). Id exacto verificado en vivo: `qwen/qwen3.8-27b` (respondió "OK"). Se fija con la variable `RIU_G2_GROQ_MODEL` en las dos llamadas `run_job` de `riu-router-job-central.yml` (commit 62e1bf74).
- Router relanzado: Job `6abb503a6b030d633f6a2dca`, dirección en el archivo de dirección (`LIVE_URL`, `PAUSED=false`). El lanzador escribió la dirección nueva y solo después canceló el Job viejo `6abb1ff352d0dbd7f1da8a58`.
- Verificado con el smoke (run 36528065394): `/health` 200; `/chat/models` 200; `/chat/router/status` 200 con cadena g2 = NVIDIA `nvidia/nemotron-3-super-120b-a12b` → Groq `qwen/qwen3.8-27b`; sin ninguna mención de Cerebras.
Pendiente / decisión del Director:
1. La cadena por defecto (no g2) sigue siendo solo NVIDIA: Groq no está en ella. ¿Se quiere ahí? (ver T-20)
2. Vercel: `RIU_ROUTER_URL` quedó vieja con el relanzamiento (dirección fija).
3. El smoke prueba `/chat/send` y `/chat/jev` con provider=hf, que falla siempre (`PROVIDER_KEY_MISSING:hf` / 401): no es un fallo del cambio. Falta una prueba de chat real por NVIDIA/Groq (SIN VERIFICAR que responda).

### T-10 — Conectar cualquier repo/MCP al Router único (documentado)
Hecho: `CONECTAR-ROUTER.md` (cómo hallar la dirección, cabeceras, secretos que necesita cada repo, cliente existente `RouterCliente`, qué hacer si el Router se mueve).
Falta: probarlo de verdad desde otro repo (una corrida corta que lea el archivo de dirección y llame `/health`). Y decidir si hace falta un envoltorio MCP del Router (SIN VERIFICAR que exista; si se hace, se cablea lo descargado, no se escribe desde cero).

### Arreglo hecho tras la reorganización
El puente del banco (`integration/chat_mvp/vault_bridge.py`) buscaba la carpeta vieja `Chat Mvp`. Ahora busca `Banco de claves` (commit 3744d9b4). Pruebas antes: 162 pasan, 8 fallan, 6 errores; después: 168 pasan, 8 fallan, 0 errores (run 36526076292).
Los 8 fallos que quedan existían antes de este cambio (no verificado si vienen de la reorganización): `test_conector_gitlab_v6` (acción desconocida), `test_conector_interno_webhook_v6` (2), `test_conector_mcp_app_v6` (2), `test_conector_vps_v6`, `test_fast_close_global_e2e` (502), `test_huggingface_openai_chat_registry` (conjunto de modelos).
Rutas viejas que quedan sin importancia: un comentario en `resilience.py` que menciona `Chat Mvp/router_policy/peak.py`, y `riu-agent11-canonical-download.yml` (mira `hermes-agent/` en la raíz).

## 1. Qué es el Router
- Es UNO solo. Todo lo que se construya se conecta a él; no se crean routers nuevos.
- Corre como un Job de Hugging Face (máquina cpu-basic 16 GB), siempre encendido.
- Aplicación: `router inteligente universal/integration/chat_mvp/app.py` (FastAPI).
- Job vivo al 2026-09-29: `6abb503a6b030d633f6a2dca` (`https://6abb503a6b030d633f6a2dca--8000.hf.jobs`; la dirección cambia en cada relanzamiento: leerla siempre del archivo de dirección).

## 2. Cómo se lanza y dónde está su dirección
- Lanzador: `.github/workflows/riu-router-job-central.yml`. Ejecuta `router inteligente universal/agents-yaiwes/common/router_job_persistent.py`.
- Ese script clona el repo, descifra el banco de claves al arrancar, levanta la aplicación con uvicorn y vuelve a bajar el repo cada 60 segundos.
- Relanzar es seguro: el lanzador arranca el Job nuevo, espera `/health`, escribe la dirección nueva y solo entonces cancela el viejo. Aun así, se hace solo con orden del Director.
- La dirección viva está en `router inteligente universal/agents-yaiwes/ROUTER_JOB_PAUSE.flag` (línea `LIVE_URL`; línea `PAUSED=false`).
- Código que ya se importó no cambia con la bajada de 60 s: para que un cambio de código tome efecto hay que relanzar el Job.

## 3. Cómo se le habla
- Cabeceras: `Authorization: Bearer <HF_TOKEN_1>` y `X-API-Key: <RIU_ROUTER_API_KEY>` (solo nombres; los valores están en tu banco, nunca en el repo).
- Rutas verificadas (smoke runs 36513612455, 36521693774 y 36528065394):
  - `/health` → 200
  - `/chat/models` → 200 (lista Kimi K3 `moonshotai/Kimi-K3`, MiniMax, DeepSeek V4 Flash, otros)
  - `/chat/router/status` → 200
  - `/v1/models` → 200 pero solo 2 modelos chicos (Qwen3-8B, gpt2): no sirve para agentes
  - `/chat/send` con provider=hf → 400 `PROVIDER_KEY_MISSING:hf`; `/chat/jev` con provider=hf → 503 (401 aguas arriba). No usar provider=hf.
- También montadas (sin probar): `/chat/route`, `/chat/jobs/run`, `/memoria/*`, `/gh/*`, `/control/*`.
- Prueba de solo lectura: `.github/workflows/riu-router-smoke.yml` (botón manual). El resultado se lee en las anotaciones de la corrida.

## 4. Ruta de modelos (orden del Director)
NVIDIA (hasta 4 claves; Kimi K3 o el más nuevo) → Groq (Qwen 3.8) → DeepSeek V4 Flash al final. Sin APIs de Anthropic. Cerebras y OmniRoute eliminados. **Orden 04:41: Nemotron como ÚLTIMA opción, y el Router pide la lista de modelos disponibles** (T-20; todavía no construido).
Estado del Router VIVO (verificado 2026-09-29): cadena g2 = NVIDIA `nvidia/nemotron-3-super-120b-a12b` → Groq `qwen/qwen3.8-27b` (DeepSeek V4 Flash al final, se salta en hora pico). La cadena por defecto sigue solo NVIDIA.

## 5. Claves (solo nombres, nunca valores)
- Banco de claves: código en `router inteligente universal/Banco de claves/` (antes "Chat Mvp"). El Job lo descifra al arrancar; las claves reales viven en tu banco de secretos.
- Nombres vistos: `HF_TOKEN_1`, `HF_WRITE_TOKEN`, `HF_TOKEN_MAXBRY123`, `RIU_ROUTER_API_KEY`, `RIU_AGENT_API_KEYS`, `NVIDIA_API_KEY_1..4`, `GROQ_API_KEY_1..7` (la 1 dio 401; el lanzador pasa la 2..7), y para GitHub `GH_CLASSIC_FULL_1`, `GH_CLASSIC_FULL_2`, `RIU_GITHUB_PAT_FULL_ACCESO`, `GH_JOB_PUSH_TOKEN`.
- Cerebras: ya no se usa `CEREBRAS_API_KEY_1`; el secreto puede seguir existiendo en GitHub, ningún código lo lee (decisión del Director si se borra).
- El repo es PÚBLICO: jamás poner valores de claves aquí.
- Pendiente tuyo: rotar las 7 llaves de Groq que se pegaron en un chat.

## 6. Hugging Face (cuenta `COMAND-CENTER-1`)
- Jobs vivos: 1 (el Router).
- Spaces: 1 — `claude-github-mcp-backup`, el conector MCP de Claude. PROTEGIDO: no tocar, no reiniciar, no borrar. `keep-mcp-space-awake` sigue desactivado. Según Opus (SIN VERIFICAR por mí): sin OAuth, dirección secreta `/<MCP_SECRET_PATH>/mcp`, un webhook dispara el lanzador único.
- Datasets: `yaiwes-hf-memoria` (privado, memoria).
- Borrados el 2026-09-29: `omniroute-1..5`.
- Documentos de Hugging Face: carpeta `Huggingface/` (incluye `README-HUGGINGFACE.md`).

## 7. Vercel (solo pantalla)
- Cuenta `maxbry123@gmail.com` · usuario `maxbry123-8833` · plan Hobby · team `maxbry123-8833s-projects` (`team_hG9df7zIgfZFY0oxFFsIRr1u`).
- Proyecto `riu-jev-bridge` (`prj_m8Lk3iaB3eN6dwlIq1ND2un8FWTD`). Sin despliegue vivo; despliegue automático apagado (cada push deja un intento CANCELED, es normal).
- Variables (solo nombres): `RIU_CHAT_PASSWORD`, `RIU_ROUTER_API_KEY`, `RIU_ROUTER_URL`, `HF_JOB_FLAVOR`, `HF_TOKEN_1`. NO se borraron: son secretas e irrecuperables. Decisión de borrarlas: del Director, más adelante.
- `RIU_ROUTER_URL` es una dirección fija: tras el relanzamiento del 2026-09-29 quedó vieja (ver `CONECTAR-ROUTER.md`, sección 1).
- Regla: no instalar nada hasta que todo esté listo; un único deploy final, solo con su orden.
- Documento: `Vercel/HANDOFF-VERCEL.md`.

## 8. Incidente que no debe repetirse
El 2026-09-29 un vigilante (`riu-hf-jobs-audit-32gb.yml`) cancelaba cualquier Job que no fuera cpu-upgrade y mató al Router a las 02:15Z (run 36511703509). Ya está borrado. Regla: ningún workflow puede cancelar ni relanzar el Job del Router salvo el lanzador único y por orden del Director.

## 9. Para llevarse el Router a otro repo
- Copiar la carpeta `router inteligente universal/` completa (incluye el banco de claves, `CONECTAR-ROUTER.md` y este archivo).
- Llevar también el lanzador `.github/workflows/riu-router-job-central.yml` y `riu-router-smoke.yml`.
- La dirección del repo está escrita en: `REPO_URL` de `agents-yaiwes/common/router_job_persistent.py` (línea 20), en el `git clone` y en la URL de la API del archivo de dirección dentro de `riu-router-job-central.yml` (líneas 62 y 102), y en `FLAG_URL` de `chat router/05-AGENTES/colmena/router_cliente.py`. Verificado leyendo esos archivos.
- Nombres de secretos de GitHub Actions: hay que recrearlos en el repo nuevo.
