# HANDOFF PROVISIONAL — Router inteligente universal
Actualizado: 2026-09-29 (~11:20 Bogotá; checkpoint progresivo ordenado por el Director a las 11:07; la versión anterior de este archivo era de las 05:00). Provisional: vale hasta que el chat se termine y se mueva a otro repo.
Alcance: SOLO el Router, sus conexiones, sus claves (solo nombres), Hugging Face y Vercel. Nada del chat, de las tareas en curso ni del equipo de agentes: eso vive aparte (`Estado y handoff global/`). EXCEPCIÓN desde las 10:55 (orden del Director): "El chat es solo un plugins más conectado al router". La cadena de modelos que usa el chat es una función del Router (código en `router inteligente universal/integration/chat_mvp/`), por eso su estado, su evidencia y su lista roja SÍ se anotan aquí (secciones 10 a 19).
Regla: solo hechos verificados. Lo no verificado dice SIN VERIFICAR.
Guía para conectar otros repos/MCP: `CONECTAR-ROUTER.md` (misma carpeta). Radiografía del Router: `Readme arquitectura router inteligente universal/HUELLA-DIGITAL-ROUTER.md`. Palabras textuales del Director: `Readme arquitectura router inteligente universal/INPUT-BLOCK-VERBATIM-2026-09-29-director.md` (02:06 y 02:35) y `…-parte-2.md` (03:26, 03:27 y 04:41 con los 5 puntos de Fables). Arquitectura detallada de fichas: `Readme arquitectura router inteligente universal/ARQUITECTURA-ROUTER-FICHAS-FABLES.md`. Respuestas del Director de las 05:15 a las 7 preguntas: `…-director-parte-3.md`; su regla de las 05:18 (3 bucles + 4 pasadas): `…-director-parte-4.md` (este último solo está en `main` por ahora). Arquitectura viva del Router y del chat: `Readme arquitectura router inteligente universal/ARQUITECTURA-ROUTER-Y-CONEXIONES.md`. Nota de checkpoint completa (para quien llega sin contexto): `Claude notas/CHECKPOINT-2026-09-29-1100-router-chat-plugins.md`. Bitácora del checkpoint: `Estado y handoff global/BITACORA.jsonl` (B-0022 en adelante).

## ESTADO EN UNA MIRADA (checkpoint 2026-09-29, ~11:20 Bogotá)
Marcas: ✅ VERIFICADO (ejecutado + probado + 4 pasadas de revisión + 3 rondas limpias seguidas, regla del Director de las 05:18) · 🟡 HECHO SIN PROBAR / probado a medias · 🔴 PENDIENTE · ⛔ BLOQUEADO. Los "PASS" antiguos de la tabla de la sección 0 (T-00, T-01, T-03) vienen de corridas reales anteriores a esa regla y NO se han vuelto a auditar con las 4 pasadas: se dejan tal cual y no se suben a ✅.
**NADA está ✅ todavía.** La ronda 1 y la ronda 2 de auditoría independiente del Bloque 1 salieron NO LIMPIAS (sin bloqueadores, pero con defectos reales, ya corregidos en código); hacen falta 3 rondas limpias seguidas.
- 🟡 Cadena de modelos del chat (Bloque 1), código de la ronda 1: hecha y probada en CI en la rama `bloque1-cadena-chat` (sección 10).
- 🟡 Correcciones de la ronda 2: ver el estado de subida exacto en 10.5; en ningún caso tienen CI.
- 🔴 El Router VIVO (Job `6abb503a6b030d633f6a2dca`) NO corre nada de esto: sigue con el código de `main` anterior al Bloque 1. Relanzar solo tras terminar y con el Director al tanto (su orden de las 10:55 lo autoriza tras terminar el Router).
- 🟡/🔴 Plugin Host mínimo (Bloque 2): lo construye otro agente; al 11:20 no hay código suyo en la rama (comprobado con git). Sin pruebas ni CI.
- 🔴 Bloque 3, Hermes/OpenClaw, salto directo NVIDIA→Groq, IA local, autoescalado, pantalla final y las decisiones del Director: sección 17 (lista roja completa).
- Cosas que las notas anteriores decían mal y aquí se corrigieron: sección 18.

