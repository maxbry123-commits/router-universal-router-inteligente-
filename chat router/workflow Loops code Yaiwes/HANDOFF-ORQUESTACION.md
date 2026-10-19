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
3. **dsv4pro/dsv4flash no ejecutan** — `reasoning_effort:'high'` en perfiles.py envía los tool calls al reasoning (nunca se despachan). Claude (INPUT 126): D_solo_tarea directo + thinking toggle por intento. Fix: enable_thinking off en primer intento + per-attempt timeout. Esperando OK de Antonio.
4. **7 categorías de fallo** — hoy todo colapsa en HERRAMIENTA_NO_EJECUTADA; falta executor con contrato de ejecución (`run_node_with_execution_contract`): ACK/NO_TOOL→retry D, TOOL_IN_REASONING→parser fallback, timeouts→idempotencia.
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
