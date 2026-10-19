# HANDOFF — Orquestación de modelos (Devin ↔ modelos por chat)

## Estado al 2026-10-19 (rama feat/modos-router, PR #27 abierto)

### Archivos entregados por el usuario (todos en el repo)
- `fichas/` (router inteligente universal/plugins/fichas_qwen/fichas/): 33 archivos — PROMPT_PARA_DEVIN.md, INSTRUCCIONES_DEVIN_MODOS.md, INSTRUCCIONES_ADICIONALES.md, ficha1-5 JSONs, modes_registry.json, mode_router, validate_*, loop_controller, mythos_engine, objective_store, prompt_import, research_sources, test_*
- `contratos/` (workflow Loops code Yaiwes/contratos/): 8 loop_contract.*.json
- `skills/` (workflow Loops code Yaiwes/skills/): wordflow-code-deploy-router.skill, SKILLS-MAXBRY-UI/diseno/ (~20 archivos styles.css + demos)
- `chat router/01-PLAN/FROMTED-YAIWES-*.png` — imágenes de referencia frontend
- `INSTRUCCIONES_INPUT_BLOCK_VERBATIM.md` — 125 inputs verbatim 1:1
- `INSTRUCCIONES_ADICIONALES.md` — spec Mythos m09 + LoopController + prompt_import + fix --exclude + seguridad m08

### Hecho y verificado en vivo
- Modos m01-m11: selector frontend + mode_request + slash commands + MODE_ERROR unknown — probado
- `loop_run`: acción real del LoopController con contratos DAG — probado (DONE + token)
- FIX Claude (gobernanza→system, tarea→user etiquetada, detector ACK + retry layout D): aplicado y desplegado — prueba A/B real PASS
- `validate_contract.py --exclude n06_final` (fix §6 ADICIONALES)
- 87 reglas YAML de las instrucciones verbatim + rules_engine + converter
- Panel 📋 Pendientes: funciona (pendientes-panel.js → puente_chat)
- `import os` faltante en puente_chat (bug real corregido)
- models-ci.yml de Claude eliminado (usaba GitHub Actions — prohibido por facturación)