## 0. Tareas del Router (todas las que tienen que ver con el Router viven aquí)
| # | Tarea | Estado |
|---|---|---|
| T-00 | Auditar el Router y dejar uno solo | PASS |
| T-01 | Limpieza de Hugging Face (la parte de Vercel queda para después, por orden del Director) | PASS (HF) · Vercel pendiente |
| T-03 | Quitar Cerebras del Router y poner Groq | PASS · Router relanzado con el código nuevo y Groq Qwen 3.8 en la cadena g2 (smoke run 36528065394) |
| T-10 | Conectar cualquier repo/MCP al Router único sin crear otro Router | 🟡 DOCUMENTADO (`CONECTAR-ROUTER.md`, reescrito a las 11:20) · sin probar desde otro repo · 🔴 CORREGIDO 11:20: la guía decía llamar a `/chat/send` sin `provider`; eso falla (en la rama da 400 `MODEL_REQUIRED`; en main, 422 por falta de `model`). Hay que mandar `"provider":"auto"` (el texto vuelve en `reply`), y `auto` solo existe cuando el Router corre el código de la rama (por el código de `main` que corre hoy el Router vivo daría 400 `PROVIDER_UNKNOWN`; no se probó en vivo). El cliente `RouterCliente` (`chat router/05-AGENTES/colmena/router_cliente.py`, líneas 105-108) NO manda `provider` y busca el texto en `response/content/text/message`: 🔴 pendiente de parche (no se editó código) |
| T-11 | IA local en máquina de 32 GB (DFlash 2, MTP, etc.) | 🔴 PLANIFICADO · DESPUÉS de terminar Router y pendientes (orden del Director). Hoy NO hay ninguna IA local corriendo (solo existe la puerta `local`) |
| T-12 | Cadenas del chat con NVIDIA: Kimi K3 → GLM-5 → DeepSeek V4 Flash | 🟡 HECHO Y PROBADO EN CI en la rama `bloque1-cadena-chat` (no ✅): cadena `default` = Kimi K3 → GLM 5.3 → DeepSeek V4 Flash → Qwen 3.8 (Groq) → Nemotron ÚLTIMO, usable con `/chat/send` `provider:"auto"`. Detalle, corridas y cifras: sección 10. Falta: 3 rondas de auditoría limpias, unir la rama a main y relanzar el Router (el Job vivo no corre este código). (Estado a las 05:00, que sigue siendo cierto en `main` y en el Router vivo: "PENDIENTE, hoy el chat solo tiene Nemotron; los agentes ya priorizan así"). Orden 04:41: Nemotron pasa a ÚLTIMA opción → T-20 |
| T-13 | Prioridad de claves: chat + Hermes + OpenClaw en NVIDIA 1–3; si ocupadas → 4 o Groq | 🟡/🔴 PARCIAL. Hecho en la rama, solo para el CHAT: las llaves NVIDIA se prueban en el orden del pool (`NVIDIA_API_KEY`, `_1` … `_5`; el Job solo recibe 1–4), la que falló hace poco pasa al final y, si las 4 fallan para un modelo, la cadena sigue a la siguiente opción. 🔴 Falta: Hermes y OpenClaw NO se tocaron; NO hay salto directo a Groq cuando NVIDIA está ocupada (hoy: claves 1→4 dentro de cada modelo NVIDIA y luego la siguiente opción, GLM 5.3, antes de llegar a Groq). (Corregido: el texto anterior decía "`run_policy` usa siempre la llave 1", y es incorrecto: `run_policy` pasa la 1ª llave pero `core.key_pool` la expande a todo el pool y `resilience.Router.execute` las prueba por orden de salud.) |
| T-14 | Autoescalado 16→32 GB (sube al 80 %, duerme a los 5 min) | 🔴 NO EXISTE · PENDIENTE (verificado en el código a las 05:00; no reverificado hoy) |
| T-15 | Plugin abierto en el Router (enchufe) para no tocar más el Router | 🟡/🔴 EN CONSTRUCCIÓN por otro agente (Plugin Host mínimo con el chat como primer plugin, sección 15); al 11:20 no hay código del Plugin Host en la rama. Director 05:15 (textual): "Si Pero explica lo de el tribunal ?" → enfoque aprobado; su OK a la propuesta del tribunal sigue 🔴 PENDIENTE. DISEÑO HECHO: "Plugin Host" = contrato/registro/failover/salud de Fables + regla del harness DeepSeek (quitable, sin dependencia dura, degradado no bloquea). Aprobado el enfoque a las 05:15 (arquitectura §8); tribunal sin OK |
| T-16 | Selector de grupos/combinaciones + subrouters + thinking, sin romper el principal | 🔴 PENDIENTE (Bloque 3). DISEÑO en arquitectura §9 (thinking = modos de ejecución de una ficha). Director 05:15 (textual): "si montalo y se enciende luego lo pones con notas en rojo como pendientes la idea es poder encender en el chat o en el panel del router" → montar el ZIP APAGADO con interruptor tras revisar su seguridad; no hecho. ZIP de otra IA sigue SIN VERIFICAR |
| T-17 | Verificación cruzada contra lo que hizo Opus | 🔴 EN CURSO, sin terminar (resultado parcial abajo; falta comparar archivo por archivo contra la rama `backup-antes-limpieza-20260929`) |
| T-18 | Prueba del Router y conectar al equipo del plan 4 objetivos (= T-04 global) | 🔴 PENDIENTE |
| T-19 | Revisar aceleradores HF y qué se puede usar en máquinas de 16 y 32 GB | 🔴 PENDIENTE (inventario de otra IA recibido, SIN VERIFICAR) |
| T-20 | Lista de modelos disponibles + Nemotron último + salto de llaves NVIDIA→Groq (orden 04:41) | 🟡 HECHO Y PROBADO EN CI en la rama (no ✅): `model_pool.py` pide `/models` a NVIDIA y Groq y salta lo no listado o enfriado; Nemotron quedó último en `default`. Cadena aprobada por el Director a las 05:15 ("Si ese flujo Pero igual el router debe pedir a la api repuesta de modelos disponibles"). 🔴 Falta: el salto DIRECTO NVIDIA→Groq (ver T-13) y el autodescubrimiento por familia cuando un proveedor renombra un id. (Antes: "DISEÑO en arquitectura §6 · espera aprobación de la cadena") |
| T-21 | Sistema paralelo (documento de Mavis / MiniMax) para hasta 1000 procesos mientras haya API o IA local | 🔴 PENDIENTE (Bloque 3: gobernador de capacidad paralelo/cola). DISEÑO en arquitectura §10. Pregunta resuelta el 05:15 (textual): "Si dejarlo con la posiblidad de que crezca que este los cimientos … algunas en paralelo y otras en cola la dos opciones disponibles siempre" → sin tope fijo en el código |
| T-22 | Fichas de Fables: registro + validación + compilador ficha→flujo + mini-chat operador + detección automática de conexiones | 🔴 PENDIENTE (Bloque 3). DISEÑO en arquitectura §4, §5, §7 · el Director mandó construir todo lo posible y anotar en rojo lo que no alcance (05:15) |
| T-23 | Conectar la Run UI al Router (ejecución real, lista real de modelos, quitar modelos de Anthropic) | 🔴 PENDIENTE A PROPÓSITO: la UI va al FINAL (Director 05:15: la Run UI y las fichas verdes de Fables son prototipo, no versión final; modo manual y modo agente; la skill de diseño la da él más adelante). Faltan además `css/` y `js/` de `fgh.html` e `index.html` |
| T-24 | Cablear dataset Yaiwes + plano de control Yaiwes como anclajes de ficha | 🔴 PENDIENTE (plugin ya existe, cableado reservado al último nodo; Bloque 3) |
| T-25 | (SIN DEFINIR) | El pedido del checkpoint mencionaba T-11..T-25, pero ni el archivo de hechos ni el repo definen una T-25: NO se inventó. Si existe, que el Director o el coordinador la definan |

## Órdenes 2026-09-29 (Director, 02:06 y 02:35) — plan de 4 pasos
Regla: se planea todo y se sube UN SOLO Job a Hugging Face al final. Nada se instala antes.
- Paso 1 (anotar textual): HECHO — `INPUT-BLOCK-VERBATIM-2026-09-29-director.md` (+ parte 2 con los mensajes de las 03:26, 03:27 y 04:41). Fidelidad: los textos del Director están copiados tal como llegaron; lo pegado de otras IAs va marcado SIN VERIFICAR.
- Paso 2 (motores de descarga): PENDIENTE — primero leer los commits de Opus sobre el motor de descarga y extracción; usar ese motor, no otro.
- Paso 3 (archivos de Fables 5): LEÍDOS. El Director los subió en el commit `2f5c111e` a `Documentos del proyecto/Documentos proyectos router inteligente universal/` (~37 archivos: Run UI, paneles v1–v5, resumen v6, enchufe v2, bus de plugins, Mavis, etc.). Resultado y qué falta: `ARQUITECTURA-ROUTER-FICHAS-FABLES.md` (§2 y §13). Faltan los `css/` y `js/` de `fgh.html` e `index.html`.
- Paso 4 (integrar y probar): 🔴 PENDIENTE en conjunto. El Director contestó las preguntas de la arquitectura (§15) a las 05:15 (textual en `…-director-parte-3.md`); el Bloque 1 ya está construido en la rama (sección 10) y los Bloques 2 y 3 siguen pendientes (secciones 15 y 17).

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
- Ese orden vale para los agentes. Estado a las 05:00 (histórico): la cadena del chat (`resilience.py`) era solo Nemotron (y Groq en g2). HOY (11:20): la rama `bloque1-cadena-chat` ya tiene Kimi K3 → GLM 5.3 → DeepSeek V4 Flash → Qwen 3.8 (Groq) → Nemotron último (sección 10); en `main` y en el Router vivo sigue la cadena vieja (`default` = solo Nemotron y sin respaldo autorizado; `g2` = Nemotron → Groq → local → DeepSeek; leído en `resilience.py` de main, blob `ae0013c5`) hasta unir la rama y relanzar. La regla "NVIDIA 1–3, luego la 4 o Groq" solo se cumple a medias (T-13).
- Prueba en vivo 2026-09-29 (NVIDIA, 4 llaves): `moonshotai/kimi-k3` 200 en 0,8 s; `z-ai/glm-5.3` 200 en 1,3 s (no existe "glm-5" a secas); `z-ai/glm-5.3-flash` y `deepseek-ai/deepseek-v4.1-flash` sin respuesta en 25 s en las 4 llaves (arranque en frío sin confirmar: NO CONFIRMADO; no se usan hasta probarlos otra vez).

