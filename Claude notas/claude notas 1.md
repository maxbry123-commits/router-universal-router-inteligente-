# Claude notas 1 — UNICO archivo de notas (fuente de la verdad)

Actualizado: 2026-10-04 17:50 (Bogotá). Autor: Opus, por orden del Director (Hy).
- Este es el UNICO archivo de notas de Claude. No crear otros (orden 17:48).
- Las órdenes del Director van TEXTUALES. Si algo de Claude contradice al Director, vale el Director.
- Sin claves ni tokens en este archivo. La clave del Director y los tokens viven en el banco.
- Historial anterior (órdenes textuales del 2026-10-03 y madrugada del 2026-
16) 2026-10-06 (Devin). Orden textual: "Ponle incluso 10 mecanismos adicionales" / "Solo el sistema de las api usa las fichas todo dentro de la fichas nada fuera de las fichas" / "el router de huggueface de respaldo no lo toque".
Hecho y verificado en job 6ac4acd7 (LIVE_URL en GitHub): failover entre proveedores conservando el trabajo, checkpoint persistente en memoria SQLite del bucket (sobrevive cambio de job), ultima clave buena primero (_BUENA), claves muertas marcadas (401/403/429), deteccion ampliada de servicio ocupado, dedup de llamadas a herramientas, herramientas rotas marcadas, tool_call truncado limpiado, frontend reintenta fetch releyendo LIVE_URL y reintenta en PROCESO_NO_EXISTE/SERVICIO_OCUPADO. Commits b7be21fae9 y be87d3689e en main. L4 respaldo intacto.

17) 2026-10-06 (Devin). Orden textual: mini-agente determinista tipo sheriff/validador/sentinela que envuelve a la LLM en bucle LOOP/coda no-stop, salida unica = checklist, dentro de las fichas, copiado con el motor de copiar, sin HF ni GH Actions.
Hecho: fichas/sentinela.py (71 lineas) + plugins/puente_chat/fichas/sentinela.py, cargado por plugin.py via importlib. Bucle ejecutar(plan, mensajes, guardar_ck, cargar_ck): pasos modelo -> retoma -> reserva de proveedor; cada fallo guarda checkpoint en memoria y la vuelta reinicia desde el ultimo checkpoint. Salida: checklist items COMPLETADO/REANUDADO en salida['checklist']. Copiado a la raiz de fichas con motor_3_copy_batches.py (VERIFIED_CLOSED). Job 6ac4b4dc verificado: los 5 modelos API responden con herramientas y checklist. Commits 344b12f216, 433abf15fc.

## 18) Fichas pipeline + adjuntos + estética (2026-10-06)

Orden del usuario (verbatim): dos fichas nuevas en el selector — 🧠 ask consil factory (paso0 investigación con los motores de búsqueda del repo: 10 webs dev + HF + GitHub; paso1 Ultra 550B propone 12 goals; paso2 consil de 12 pasos: Groq propone, Muse Glimmer refuta y propone, Kimi decide; paso3 nemotron-3-super ejecuta; paso4 Kimi refactoriza con 12 goals de salida) y ➡️ MOTOR DESCARGA (Embed 1B ancla/busca, Muse Glimmer dirige los motores de descarga/extracción/copiar/mover del repo, solo esos motores). Tarea 2: 📎 adjuntar → almacenamiento/memoria anclados + ventana para ver/seleccionar/anclar + botón copiar en salida e input. Tarea 3: mejorar estética del chat móvil.

Hecho:
- fichas/modelo-ask-consil-factory.json (tipo "consil") y modelo-motor-descarga.json (tipo "motor"); motores canónicos copiados con motor_3_copy_batches a fichas/motores_busqueda/ (motor_1 web, motor_2 github, motor_3 hf + sources.json) y fichas/motores_descarga/ (motor_1 extract, motor_2 download+extract, motor_3 copy, motor_4 move, hf_download_extract_engine).
- plugin.py: _consil() y _motor_descarga() (embed-1b /v1/embeddings rankea el motor, muse da plan JSON {env, explicacion}, se ejecuta solo ese motor por subprocess); _paso_llm usa _llamar_api con rotación/ocupado; acciones subir (b64→memoria 'archivo:NOMBRE') y archivos (lista); chat acepta payload.anclados → inyecta contenido en el system.
- ficha.json allowed_actions += subir, archivos (el host rechazaba "accion no permitida por la ficha").
- Frontend: config.js +2 fichas; panel-chat 📎/🗂/⧉, ventana de archivos con checkboxes de anclaje, burbujas con botón copiar; api.js accion() + harness anclados; shell.css estética (burbujas redondeadas, composer compacto, selects con flecha, modal).
- Verificado en vivo job 6ac55ace: modelos lista las 2 fichas; subir/archivos OK; motor-descarga ejecutó motor_3_copy_batches VERIFIED_CLOSED; consil COMPLETÓ los 5 pasos (paso0 motores → ultra 12 goals → 3 rondas consil → super ejecuta → kimi 12 goals salida); groq responde con checklist.
- L4 respaldo intacto. Commits: db0bfbd2a9, 445d79fef0.


## 19) Chat UI compacta + multi-chat + sandbox + motores xray/auditor/handoff (2026-10-06)

Orden (verbatim): "Estos botones son demasiado gigante reducelos al mínimo posible… abrir un nuevo chat una nueva sección… 3 o 5 estancias de chat diferentes corriendo tareas diferentes… motor de auditoría forense x Ray de archivos… motor auditor de code de los repo… selector de ancla… handoff en Jason… Todos los botones solo selector de encender y apagar… Usa mi skills Maxbry UI fromtend para todo… Todo en Github donde está el chat nada en vercel nada en huggueface nada de Github acción… Todo organizado en un solo carpeta adjunto al chat."

Hecho y verificado en vivo (job 6ac578a8, LIVE_URL publicada):

- Frontend (chat router/chat frontend/, una sola carpeta): selects → pildoras compactas que abren hojas (estilo Grok/Claude): modelo, modo, ⚙ más (selects secundarios dentro), ⚓ ancla. Control → toggles encender/apagar. Pestañas de chat hasta 5 estancias, cada una con su propia sesion → tareas en paralelo en el servidor. Botón 🧪 sandbox (system prompt de code persistido en memoria por sesion e inyectado al system prompt del modelo). Archivos: anclar por chat + botón X-Ray por archivo. Selector ⚓ genera handoff JSON (chat router/, 01-PLAN/SKILL.md, preview Vercel) anclado al input.
- Backend (todo dentro de las fichas/puente_chat): acciones nuevas xray, auditor_code, handoff, sandbox (en ficha.json allowed_actions). xray = auditoría forense: urls + estructura raíz + mapa mental + microflujo horizontal + goals G1..G12 (nemotron-super). auditor_code = git-tree del repo clasificado por carpeta (30124 archivos). handoff = JSON de chat router/, SKILL.md o preview. sandbox = memoria 'sandbox' por sesion.
- Fichas nuevas en el selector: motor-xray (tipo xray) y motor-auditor-code (tipo auditor) → 11 modelos. ESPECIALES/FICHAS aceptan tipos xray/auditor.
- api.js: sesion por pestaña (multi-chat paralelo); harness/accion la propagan.
- Verificado vivo: handoff skill/chat-router, auditor_code (30124), sandbox (modelo respondió "hola CLAVE"), subir/archivos, xray acción y ficha motor-xray por chat con anclados.
- Sin Vercel, sin HF respaldo (L4 intacto), sin GH Actions.