### GAPs identificados (pendiente code de Claude o decisión)
1. **Flag `motor` no se propaga a la ruta ficha** — leído en plugin.py L2324 (`_MOTOR_HAB.set(bool(p.get('motor')))`), la ficha no lo manda → modelos en tarea no ven motor_descargar/extraer/copiar/mover. Verificado ×2 (yo + qwen38max).
2. **TIMEOUT_NODO 150s** — Claude: separar 3 relojes (NODE_TOTAL/ATTEMPT/TOOL_EXECUTION) + deadline dinámico `min(config, deadline-now-reserve)`; nodos con retry llevan deadline mayor, no subir el tope global. Diseño completo en README §8.
3. **dsv4pro/dsv4flash** — RESUELTO ✅ (deploy 2026-10-19): layout D primario para ficha-dsv4* + `enable_thinking` off (intento 1) / on (reintento) via `dsv4_think` + fallback de modelo a qwen38max/glm52 si acusa x2. Probado en vivo: dsv4flash->'4 layouts', dsv4pro->'A_system_user' (evidencia real).
4. **7 categorías de fallo** — `exec_dispatch.py` de Claude (INPUT 128) copiado a modos/ con classify OK/ACK/VACIO/HERRAMIENTA_NO_EJECUTADA/MODEL_ERROR + Profile con cuarentena + 11 tests PASS. Integrado parcial: fallback de modelo en acuse (layout F). Falta cablear como executor completo del LoopController + timeout por intento (3 relojes).
5. **GLM 5.2 vía Qianwen** — verificar `extra_body={"tool_stream":True}` si sigue intermitente.
6. **ROOM CONFERENCIAS** — existe `room_debatir` (tema, participantes ≤6, rondas 1-3, asincrono); falta acción `enviar_mensaje` para que Devin/AI externo escriba un mensaje suelto + integración MCP HTTP/JSON (tarea de qwen38max).
7. **Motores→tools anclables** — `motor_descargar/extraer/copiar/mover` + `_motores_buscar` (motor_1..3) ya existen; quedan tras el flag `motor` (GAP #1). Fichas modelo-motor-descarga/xray/auditor ya registradas.
8. **dsv4pro ficha config** — su entrada en ficha1-modelos.json es idéntica a qwen38max; el problema es el modelo (thinking), no la ficha.

### Tareas del usuario pendientes de ejecución por modelos
- T1 revisión fichas ×3 (glm52 ✅ PASS · qwen38max ✅ PASS · dsv4pro ❌ bloqueado #3)
- T2 frontend gaps (dsv4pro→reasignado qwen38max: 5 GAPs citados, 1 falso positivo) + backend qwen38max ✅
- T3 frontend Maxbry UI desde imágenes+skill — necesita tools de escritura (GAP #1)
- T4 canvas OSS componentes → chat (qwen38max) — idem
- T5 refactor frontend dsv4→qwen (misma sección)
- T6 botón/selector trabajo paralelo minimax
- T7 review 3× no-flash + botones reales Maxbry UI
- X-Ray audit: dsv4flash parcial · qwen36 ✅ PASS (11 modos)
- Watchdog auditor: archivo 1.1MB > límite API GitHub → leer por rangos/índice
- Backlog INPUT ~100-121: T0-T3 ventanas/moves, I1-I3, P4, F1, G-series, FASE 1 (bloqueada: falta fuente maestra)

### Cómo despacha Devin (receta que funciona)
`POST /plugins/fichas_qwen/call/chat_async` con `{ficha_qwen:"1", task_type:"code", modelo:"ficha-*", sesion:"<nombre>", message:"<prompt corto imperativo>"}` → poll `/call/resultado` con `proceso_id`. Prompts cortos imperativos ("Usa tu herramienta GitHub AHORA + 1 tarea + formato") — los largos devuelven texto plano.

## N8 HANDOFF — DSL DAG CORREGIR CABLEADO TOOL-CALLING (2026-10-19, commit 3767ddd)

### Tabla modelo | categoria | tool | ms | reintentos | PASS/FAIL (N7 real, Space redeployed)
| modelo | categoria | tool real | ms nodo | reintentos | PASS/FAIL |
|---|---|---|---|---|---|
| ficha-qwen38max | EXECUTED | github_leer (1 call) | 6316 | 0 | PASS |
| ficha-qwen38flash | EXECUTED | github_leer (6 calls) | 29812 | 0 | PASS |
| ficha-glm52 | EXECUTED | github_leer (4 calls) | 19640 | 0 | PASS |
| ficha-dsv4pro | EXECUTED | github_leer (1 call) | 8930 | 0 | PASS |
| ficha-dsv4flash | EXECUTED | github_leer (1 call) | 5712 | 0 | PASS |
| ficha2 consulta | completado | lectura repo | ~ | 0 | PASS |
| ficha3 plan | completado (GAP juez) | lectura repo | ~ | 0 | PASS (sin TIMEOUT_NODO) |

Nota: LIVE_URL.json no contiene job_id (campos: LIVE_URL, runtime, space_id, hardware, updated, auth, harnessUrl) — los 5 modelos lo leyeron con evidencia y reportaron la ausencia en vez de inventar. Criterio cumplido: EXECUTED + tool real + < tope.

### Commits
- 3767ddd DSL N1-N5: estado por nodo en ContextVar, required solo paso 1, acuse con evidencia, deadline por nodo, fuente unica de politicas
- 5a077a4 fichas JSON: contrato reintento Claude + tool_stream GLM + per_attempt dsv4 + lectura >1MB (INPUT 129 x4 pasadas)
- f54435a conectar prompt layout D ejecutor (INPUT 129) en reintento y dsv4 primario
- 36f6a17 N5: fallback_modelo distinto por modelo (glm52->qwen38max, qwen38max->glm52); el JSON ya no lista a un modelo como su propio fallback
- (bundle desplegado: router-bundle.tar.gz 308MB -> bucket; backup .bak NO creado: HfFileSystem.cp no soportado en buckets -> GAP menor)

### Que se borro y por que
- fichas_qwen/modos/exec_dispatch.py + test_exec_dispatch.py -> nadie lo importaba (DSL N5: integrar o borrar; se borro, el camino HTTP existente queda unico)
- politicas_modelo en ficha2/3/4 -> copias muertas (solo ficha1 es fuente via _politica; primera ficha del glob ganaba siempre)
- lectura_archivo_grande en ficha1 (x6) -> nota operativa, no config; movida a README-ORQUESTADOR-MODELOS.md
- per_attempt_s/max_attempts/reintento en tarjetas modelo-*.json -> claves sin lector en codigo (el reintento vivo es el de politicas_modelo en ficha1); tarjetas restauradas byte-identicas a HEAD

### N1-N5 implementado
- N1: _NODO_CALL ContextVar ({sys_prompt,forzar_tool,dsv4_think,per_attempt_s,deadline,max_attempts}) set/reset por nodo; _llamar_harness_1 lee del ContextVar, no de opts compartido -> nodos paralelos de _dag() ya no se pisan
- N2: tool_choice=required solo paso 1 del reintento (_FORCE_TOOL.set(None) tras paso 1 en _bucle); dsv4 reintento con enable_thinking=false explicito
- N3: si r.herramientas tiene ok -> EXECUTED, no reintento; traza clasifica EXECUTED|ACK_ONLY|NO_TOOL|TOOL_IN_REASONING|DISPATCH_FAILURE|TIMEOUT
- N4: deadline = inicio + timeout_s; api_s = min(per_attempt, deadline-5s); <20s restantes -> no otro intento ni fallback; fallback max 1 modelo (excluye a si mismo)
- N5: fuente unica = politicas_modelo de ficha1; bloque reintento ahora LO LEE el codigo (per_attempt_s, max_attempts, fallback_modelo); glm52 nunca es su propio fallback
- N6: 56 tests existentes + 4 nuevos test_dsl_cableado = 100% verde
- N9: PENDIENTE — auditoria independiente de Claude Sonnet (no la hago yo)
- PENDIENTE: auditoria de las fichas por GLM 5.2 — 2 intentos, TIMEOUT_NODO a 150s sin emitir tool calls (api.z.ai lento en tareas largas de lectura); la opinion de qwen38max si llego y se aplico (lectura_archivo_grande)


## DSL G1–G19 (2026-10-19) — sistema único, biblioteca de capas, motor de objetivos, buzón y paralelo

Implementado por DEVIN en `feat/modos-router`. Audita: CLAUDE SONNET (N9).

| G | Cambio | Archivo |
|---|--------|---------|
| G1 | UN solo system: SYSTEM_CORE + Constitución + ROL DEL NODO + capa B + anclas/memoria/handoff fusionados; system entrante del nodo ya no duplica | puente_chat/plugin.py |
| G2 | Rol ≤600 chars dentro del user tras `</tarea>` como `<rol>` en layout D (dsv4) | fichas_qwen/plugin.py |
| G3 | El user siempre cierra con "Responde con el RESULTADO..." (`_CIERRE_USER`) | fichas_qwen/plugin.py |
| G4 | Evidencia real: `_ejecuto` del delta `opts['herr'][nid]`; categorías EXECUTED/ACK_ONLY/TOOL_IN_REASONING/NO_TOOL/TIMEOUT/DISPATCH_FAILURE | fichas_qwen/plugin.py |
| G5/G9 | `_politica_ficha(fid)` consulta directa; fuente única `fichas/politicas_modelo.json` (ficha1/ficha4 solo referencian) | puente_chat/plugin.py + fichas/ |
| G6 | Reintento por modelo con fallback correcto (qwen38max↔glm52, otros→qwen38max), thinking off | fichas/politicas_modelo.json + plugin.py |
| G7 | `_NODO_CALL` ContextVar con try/finally reset | fichas_qwen/plugin.py |
| G8 | Tests reales `tests/test_g_gaps.py` (6/6: G1,G2+G3,G4,G7,G17,G18) | fichas_qwen/tests/ |
| G10 | Biblioteca del prompt por capas `chat router/workflow Loops code Yaiwes/prompt/` (system_core ≤3000 tok, bloques 1-5, reglas SRC-001..114); capa B por nodo (`_CAPA_NODO`), tool `regla_yaiwes` (capa D, máx 5/nodo) | prompt/ + puente + herramientas |
| G11 | glm52 `con_tools.tool_stream=false` | politicas_modelo.json |
| G13 | Recorte con prioridad memoria→anclas→handoff/sandbox; NUNCA core/const/rol/tarea/cierre; marca `[recortado: bloque N chars]` + traza | puente_chat/plugin.py |
| G14 | `requiere_evidencia` + mutación + aprobado → PASS solo con ≥1 tool ok (mutacion_real si escribe), si no `GAP SIN_EVIDENCIA` | fichas_qwen/plugin.py |
| G15 | `capas` por modo en modes_registry (rapido→core, code→core+b3, auditor→core+b4, plan→core+b2+b5) + `reglas_revision` determinista (1 corrección → GAP REGLA_INCUMPLIDA) | modes_registry.json + plugin.py |
| G16/G16b | `fichas/cadenas.json` + `_cadena_para`/`_expandir_cadena` (F1/F4), pausa entre pasos, checkpoint/reanudar reutilizando `_ck_*`, `GAP CADENA_ABANDONADA` | plugin.py + cadenas.json |
| G17 | `modos/motor_objetivo.py` (correr_objetivo, max_vueltas=20) + activación payload `objetivo`/modo `loop` + `fichas/programas.json` + `modos/programador.py` (hilo 30 s) | modos/ + plugin.py |
| G18 | Tool `delegar_paralelo` (≤6 paralelo, ≤12 subtareas, `_PROF_DELEGACION` un nivel, subagentes solo lectura) | puente_chat/herramientas.py |
| G19 | Buzón SQLite (buzon/pendientes_director) + endpoints buzon_enviar/estado_objetivo/responder_pendiente/pendientes_director + `preguntar_director` + buzón mid-loop `[DIRECTOR, en vivo]` + frontend (selector, Pausa/Continuar/Cancelar, panel Cola 3 s) | plugin.py + herramientas.py + panel-chat.js + ficha.json |

### T_REAL (Space redeployado, 2026-10-19)

| modelo | estado | evidencia |
|--------|--------|-----------|
| Qwen 3.8 Max | completado | github_leer LIVE_URL real, reportó ausencia de job_id |
| Qwen 3.8 Flash | completado | idem |
| GLM 5.2 | completado | idem |
| DeepSeek V4 Pro | completado | idem |
| DeepSeek V4 Flash | completado | idem |

Commits: `d9fd131` (G1-G19 core), `276ca41` (allowed_actions + frontend + G16b). Tests locales: `test_g_gaps.py` 6/6 PASS.

### Pendiente para el audit (N9, Claude Sonnet)
- G1/G2/G3: el system final es UNO con bloques; rol dsv4 en user.
- G13: el recorte nunca toca core/const/rol/tarea/cierre.
- G17/G18/G19: motor, buzón y paralelo por los endpoints reales.