### T-14 Autoescalado (Director)
- Regla dada: el Router de 16 GB corre 24/7 (con el conector MCP) y es el que despierta a los demás; el siguiente procesador se enciende al llegar al 80 %; el de 32 GB se duerme a los 5 min sin llamadas. Hermes, chat y OpenClaw usan procesadores de 16 GB y saltan al siguiente según necesidad; los de 32 GB son para IA local, generar código y correr workflows por llamada.
- Verificado en el código: NO está construido. `hf_scheduler.py` solo elige entre HF1/HF2/HF3 con tope de 95 % de RAM y nadie lo llama; `hf_jobs_compute.py` puede lanzar un Job pero solo si se lo piden. Opus lo dejó como pendiente B2.6 (con 80 %/85 % y 15 min; el Director ahora dice 80 % y 5 min: manda el Director).

### T-15 Plugin abierto
Candidatos leídos el 2026-09-29: (a) `ruflo-deepseek-harness` (Node; aporta 3 reglas: quitable, sin dependencia dura, si falla devuelve estado degradado; llama directo a la API de DeepSeek, cosa que NO se copia porque los modelos solo van por el Router), (b) bus de plugins de Fables + Kimi (`universal_plugin_bus_v2_integrated.py` y `ficha_contract_v2.py`; contrato, registro, failover, salud, presupuesto, evidencia; límites: `trigger_plugin` no ejecuta nada, exige aprobación de "tribunal", el intercambio en caliente usa `exec` con una revisión de seguridad por texto), (c) el validador y el esquema v2 que ya están en `enchufe/` y `domain/schemas/`. Decisión propuesta: "Plugin Host" que junta lo mejor de los dos sobre `RedUniversal` (que ya invoca conectores) — ver arquitectura §8.

### T-16 Selector / subrouters / thinking
El ZIP de otra IA (`yaiwes_subrouters_modulares.zip`) trae 4 subrouters (instant, thinking, council, code), perfiles en un JSON y `GET /chat/subrouters/catalog`, apagado por defecto. SIN VERIFICAR (sus pruebas eran simuladas), no aplicado. El Router de hoy no envía parámetros de razonamiento a los proveedores (`providers.py` manda solo model, messages, max_tokens, temperature). Propuesta: los modos de thinking son plantillas de ficha (arquitectura §9).

### T-17 Verificación cruzada con Opus (resultado parcial)
- Los documentos de Opus (`chat router/03-ESTADO/OPUS-PENDIENTE.md` y `RECUPERACION-OMNIROUTE.yaml`, 2026-09-27) ya no están en main: la limpieza general del 2026-09-29 (orden del Director) los quitó. Existen en la rama `backup-antes-limpieza-20260929`.
- No creé un Router nuevo. Sobre el Router de Opus solo hice: quitar Cerebras, poner Groq Qwen 3.8, corregir la ruta del banco tras la reorganización (`vault_bridge.py`) y fijar una variable en el lanzador. Pruebas de aquella corrida (36526076292; el conjunto que corre `riu-chat-mvp-verify`, SIN VERIFICAR el alcance exacto): 168 pasan, 8 fallan (ya fallaban), 0 errores. OJO: esa cifra NO es comparable con la de la carpeta de pruebas completa del Bloque 1 (`main` 153 pasan / 8 fallan / 6 errores); esos 6 errores están en `test_vault_wordflow_jobs`, el mismo grupo que el arreglo del puente del banco había dejado en 0. La diferencia NO se ha reconciliado (posible causa: entorno o alcance distinto de los flujos; SIN VERIFICAR).
- Construido por Opus y todavía presente (según su nota, no re-probado por mí hoy): chat con Kimi K3, Groq con las claves 2–7.
- Pendiente de la lista de Opus que NO está construido: autoescalado, OmniRoute como proveedor (además el Director eliminó OmniRoute: esos puntos quedan CANCELADOS), aviso de modelos en el chat, montar módulos de los espejos, puente de almacenamiento HF. Nota (releído en `app.py` el 11:20): `app.py` todavía intenta montar `omniroute_proxy`, que no existe; el `try` lo tolera. También sigue el archivo `.github/omniroute-relaunch.trigger` (resto de OmniRoute; 🔴 decidir si se borra).
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
1. RESUELTO EN LA RAMA, no en el Router vivo: la cadena `default` de la rama ya incluye Groq Qwen 3.8 (el Director dijo "Si ese flujo" a las 05:15). En `main` y en el Router vivo sigue siendo solo NVIDIA hasta unir la rama y relanzar.
2. Vercel: `RIU_ROUTER_URL` quedó vieja con el relanzamiento (dirección fija).
3. El smoke prueba `/chat/send` y `/chat/jev` con provider=hf, que falla siempre (`PROVIDER_KEY_MISSING:hf` / 401): no es un fallo del cambio. Falta una prueba de chat real por NVIDIA/Groq (SIN VERIFICAR que responda). Actualización 11:20: en el runner de CI (NO en el Router vivo) sí se probó `/chat/send` con `provider:"auto"` y llaves reales (sección 10.3); contra el Router vivo sigue SIN VERIFICAR.

### T-10 — Conectar cualquier repo/MCP al Router único (documentado)
Hecho: `CONECTAR-ROUTER.md` (cómo hallar la dirección, cabeceras, secretos que necesita cada repo, cliente existente `RouterCliente`, qué hacer si el Router se mueve).
Falta: probarlo de verdad desde otro repo (una corrida corta que lea el archivo de dirección y llame `/health`). Y decidir si hace falta un envoltorio MCP del Router (SIN VERIFICAR que exista; si se hace, se cablea lo descargado, no se escribe desde cero).

### Arreglo hecho tras la reorganización
El puente del banco (`integration/chat_mvp/vault_bridge.py`) buscaba la carpeta vieja `Chat Mvp`. Ahora busca `Banco de claves` (commit 3744d9b4). Pruebas antes: 162 pasan, 8 fallan, 6 errores; después: 168 pasan, 8 fallan, 0 errores (run 36526076292; no comparable con la carpeta de pruebas completa del Bloque 1, ver sección 18 punto 8).
Los 8 fallos que quedan existían antes de este cambio (no verificado si vienen de la reorganización): `test_conector_gitlab_v6` (acción desconocida), `test_conector_interno_webhook_v6` (2), `test_conector_mcp_app_v6` (2), `test_conector_vps_v6`, `test_fast_close_global_e2e` (502), `test_huggingface_openai_chat_registry` (conjunto de modelos).
Ruta vieja que queda sin importancia: `riu-agent11-canonical-download.yml` (mira `hermes-agent/` en la raíz). (El comentario de `resilience.py` que citaba `Chat Mvp/router_policy/peak.py` ya está corregido en la rama, commit 352327a4; en `main` seguirá el comentario viejo hasta unir la rama.)

## 1. Qué es el Router
- Es UNO solo. Todo lo que se construya se conecta a él; no se crean routers nuevos. El chat es UN plugin más conectado al Router (Director, 10:55), no el centro.
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
  - `/chat/send` con `"provider":"auto"` (el Router elige el modelo con la cadena `default`; el texto vuelve en `reply`): existe SOLO en el código de la rama; el Router vivo, por el código de `main` que corre, respondería 400 `PROVIDER_UNKNOWN` (no probado en vivo) hasta que se una la rama y se relance. Sin `provider` la petición falla siempre (ver T-10).
- También montadas (sin probar): `/chat/route`, `/chat/jobs/run`, `/memoria/*`, `/gh/*`, `/control/*`.
- Prueba de solo lectura: `.github/workflows/riu-router-smoke.yml` (botón manual). El resultado se lee en las anotaciones de la corrida.

## 4. Ruta de modelos (orden del Director)
Orden anterior (03:26): NVIDIA (hasta 4 claves; Kimi K3 o el más nuevo) → Groq (Qwen 3.8) → DeepSeek V4 Flash al final. Sin APIs de Anthropic. Cerebras y OmniRoute eliminados. **Orden 04:41: Nemotron como ÚLTIMA opción, y el Router pide la lista de modelos disponibles** (T-20). HOY (11:20) en la rama: Kimi K3 → GLM 5.3 (NVIDIA) → DeepSeek V4 Flash (hf) → Qwen 3.8 (Groq) → Nemotron último, con la lista de modelos disponibles construida y probada en CI (🟡, sección 10); todavía NO corre en el Router vivo.
Estado del Router VIVO (verificado 2026-09-29 con el smoke 36528065394; sigue siendo cierto porque el Job no se relanzó): cadena g2 = NVIDIA `nvidia/nemotron-3-super-120b-a12b` → Groq `qwen/qwen3.8-27b` (DeepSeek V4 Flash al final, se salta en hora pico). La cadena por defecto sigue solo NVIDIA (sin respaldo autorizado en el código de main). Esto cambia al unir la rama y relanzar.

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

## 10. Bloque 1 — cadena de modelos del chat en el Router (checkpoint 11:20)
Marca global: 🟡 HECHO Y PROBADO EN CI (código de la ronda 1) + 🟡 correcciones de la ronda 2 sin CI. NO ✅ (rondas 1 y 2 de auditoría no limpias; el Router vivo no corre este código).

### 10.1 Dónde vive (rama `bloque1-cadena-chat`, todavía NO unida a main)
Carpeta `router inteligente universal/integration/chat_mvp/`:
- `model_pool.py` (nuevo): pide `/models` a NVIDIA y Groq (plazo 6 s por proveedor, como máximo 2 llaves, caché 300 s o 60 s si la lista quedó desconocida); enfriamiento de 120 s por modelo que falló (`RIU_MODEL_COOLDOWN`); al terminar el enfriamiento UNA sola petición prueba el modelo con un "arriendo" de 30 s y las demás lo siguen saltando; si el filtro deja la cadena vacía se intenta la cadena completa (`POOL_EMPTY_TRY_ALL`).
- `resilience.py`: `DEFAULT_POLICY` con 4 grupos (sección 10.2), plazo por opción, cortacircuitos por (proveedor, hash de llave, modelo) y limitador adaptativo 3→10 espacios (espera ≥ 5 s sube a 10; ≥ 20 s responde `ROUTER_SATURATED`).
- `route_api.py`: `/chat/route`, `/chat/router/status`, `/chat/router/models` (es un REPORTE: no gasta la sonda única) y `/chat/jev`.
- `router.py`: `/chat/send` con `provider:"auto"`; `/chat/providers` lista "auto" primero; `/chat/providers/auto/models` devuelve un seudo-modelo.
- `providers.py`: `ATTEMPT_DEADLINE` (plazo de la opción en curso; viaja por `contextvars` hasta la llamada HTTP).
- Pruebas: `router inteligente universal/tests/test_model_pool.py`, `test_resilience.py` (más `test_nvidia_pool.py` sin cambios y `test_chat_mvp_app.py`).
- CI permanente: `.github/workflows/riu-chat-mvp-verify.yml` de la rama incluye las dos pruebas nuevas y se dispara al cambiar `integration/chat_mvp` (commit b2d79924); los commits con `[skip ci]` no la disparan.
- Flujo TEMPORAL de verificación: `.github/workflows/tmp-bloque1-cadena-verify.yml` vive SOLO en `main` (blob `a86b3504`) y se borra al terminar; la copia que había en la rama ya se quitó (commit 375594b7).

### 10.2 Las 4 cadenas, tal como están en `resilience.DEFAULT_POLICY` (leído en el código de la rama)
Todos los grupos tienen `authorized_fallback: True`. Una cadena se recorre en orden; cada opción es (proveedor, modelo):
- `default` (la que usa el chat con `provider:"auto"`): Kimi K3 (`nvidia`, `moonshotai/kimi-k3`) → GLM 5.3 (`nvidia`, `z-ai/glm-5.3`) → DeepSeek V4 Flash (`hf`, `deepseek-ai/DeepSeek-V4-Flash`, marcado `deepseek`: se salta en hora pico) → Qwen 3.8 (`groq`, `qwen/qwen3.8-27b`) → Nemotron (`nvidia`, `nvidia/nemotron-3-super-120b-a12b`) ÚLTIMO.
- `code`: MiniMax M3 (`hf`, `MiniMaxAI/MiniMax-M3`) → Nemotron.
- `minor` (con `peak_only_minimax`): DeepSeek V4 Flash → Nemotron → MiniMax M3; en hora pico de DeepSeek SOLO queda MiniMax M3 (se saltan DeepSeek y Nemotron).
- `g2`: Kimi K3 → GLM 5.3 → Groq (modelo por `RIU_G2_GROQ_MODEL`) → local (modelo por `RIU_G2_LOCAL_MODEL`) → DeepSeek V4 Flash → Nemotron. Reescrito por Claude el 2026-09-29 para poner Nemotron último: falta el OK del Director (🔴).
- Hora pico de DeepSeek: 01–04 y 06–10 UTC, lunes a viernes (`PEAK_WINDOWS_UTC`; fuente `Banco de claves/router_policy/peak.py`, comprobado que el archivo existe). En hora de Bogotá (UTC−5): 20:00–23:00 de domingo a jueves y 01:00–05:00 de lunes a viernes. En ese horario el chat automático NO usa DeepSeek (decisión del Director pendiente, sección 17 punto 1).
- Un nombre de grupo desconocido en `/chat/route` usa la cadena `default`. Errores: `NEEDS_DIRECTOR_AUTH` (409) solo saldría si un grupo tuviera `authorized_fallback: False` (hoy ninguno); el resto de fallos de `/chat/route` es 503 con `detail = {error, trace}`; `/chat/send` con `auto` devuelve 502 con un texto plano (ver 10.4, punto 6 de la ronda 2).

### 10.3 Evidencia de CI y en vivo (todo de flujos temporales en el runner; NADA de esto es el Router vivo)
- Corridas del flujo temporal `tmp-bloque1-cadena-verify.yml`: 36557644179, 36561019462, 36562078042 (fuente: archivo de hechos del checkpoint; yo NO consulté las corridas). El flujo compara la rama contra `main`.
- Carpeta de pruebas completa: la rama tiene 183 pasan (cifra del archivo de hechos; la corrida 36561019462, ya citada en la arquitectura, dio 181, y la diferencia de +2 coincide con las dos pruebas del commit 82209701; cuál corrida dio 183 no consta) contra `main` 153 pasan. El MISMO conjunto de 14 pruebas falla en las dos (8 fallos + 6 errores; huella sha256 `fa97bc78c2a8e444`): son `test_vault_wordflow_jobs` (6 errores), `test_conector_*_v6` (6), `test_fast_close_global_e2e` (1) y `test_huggingface_openai_chat_registry::test_allowed_model_ids_does_not_raise_and_matches_runtime_verified` (1). Ya fallaban antes → el bloque no rompió nada.
- Pruebas de la cadena: 42 pasan en CI (coincide con 27 en `test_model_pool.py` + 11 en `test_resilience.py` + 4 en `test_nvidia_pool.py` de aquel momento). Hoy la rama tiene 35 + 12 + 4 = 51 funciones `test_` (conteo por lectura del archivo, no por ejecución); las añadidas después de aquellas corridas NO tienen CI.
- Mutaciones (romper el código a propósito en el runner, sin tocar el repo): 27 de 28 detectadas. La sobreviviente ("respuesta vacía guardada" en `/chat/send` auto) se cubrió con una prueba nueva, `test_send_auto_does_not_save_an_empty_reply` (commit cb781fb4; `test_resilience.py`, blob `ddc69404`). 🟡 Esa prueba necesita FastAPI: solo corre en CI y, según el archivo de hechos, no consta ninguna corrida que la ejecute; tampoco se repitió la mutación con ella.
- En vivo con llaves reales (runner de CI, NO el Router vivo): NVIDIA lista 81 modelos (Kimi K3, GLM 5.3 y Nemotron incluidos) y Groq 11 (Qwen 3.8 incluido). Cadena escalón por escalón: sano → Kimi K3 (1,6 s); Kimi marcado muerto → GLM 5.3; + GLM muerto → DeepSeek V4 Flash (hf); + DeepSeek muerto → Qwen 3.8 (Groq, 0,2 s); + Qwen muerto → Nemotron; todos muertos → se prueba la cadena completa (`POOL_EMPTY_TRY_ALL`) y contesta Kimi. `/chat/send` con `provider:"auto"` mantiene la misma conversación al cambiar de modelo. (Cifras 81/11 y tiempos: de la arquitectura, corrida 36561019462.)
- Aviso sobre el escalón DeepSeek(hf): en el runner se probó con `RIU_CHAT_ALLOW_PROVIDER_LIVE=1` y `HF_TOKEN_1` (comprobado leyendo el flujo temporal y `riu-chat-mvp-verify.yml`); el Job vivo no tiene ninguna de las dos cosas (sección 14) → en el Router vivo ese escalón está 🟡/🔴 hasta corregir el lanzador.
- Kimi K3 respondió lento hoy (25–30 s en 2 de 3 intentos): el Router lo salta tras 30 s (`RIU_CHAT_ATTEMPT_TIMEOUT`) y lo recuerda 2 min (enfriamiento 120 s).

### 10.4 Correcciones de las auditorías
Ronda 1 (NO LIMPIA; ya en el código que pasó CI): (1) un Router saturado ya no marca "modelo muerto"; (2) 400/422 no enfrían el modelo; (3) plazo por opción de 30 s base × `max_tokens`/1024 con tope de 90 s, y la última opción tiene 90 s; (4) las llaves del mismo modelo dejan de probarse cuando se agotó el tiempo de la opción; (5) el cortacircuitos perdona fallos viejos (una llave que falló una vez vuelve a ser la primera); (6) sonda única tras el enfriamiento. Además, por los mensajes de commit de la rama: `/chat/router/models` sigue las mismas reglas que una petición real (`POOL_EMPTY_TRY_ALL`, grupo sin autorización), "Automático" primero en `/chat/providers` con seudo-modelo, `RIU_MODEL_COOLDOWN` tolerante a valores inválidos y la cita textual del Director corregida (04:41 / 05:15).
Ronda 2 (NO LIMPIA; subidas a la rama entre las 11:14 y las 11:18, SIN CI): (1) el tiempo esperando un hueco del limitador ya no se le cobra al modelo; (2) cualquier excepción de una opción pasa a la siguiente (antes solo `RuntimeError`); (3) un Router saturado corta la cadena al instante con `ROUTER_SATURATED` y no enfría modelos (en `/chat/route` sale 503; en `/chat/send` con `auto` sale 502 con ese texto: ver sección 18); (4) los arriendos de sonda no usados o sin veredicto se devuelven (`release`, solo el propio); (5) `RIU_CHAT_ATTEMPT_TIMEOUT` que no sea un número finito (`abc`, `nan`, `inf`) vale 30; (6) el 502 de `/chat/send` con `auto` trae un texto plano ("ERROR | traza ; traza", máximo 900 caracteres) en vez de un objeto, porque la pantalla actual del chat escribe `detail` dentro de una frase; (7) docstring del cortacircuitos: se añadió que half-open deja pasar a TODOS los que llegan, pero la PRIMERA frase de ese docstring todavía dice "lets one probe through after `cooldown` seconds" (contradice el párrafo nuevo y el código): 🔴 corregir esa frase; (8) comentario de `peak.py`: ya estaba corregido en la rama desde la ronda 1 (commit 352327a4), no es un cambio de la ronda 2; (9) `z-ai/glm-5.3-flash` y `deepseek-ai/deepseek-v4.1-flash`: "posible arranque en frío: NO CONFIRMADO: no se usan hasta probarlos otra vez" (solo comentario).
Pruebas nuevas de la ronda 2 en `test_model_pool.py` (8 nuevas y 1 renombrada; 27 → 35): `test_a_404_is_never_retried_on_another_key_and_the_first_key_is_tried_even_when_the_time_is_spent`, `test_a_busy_router_stops_the_chain_at_once_and_is_not_a_dead_model` (antes `test_a_busy_router_is_not_a_dead_model`), `test_a_probe_lease_that_was_never_used_is_given_back`, `test_a_probe_that_ends_without_a_verdict_gives_the_lease_back`, `test_a_success_settles_the_pool_and_the_breaker`, `test_a_typo_in_the_attempt_timeout_setting_falls_back_to_30`, `test_any_exception_from_one_option_moves_the_chain_on`, `test_release_only_gives_back_its_own_lease`, `test_the_wait_for_a_free_slot_is_not_charged_to_the_option_time`. En `test_resilience.py` cambió una aserción (el 502 ahora es texto). Pruebas locales del agente (con un `pytest` de mentira sin FastAPI): `test_model_pool.py` 35 pasan, 0 fallan; `test_resilience.py` 7 pasan y 5 figuran como "fallan" porque en realidad se SALTAN (necesitan FastAPI: solo corren en CI).

### 10.5 Estado de subida de la ronda 2
Estado de subida comprobado con `git fetch` a las 11:33 (Bogotá); rama `bloque1-cadena-chat` en el commit cb229a12. Un archivo cuenta como subido solo si el blob de la rama es igual a `git hash-object` del archivo local:
- `router inteligente universal/integration/chat_mvp/resilience.py` [cambio de la ronda 2]: local `c3043881` · rama `c3043881` → SUBIDO (blob igual)
- `router inteligente universal/integration/chat_mvp/model_pool.py` [cambio de la ronda 2]: local `34df8847` · rama `34df8847` → SUBIDO (blob igual)
- `router inteligente universal/integration/chat_mvp/router.py` [cambio de la ronda 2]: local `3b0445af` · rama `3b0445af` → SUBIDO (blob igual)
- `router inteligente universal/integration/chat_mvp/route_api.py`: local `83d2e677` · rama `83d2e677` → SUBIDO (blob igual)
- `router inteligente universal/integration/chat_mvp/providers.py`: local `bd96dd07` · rama `bd96dd07` → SUBIDO (blob igual)
- `router inteligente universal/tests/test_resilience.py` [cambio de la ronda 2]: local `26255aa3` · rama `26255aa3` → SUBIDO (blob igual)
- `router inteligente universal/tests/test_model_pool.py` [cambio de la ronda 2]: local `cc5b8fa1` · rama `cc5b8fa1` → SUBIDO (blob igual)
- `router inteligente universal/tests/test_chat_mvp_app.py`: local `fd64ad22` · rama `fd64ad22` → SUBIDO (blob igual)
Veredicto: las correcciones de la ronda 2 en resilience.py, model_pool.py y router.py están SUBIDAS a la rama. Siguen SIN CI (ninguna corrida las ha ejecutado).

### 10.6 Lo que NO está probado
- El Router vivo (Job de Hugging Face) no corre este código; el código importado no se recarga solo: hay que relanzar.
- Las correcciones de la ronda 2 no tienen CI; las pruebas que necesitan FastAPI solo pueden correr en el runner.
- La pantalla `chat_ui.html` no se tocó (lista "Automático" como un proveedor más, con una fila de clave que no sirve porque en automático se ignora `X-Provider-Key`).
- El escalón DeepSeek(hf) en el Job vivo (falta `HF_TOKEN_1` y `RIU_CHAT_ALLOW_PROVIDER_LIVE=1`, sección 14).

## 11. Auditorías independientes del Bloque 1
Regla del Director (05:18, textual): "una vez que hagas una salida cuando termines haces 3 bucles de revisión de todo verificación cruzada con el code fuente y los archivos y las instrucciones 4 pasadas por tarea terminada sin eso no está 100 pass ✅". Cómo se aplica (interpretación de Claude, `…-director-parte-4.md`, no texto del Director): 4 pasadas por tarea (instrucciones, código fuente, archivos y documentos, ejecución) y 3 vueltas seguidas de todo el bloque sin hallazgos nuevos.
- Ronda 1: NO LIMPIA (sin bloqueadores, con defectos reales). Correcciones en 10.4; ya pasaron CI.
- Ronda 2: NO LIMPIA (sin bloqueadores, con defectos reales). Correcciones en 10.4; subidas a la rama y SIN CI.
- Siguiente: 🔴 una ronda 3 después de que la ronda 2 tenga CI. Para ✅ hacen falta 3 rondas limpias seguidas.
- Los hallazgos abiertos de las auditorías que todavía NO son cambios de código (decisiones del Director o trabajo pendiente) están en la sección 17.

## 12. Incidente de las mutaciones (lección que no debe repetirse)
El script de mutaciones local (`mutate2.py`) se interrumpió a las 10:55 cuando el Director rechazó la llamada y dejó UNA mutación aplicada en el árbol de trabajo local (`model_pool.py` sin el bloque del arriendo de sonda). Se detectó a las 11:1x porque las pruebas locales fallaban (3 fallos) ANTES de subir; se restauró y quedó 35/35. Nada mutado llegó al repo (la comprobación de que el `model_pool.py` de la rama coincide con el archivo restaurado está en 10.5).
LECCIÓN: (1) nunca correr mutaciones sobre el árbol de trabajo: hacerlo en una COPIA o en CI; (2) correr las pruebas locales ANTES de cada push. (Es distinto del incidente de la sección 8, el vigilante de 32 GB.)

## 13. Órdenes del Director vigentes (con qué texto consta cada una)
- 10:55 (entre comillas tal como está en el archivo de hechos): "Ok termina el router y activalo / El chat es solo un plugins más conectado al router" → autoriza RELANZAR el Job del Router tras terminarlo; el chat es UN plugin más, no el centro.
- 11:07 (paráfrasis del archivo de hechos; el texto literal NO está en el repo): checkpoint progresivo (bitácora, estado JSON, handoff, "Claude notas", Crazy Wall) por si Anthropic se satura; no desviarse; terminar el Router primero (prioridad 1) con un agente en paralelo auditándolo; luego chat + agentes (prioridad 2): DSL DAG con loops, agente orquestador, Hermes y OpenClaw como asistente / sheriff / sentinela / supervisor / juez / guardián / investigador de contexto / manipulación de memoria y almacenamiento, harness de DeepSeek; el sistema debe poder generar un espejo (mirror) solo de Hermes+OpenClaw o de todo el equipo, y varias UI de chat una debajo de otra, todo separado, nada monolítico.
- 11:11 (paráfrasis del archivo de hechos; el texto literal NO está en el repo): delegar varias tareas a varios agentes (Claude escribe el código, los agentes hacen lo demás) para terminar lo antes posible.
- 05:18 (textual, `…-director-parte-4.md`): la regla de 3 bucles + 4 pasadas (sección 11).
- 05:15 (textual, `…-director-parte-3.md`): cadena aprobada, lista de modelos disponibles, paralelo y cola, tribunal explicado, ZIP montado apagado, UI al final, todo en GitHub (HF solo puente/túnel, datasets de IA, almacenamiento y procesador), y "sintetizar y no resumir".
- 02:06 (textual, `INPUT-BLOCK-VERBATIM-2026-09-29-director.md`, línea 36): "El chat y los agentes de Hermes y open claw prioridad con Nvidia si está ocupado las primeras 3 Salta a la 4 o a groq". ALCANCE: cubre el chat Y los agentes de Hermes y OpenClaw. Hoy solo se cubre el chat (a medias, ver T-13); Hermes y OpenClaw NO se tocaron (🔴).
- Cadena aprobada del chat: Kimi K3 → GLM 5.3 → DeepSeek V4 → Qwen 3.8 (Groq) → Nemotron ÚLTIMO; si uno falla cae al siguiente; el Router pide a la API los modelos disponibles.

## 14. Activación del Router (relanzar el Job): pasos y huecos
- El Router es un Job de Hugging Face cpu-basic 16 GB, lanzado por `.github/workflows/riu-router-job-central.yml` (leído en `main`). Job vivo: `6abb503a6b030d633f6a2dca` (dato del archivo de hechos y de la sección 1; no lo reverifiqué en vivo). Autenticación: `Authorization: Bearer <HF_TOKEN_1>` + `X-API-Key: <RIU_ROUTER_API_KEY>`.
- Cambio seguro: el lanzador espera `/health` 200 del Job nuevo, escribe `LIVE_URL` en `router inteligente universal/agents-yaiwes/ROUTER_JOB_PAUSE.flag` y SOLO ENTONCES cancela los Jobs viejos.
- Huecos verificados en el lanzador: (a) NO pasa `HF_TOKEN_1` al Job: los secretos del Job son solo `GITHUB_TOKEN`, `RIU_ROUTER_API_KEY`, `RIU_AGENT_API_KEYS`, `NVIDIA_API_KEY_1..4` y `GROQ_API_KEY_2..7` (el `HF_TOKEN_1` del flujo lo usa el propio lanzador para hablar con Hugging Face); (b) NO pone `RIU_CHAT_ALLOW_PROVIDER_LIVE=1` (el único `env` del Job es `RIU_G2_GROQ_MODEL`). Efecto: el proveedor `hf` lee `HF_TOKEN` o `HF_TOKEN_1`; sin ellos (y sin que el banco desbloqueado aporte un token: SIN VERIFICAR) el escalón DeepSeek V4 Flash fallaría rápido y la cadena seguiría a Qwen 3.8. Plan: agregar ambos al lanzador (es un cambio de workflow: hoy NO hecho) e informar al Director.
- Pasos: (1) CI verde de la rama; (2) Plugin Host mínimo con el chat como primer plugin; (3) unir a `main`; (4) relanzar (la orden de las 10:55 ya autoriza relanzar tras terminar); (5) verificar `/health`, `/chat/router/status`, `/chat/send` con `provider:"auto"` y la lista de plugins; (6) borrar los workflows temporales (`tmp-bloque1-cadena-verify.yml`).
- Tras relanzar la URL cambia: `RIU_ROUTER_URL` de Vercel queda vieja. NO se toca Vercel ni el Space MCP `claude-github-mcp-backup` sin orden explícita.

## 15. Plugin Host (Bloque 2, EN CONSTRUCCIÓN por otro agente) y Bloque 3 (pendiente)
Marca: 🟡/🔴 EN CONSTRUCCIÓN. Al 11:20 no hay `plugins/`, ni `ficha.json`, ni código de Plugin Host en la rama (comprobado con `git ls-tree`); no hay pruebas ni CI. Lo que sigue es el DISEÑO (de `ARQUITECTURA-ROUTER-FICHAS-FABLES.md` §8 y `universal_plugin_bus_v2_integrated.py` de Fables), no lo que ya funciona:
- Plugins en `plugins/<id>/ficha.json`, montados UNA vez por el Router.
- Regla del harness de DeepSeek: envoltura obligatoria en cada llamada, removible, sin dependencia dura; ante fallo o timeout devuelve `{status:'degraded', reason}` sin tumbar el Router.
- NO se ejecuta código de terceros: el `ContractGenerator` y el `HotSwapManager` de Fables usan `exec` y NO se copian.
- "Tribunal" = comprobaciones automáticas + OK del Director; su OK a esa propuesta sigue 🔴 PENDIENTE.
- 🔴 Sin cablear de lo de Fables: failover declarativo, presupuesto por nivel, evidencia L1–L4, hot-swap, sandbox C13.
Bloque 3 (pendiente; va en rojo si no se llega): registro de fichas, compilador ficha→`riu.dag/v1`, agente operador, autodetección; gobernador de capacidad paralelo/cola; ZIP `yaiwes_subrouters_modulares.zip` (modos de pensamiento): revisar su seguridad y montarlo APAGADO con interruptor (notas en rojo); conectores plugin (HTTP, SSH, MCP, push al celular; lo que necesite dependencias o llaves que no hay queda 🔴); dataset Yaiwes y anclas del Control Plane (T-24).

## 16. Otros pendientes vigentes
- IA local (DFlash 2, MTP, Flash Attention, KV Q8, Qwen 3.8 Q4 en la máquina de 32 GB) SOLO después del Router y sus pendientes (T-11).
- Autoescalado: la de 16 GB siempre encendida despierta a las otras; escalar al 80 %; la de 32 GB duerme a los 5 min (T-14).
- Cruzar con lo previo de Opus (rama `backup-antes-limpieza-20260929`) (T-17); T-18.
- Rotar las 7 llaves Groq (acción del Director).
- Restaurar `Claude notas/HANDOFF-PARCHE-RECUPERACION-2026-09-21.md` (solo existe en la rama de respaldo).
- Regla de infraestructura: todo en GitHub; HF solo puente/túnel, datasets de IA, almacenamiento y cómputo.
- Reglas permanentes: sin llaves en el repo (público; solo nombres de secretos); modelos solo por el Router único (NVIDIA hasta 4 llaves → Groq → DeepSeek V4 Flash; Nemotron ÚLTIMO); Cerebras y OmniRoute eliminados; sin APIs de Anthropic; descargas solo por el motor de descarga/extracción; Vercel = solo UI, UN despliegue final cuando lo ordene el Director (auto-deploy OFF); no tocar ni reiniciar el Space MCP `claude-github-mcp-backup` (`keep-mcp-space-awake` sigue deshabilitado); no borrar componentes, solo reubicar; la raíz del Router debe poder moverse a otro repo; sin código desde cero (podar, cirugía, cablear lo descargado).

## 17. Lista roja completa 🔴 (todo lo abierto; nada de esto es un cambio de código hecho)
Hallazgos de las auditorías → decisiones del Director o trabajo pendiente:
1. DeepSeek se salta en horas pico (01–04 y 06–10 UTC, lunes a viernes) en las cadenas `default` y `g2` (y en `minor` solo queda MiniMax) → decisión del Director.
2. El grupo `minor` deja a Nemotron segundo.
3. La reescritura del grupo `g2` (Nemotron último) necesita el OK del Director.
4. No hay salto directo a Groq cuando NVIDIA está ocupada (regla de las 02:06): hoy solo funciona por el orden de llaves y la cadena. Hermes y OpenClaw sin tocar.
5. Una respuesta vacía de un modelo NO cuenta como fallo (no pasa al siguiente; en `/chat/send` sale `empty: true` sin guardarse) → decisión.
6. Un fallo enfría el modelo 120 s para TODOS (diseño deliberado).
7. La cadena no tiene plazo TOTAL (hasta ~210–450 s: 4 opciones × 30–90 s + 90 s de la última) y se dice que Vercel tiene `maxDuration` 60 → decisión. (No encontré `maxDuration` en `Vercel/vercel-chat/vercel.json` ni en `api/chat.js`; SIN VERIFICAR de dónde sale el 60; no se consultó Vercel.)
8. El timeout HTTP es por lectura de socket, no de reloj de pared (`urllib.urlopen(timeout=…)` en `providers._http`).
9. No hay single-flight en las llamadas a `/models`; `/chat/router/models` no tiene límite de frecuencia.
10. Los ids del proveedor `hf` (DeepSeek V4 Flash, MiniMax M3) no están certificados y requieren `RIU_CHAT_ALLOW_PROVIDER_LIVE=1` (hoy NO puesto en el Job) y `HF_TOKEN_1` (hoy NO pasado al Job).
11. Restos de OmniRoute: el intento de montar `.omniroute_proxy` en `app.py` (dentro de un `try`) y `.github/omniroute-relaunch.trigger`.
12. Workflows temporales siguen en `main` (`tmp-bloque1-cadena-verify.yml`) → borrar antes de terminar.
13. Persistencia del estado de plugins / interruptor entre reinicios del Job (el Job es efímero): sin resolver.
14. La UI no se toca (la opción "Automático" ya aparece en la lista del chat actual; la UI final va al último).
15. La URL del Router cambia al relanzar → `RIU_ROUTER_URL` de Vercel quedará vieja; NO se toca Vercel ni el Space MCP sin orden explícita.
16. Las rondas 1 y 2 de auditoría salieron NO LIMPIAS; se necesitan 3 rondas limpias seguidas para ✅.
Otros 🔴 vigentes: Plugin Host y Bloque 3 (sección 15); Hermes/OpenClaw en la regla 02:06; autodescubrimiento por familia cuando un proveedor renombra un id (`glm-5` → `glm-5.3`; hay algo parecido en `agents-yaiwes/common/routes.py`, `disponibles()`, NO importado para no acoplar); candidatos NVIDIA sin probar (`kimi-k2.6`, `nemotron-3-ultra-550b-a55b`, `nemotron-3.5-lightning-30b-a3b`); salud por (clave, modelo): una clave colgada se vuelve a aprender modelo por modelo (hasta 30 s por cada modelo nuevo); la latencia de Kimi K3 varía y el límite de 30 s puede cortar un Kimi lento pero vivo (ajustable con `RIU_CHAT_ATTEMPT_TIMEOUT`); solo NVIDIA y Groq tienen lista de modelos consultable (no `hf`, `deepseek`, `moonshot`, `minimax`, `local`); el modo automático de `/chat/send` no usa caché, ignora `X-Provider-Key` y devuelve siempre `certified: false`; las 14 pruebas que ya fallaban en `main` (huella `fa97bc78c2a8e444`); restaurar `HANDOFF-PARCHE-RECUPERACION-2026-09-21.md`; T-11, T-14, T-17, T-18, T-19, T-21, T-22, T-23, T-24; rotar llaves Groq; parche de `RouterCliente` (sección 18); primera frase del docstring del cortacircuitos (10.4, punto 7).

## 18. Correcciones y contradicciones halladas al escribir este checkpoint (verificadas leyendo el repo a las 11:20)
1. `CONECTAR-ROUTER.md` decía que `/chat/send` se llama con `{"message":…,"max_tokens":…}` y que el texto vuelve en `response`, `content`, `text` o `message`. Falso: sin `provider` la petición falla (rama: 400 `MODEL_REQUIRED`; main: 422 por falta de `model`), y el Router devuelve el texto en `reply`. Corregido en `CONECTAR-ROUTER.md`. `RouterCliente` tiene el mismo error (no manda `provider`; su `_extract_text` no mira `reply` y devolvería el JSON entero): 🔴 sin parche.
2. El archivo de hechos dice que un Router saturado corta con `ROUTER_SATURATED` (503). En el código eso es 503 solo en `/chat/route` (`route_api.py`, líneas 62-64); en `/chat/send` con `auto` cualquier `RouteFailed` sale como 502 con texto plano (`router.py`, `except RuntimeError`).
3. El mismo archivo lista el comentario de `peak.py` como corrección de la ronda 2; en realidad ya estaba corregido desde la ronda 1 (commit 352327a4).
4. La corrección del docstring del cortacircuitos quedó a medias: la primera frase todavía dice "lets one probe through" (10.4, punto 7). Además esta arquitectura decía "una prueba" para el half-open: incorrecto, corregido en `ARQUITECTURA-ROUTER-Y-CONEXIONES.md`.
5. El salto de DeepSeek en hora pico también aplica a `minor` (allí solo queda MiniMax), no solo a `default` y `g2`.
6. La tabla decía en T-13 que `run_policy` usa siempre la llave 1: incorrecto (T-13, texto corregido).
7. `Vercel/vercel-chat/api/chat.js` llama a `/chat/send` con `provider:"hf"` y `model:"deepseek-ai/DeepSeek-V4-Flash"` fijos, no con `auto`: 🔴 al ordenar el despliegue final hay que cambiarlo (NO se tocó Vercel).
8. Cifras de pruebas de fuentes distintas no cuadran a simple vista (168/8/0 de la corrida 36526076292 frente a 153/8/6 de main con la carpeta completa; 181 frente a 183 en la rama; 42 en CI frente a 51 funciones hoy): explicaciones en T-17 y en 10.3; la primera SIN reconciliar.
9. La cita de la regla de las 02:06 en la arquitectura estaba parafraseada; ahora va textual (sección 13).
10. T-25: no existe en ninguna fuente (T-25 de la tabla).

## 19. Cómo comprobar el estado de subida y el CI sin fiarse de estas notas
- `git fetch origin bloque1-cadena-chat main` y comparar `git rev-parse origin/bloque1-cadena-chat:"<ruta>"` con `git hash-object "<ruta>"` de tu copia local, archivo por archivo (10.5 lista las rutas).
- Las cifras de CI de esta nota vienen del archivo de hechos del 11:15 y de la arquitectura; para verlas de nuevo hay que abrir las corridas 36557644179, 36561019462 y 36562078042 del flujo temporal (no se consultaron al escribir esto).
