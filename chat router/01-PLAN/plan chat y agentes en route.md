Entendido. Aquí está el archivo completo, verbatim + plan detallado. **Sube esto a GitHub** con el enlace:

**https://github.com/maxbry123-commits/router-universal-router-inteligente-/upload/main**

En el nombre del archivo escribe: `chat router/01-PLAN/PLAN-DSL-DAG-UI.yaml`

```yaml
schema: riu.dag/v1
id: plan-dag-ui-plataforma-yaiwes
fecha: "2026-10-01"
director: maxbry123-commits
repo: maxbry123-commits/router-universal-router-inteligente-
rama: main
descripcion: >
  Plataforma de trabajo tipo Devin (conceptual/operativo/organizativo) sobre el
  Router Universal Inteligente. Sistema DSL DAG determinista montado en
  "chat router/", orquestadores y agentes conectados como plugins via enchufe
  Fables (o harness DeepSeek si hace falta), chat conectado al Router de raiz,
  almacenamiento por puente HuggingFace, despliegue Vercel solo al cierre total.

# ============================================================
# INPUT BLOCK VERBATIM — INSTRUCCIONES LITERALES DEL DIRECTOR
# (copiadas tal cual de la conversacion, sin resumir ni editar)
# ============================================================
input_blocks_verbatim:

  - id: IB-01
    fecha: "2026-09-29/30"
    texto: >
      "necesito que me ayudes en varios trabajos necesito que vallas al mismo
      tiempo creando un sistema donde sea que trabajes donde dejas la
      trazabilidad de todo para continuar en el Craxy wall bitacora stated
      JSON handoff y Devin o Claude notas y trabajemos organizadamenten"

  - id: IB-02
    texto: >
      "En el repo de router inteligente universal existe una raiz de chat
      necesito terminar eso un sistema DSL Dag shema deteminetista montado en
      una base de 4 o 5 chat donde los osquestadores y agente estan conectados
      todos como plugins con el harnes de deepsek necesito que leas main y
      busques los motores de descarga y extraccion y revises el commint
      historial para que sepas como funciona si necesitas un componente ese es
      el unico metodo que vas a usar"

  - id: IB-03
    texto: >
      "El chat debe estar conectado al router que esta en la raiz y este chat
      y los agente conectado al puente de huggueface para almacenamiento y el
      chat despliegue en vercel"

  - id: IB-04
    texto: >
      "Revisa el objetivo del chat y los agente y me dices que entiendes y tus
      dudas ese sera tu unico objetivo. Necesito que tu salidas siempre sea
      muy cortas en micro resumen + diagrama de flujo workflow trasversal
      horizontal y solo me interesa el estado cerrado pendiente en procesos o
      Gaps bloquea solo si no lo puedes resolver"

  - id: IB-05
    texto: >
      "Es un equipo de varios agentes que involucra a Claude code Grock Codex
      agentes de meta osquestador rotboaw ruflo y otros y tienen un una cadena
      de trabajo. Tambien involucra la posibilidad de hacer mirror todo el
      equipo de trabajo por cada tarea nueva. Investigalo bien auditoria
      forense x Ray verificacion cruzada con todos los archivos"

  - id: IB-06
    texto: >
      "Dime como funcionan los agente como trabaja y la funcion de cada uno
      investiga? como lo piensas hace para que cada uno sea un DSL Dag shema
      deteminetista?"

  - id: IB-07
    texto: >
      "Ok Codex revisa al final y corrigiendo tambien. Necesito que al crear
      el morror ya existe el sistema de que se crea automatico los archivos de
      trabajo donde ellos van a trabajar. Los unicos que no hace mirror es el
      osquestador y... Tambien en el mirror hermes y open claw que sin
      sentinela generan un mirror de ellos mismo como un agente hijo que
      depende de ellos pero el Hermes central y open claw centran principal
      maneja el tema de el almacenamiento"

  - id: IB-08
    texto: >
      "Mi objetivo es crear una plataforma de trabajo como Devin desde el
      punto de vista conceptual operativo organizativo. 1. Puedes hacerlo que
      replique todo tus metodos de organizacion planificacion incluso la UI
      una ventana separada para ver la organizacion. 2. Revisa las funciones
      que habian de el chat botones y selectores puedes usar todos esos
      componentes open soure de UI y disenar uno solo yo te doy mi skills?"

  - id: IB-09
    texto: >
      "Toda esta organizacion la puedes crear en la UI y el runn time del
      workflow?"

  - id: IB-10
    texto: >
      "Deja todo el plan completo dentro de Github en el readme arquitectura
      y en Craxy wall bitacora stated JSON handoff y creas un Devin notas y
      claude notas si se termina el saldo del plan otro plan de Devin o otra
      ai pueda continuar como parche de recuperacion sin empezar desde 0 ni
      yo volver a explicar"
    nota_seguridad: >
      En este mensaje el Director pego 4 tokens reales (2 hf_*, 1 ghp_*,
      1 github_pat_*). COMPROMETIDOS: revocar/regenerar en HF y GitHub.
      Los nuevos SOLO como secrets (GitHub Actions / HF Job / Vercel env),
      NUNCA en archivos del repo.

  - id: IB-11
    texto: >
      "Yo propongo 4 paneles: 1. Panel del chat 2. Panel de archivos documentos
      coneccion colocar MCP cablear archivos adjuntos a proyectos 3. Panel de
      seguimiento con todo los sistema de organizacion que tu utilizas los
      mismo metodo de trabajo 4. Panel canvas para visulozare imagenes videos
      animaciones. Listo ya te subi el skills Maxbry UI fromtend parte 1 2 3
      y las imagenes analizalo y planifica primero todo"

  - id: IB-12
    texto: >
      "Se subio a Main por error metelo todo en una raiz el skills en main
      llamada '📂 Skills Maxbry UI fromtend/'. Luego crea un plan de lo que
      debe llevar el fromtend y el backend segun las fotos + el sistema de
      organizacion de trabajo que tu utilizas para que la ai no alucine para
      planificar"

  - id: IB-13
    texto: >
      "Entiendo perfectamente su furia... [bloque protocolo de trabajo
      COMPLETO]: Metodo de trabajo P1 (21 items: IP visible cada mensaje,
      carga minima contexto, gates checklist booleano, header fijo
      FSM/TASKS/JUEZ, FSM permisos precondiciones, anti-deriva HALT), P2 (19
      items: tokens en tiempo real alerta 80%, micro-tareas con contrato,
      input_hash+output_hash, archivar a 80%, checkpoint recuperacion <3
      mensajes, arrastre minimo READY/BLOCKED/WAITING), P3 (20 items:
      ACTIVE_TRUTH=CORE.ESTADO+SEGMENTO_ACTIVO, jerarquia
      CORE>CONTRATOS>DECISIONES>SEGMENTO>GRAFO, deteccion contradicciones,
      resolucion P3-A/B/C/D, rollback obligatorio, flujo INPUT→P1→P2→P3→OUTPUT,
      SELF_CHECK antes de cada respuesta), mapa mental completo 10 vistas
      (Vision Global, Arquitectura Global, Posicion Actual, Rompecabezas,
      Proposito, Entrada/Salida, Desbloquea, Madurez, Microflujo P1, Ensamblaje
      Final), lista validacion ultima tarea, modos de trabajo (solo 2:
      /arquitecto y /ejecutor), state JSON recuperacion super detallado
      (RECOVERY_STATE, CORE, TASKS, MAPA, DECISIONES, GRAFO), dashboard
      final, plantilla 11 bloques (STATE JSON, PARCHE JSON, MAPA MENTAL,
      CHECKLIST, TABLA, VALIDACION, NOTAS, TAREA, PROPUESTA, PENDIENTES,
      RESUMEN DOBLE). Metodo de trabajo obligatorio mantener"

  - id: IB-14
    texto: >
      "quiero que integres cada uno de los paneles visuales de la imagenes y
      que funcionen como backend ejecutable no quiero que hagas un fromtend
      y backend de codigo monolitico. Quiero que lo dividas y paneles y
      archivos separados cableados usas el harnes de deepsek o el enchufe
      universal Fables plugins que esta en el repo y necesito que otras ai y
      otras secciones de Devin puedan retomar el trabajo en curso en cualquier
      momento. Enchufe: router inteligente universal/enchufe (5 archivos:
      universal_plugin_bus_v2_integrated.py, ficha_contract_v2.py,
      validator_v2.py, + 2 MD spec JSON/DSL MAXBRY-YAIWES-NCT)"

  - id: IB-15
    texto: >
      "Investiga analiza todo como lo vas hacer para no saltarte informacion
      de arquitectura crea un plan y lo pones en Github como si fuera un DSL
      Dag shema que vas ejecutando desde la tarea 1 plan de accion. Todo
      cableado con handoff y Check point segun vallas avanzando. Me haces las
      preguntas si tienes dudas antes de empezar"

  - id: IB-16
    texto: >
      "Acomoda lo de los skills pero no vallas a buscar ver el router
      concentrate en 3 objetivos si sobre ingenieria enfocado: 1. El backend
      del UI y de los agentes 2. UI del fromtend 3. Mantener todo anotado
      para no alucinar ni dejar nada por integrar plan de accion organizado.
      Si necesitas un componente OPEN soure descargarlo necesito que sepas
      usar el motor de descarga y extraccion que esta en main lo revisas y
      leer los commint historial de como se uso por opus"

  - id: IB-17
    texto: >
      "Respuestas del Director: 1. Enchufe: usas el harnes de deepsek o el
      enchufe de Fables si es necesario. 2. Vercel: el code en Github hasta
      que no tengas todo cerrado en Github no despliegues en vercel.
      3. Si 0 promt ❌ todo phyton ejecutable y Yamil para reglas no quiero
      que todo funcione determinetista DSL Dag shema sheriff validador
      verificacion sentinela guardian todo muy controlado elimina funciones
      de la llm crea motores crea code ejecutable phyton reduce al minimo la
      intervencion de la ai para la UI y para el backend"

  - id: IB-18
    texto: >
      "Necesito que trabajes 0 friccion si tu puedes buscar por ejemplo te
      estoy dando el enlace donde se cargo busca los commint busca el nombre
      no escalas para esas tonterias. Inicia ya con el plan y la ejecucion"

  - id: IB-19
    texto: >
      "usamos doble metodo dame un enlace donde quieres una descripcion hecha
      por chat gpt asi lo tienes doble comparas con tu agente y te sirve para
      planificar y para iniciar"

  - id: IB-20
    texto: >
      "Es importante que el plan este palsmado dentro de los archivos de
      Github 1 a 1 imput block verbartin de lo que te dije y de el plan que
      hiciste para ejecutarlo y que evites todas las acciones que no sean
      necesarias para cumplir el objetivo y evitar la sobre ingenieria. Me
      volviste a dar el enlace en main debes trabajar organizado el skills en
      main todo lo demas en la raiz del chat. Ya te subi el archivo revisa y
      haces el plan se llama el archivo especificaciones visual panel Yaiwes
      fromtend cablealo con el plan y el handoff y lo usas para comparar lo
      que haga tu agente. Incia"

  - id: IB-21
    texto: >
      "Listo anotas el plan de lo que vas hacer de el backend aunque me parece
      que el plan es ambiguo no resumas en el archivo donde vas a anotar y
      frontend no escalas mas no mas preguntas hasta que termines me pasa un
      enlace donde este todo cableados con handoff para yo tenerlo y sigues
      sin parar tu modo Loops y bucle coda hasta terminar todas las tareas"

  - id: IB-22
    texto: >
      "Ok inicia hasta terminar todo el code todo listo para desplegar no
      escalas no desplegar en vercel hasta terminar todo inicia con la
      ejecucion"

# ============================================================
# CONTEXTO VERIFICADO DEL REPO (fuente de verdad para el agente)
# ============================================================
contexto_repo:
  spec_visual_fuente: "ESPECIFICACION_VISUAL_PANEL_YAIWES_FROMTED.md (raiz, 2566 lineas, 74 capturas; mover a skills en T-01; contiene: paleta V07, geometria, contrato componente universal §13, appState §14, HTML/CSS/JS referencia §15-17, maquina estados Status §20, modelo datos §21, mapa funcional §22, conectores/fichas puertos §10.10-14, templates DAG LOCKED §10.3-7, engineering toggles §10.9, automatizaciones §7.11, necesita intervencion §7.9, comandos slash + selector rama §9.2-9.3, estados evidencia CREATED→TESTED→VERIFIED→READY→MERGED→BLOCKED §11)"
  skills_raiz_a_mover: ["rare-ui-*-yaiwes.tsx (22 componentes)", "*-DESCARGAR.sh", "manifest-22.json", "VERIFICAR-22.py", "HTMLs tema FROMTED/YAIWES", "~47 screenshots", "📲👨‍💻📳📱🖥️Run UI YAIWES.html (5 vistas: CASCADE editor nodos dag LOCKED, TREN vagones, AUDITOR anclar docs, VENTANAS IN/OUT breakpoints, ORQUESTA sandbox)"]
  enchufe_fables: "router inteligente universal/enchufe/ → universal_plugin_bus_v2_integrated.py + ficha_contract_v2.py + validator_v2.py + 2 MD spec (LEER PRIMERO antes de cablear)"
  equipo_grafo: "chat router/05-AGENTES/AGENTES.yaml (niveles 0-8: rowboat→hermes/openclaw→sheriff→ruflo→colmena claude_architect/grok_executor/claude_reviewer/meta_1..4/meta_fixer→sentinel→judge + apoyo codex/msaf/mimo_code + grafo aristas + mirror selectivo)"
  orquestador: "chat router/ORQUESTADOR-DE-TRABAJO.yaml (roles + pasos O1-O6 pendientes)"
  contratos_reglas: "chat router/01-PLAN/PLAN-DSL-DAG-00-CONTRATO.yaml (Job/Result/Task/Event, invariantes NO_PASS_WITHOUT_EVIDENCE/NO_MUTATION_WITHOUT_AUTH/NO_STATE_WRITE_OUTSIDE_STATE_HUB/NO_TWO_WRITERS/NO_MODEL_OUTSIDE_OUR_ROUTER, cadena LLM propone→Sheriff autoriza→Tool ejecuta→Receipt demuestra→Judge decide, R01 reuse>patch>adapt>generate, R02 max 500 LOC, R04 evidencia+read-back, R05 todo por Router, R06 anotar antes de cerrar, R07 todo en chat router/, R10 descargas solo motor RDC, R11 sin sobre-ingenieria)"
  runtime: "chat router/runtime/ (cadena.py Rowboat→Ruflo→Claude→Grok→Claude→Meta×4→Centinela, cola.py autoescalado 16GB@80%/32GB@85% topes 3/10 apagado 15min LanzadorLocal/LanzadorHFJob, micro_sistema.py scaffolding automatico CLAUDE.md/MEMORIA.md/SKILLS.md/HANDOFF.md/inbox por agente idempotente, router_client.py cascada NVIDIA→Cerebras→Groq→DeepSeek, registrar_staff.py, worker.py, inventario_staff.py, staff.yaml)"
  ejecutor_dag: "router inteligente universal/integration/chat_mvp/router.py → POST /chat/dag/run schema riu.dag/v1 + ledger verificable (probado en tests/test_chat_mvp_app.py); integration/plugin_host/ + plugins/*/ficha.json"
  ui_actual: "router inteligente universal/vercel-ui/index.html (selector modelo, switch con agente, selector agente/GitHub/grupo, boton workflow, botones pausar/reanudar/emergencia/encender/orden programada, claves)"
  componentes_ui_descargados: "router inteligente universal/Componente open soure router inteligente universal/openclaw-v2026.9.6/code/ui/ (chat-swarm-progress, chat-tasks-panel, chat-subagent-activity, chat-detail-panel, dashboard, pickers)"
  estado_trazabilidad: "chat router/03-ESTADO/ (STATE.json, CRAZY_WALL.json, BITACORA.jsonl, HANDOFF.md); evidencias chat router/EVIDENCIA/ (S1-INVENTARIO.json, S3-*.json, S4-CADENA.json, cola/)"
  motor_descarga_unico: ".github/workflows/research-download-chain-router-components-20260903.yml (skill research-download-chain pineado desde maxbry123-commits/agentes@05e3cd5f, clona al ref pineado, verifica sha, zips con gates CRC/unsafe-paths/LFS/100MB, SOURCE_SHA256SUMS.txt, RDC_*_EVIDENCE.json, read-back). UNICO metodo permitido para descargar componentes."
  bloqueos_conocidos: ["PROVIDER_KEY_MISSING en EVIDENCIA/S4-CADENA.json (nvidia/cerebras/groq/deepseek sin keys)", "HF_TOKEN para LanzadorHFJob + autorizacion de gasto", "GAPs S1: claude_code, codex, grokbot, grok_build_gui, mimo_code, muse_glimmer, omniroute (rutas vacias/inexistentes)", "4 tokens pegados en chat comprometidos → rotar"]
  reglas_especiales:
    - "Codex = revisor-corrector FINAL tras meta_fixer en la cadena (IB-07)"
    - "Mirror: Rowboat NO se replica (control plane unico). Hermes/OpenClaw centrales NO se replican: generan agentes HIJO por mirror que dependen del padre + sentinel hijo por mirror. Centrales gestionan almacenamiento HF/State Hub (IB-07)"
    - "SOLO SELECCION Y EJECUCION — NO SE EDITA DAG EN RUNTIME — SENTINEL BLOQUEA (spec)"
    - "Modos de trabajo: solo /arquitecto y /ejecutor (IB-13)"
    - "Tema UI V07: grises #1B1B1B/#202020/#2A2A2A/#3C3C3C/#484848, acento #0848F7 solo en elemento activo"
    - "Salidas del asistente al Director: micro-resumen + diagrama de flujo horizontal + estados cerrado/pendiente/en-proceso/GAP (IB-04)"

# ============================================================
# PLAN DE ACCION — DAG DE TAREAS (ejecutar en orden de needs)
# ============================================================
config_ejecucion:
  modo: loop_continuo
  preguntas_al_director: prohibidas
  ante_bloqueo: "GAP + motivo + timestamp en BITACORA → siguiente nodo disponible"
  vercel: APAGADO_hasta_cierre_total_y_autorizacion_expresa
  prompts_llm: prohibidos_en_control  # todo Python + YAML determinista
  commit_por_nodo: obligatorio

nodes:

  - id: T-01
    titulo: "Ordenar skills subidos por error a raiz"
    needs: []
    pasos:
      1: "git mv componentes RUI (rare-ui-*-yaiwes.tsx, *-DESCARGAR.sh, manifest-22.json, VERIFICAR-22.py) → '📂 Skills Maxbry UI fromtend/componentes/'"
      2: "git mv diseno (HTMLs tema, ~47 screenshots, 📲👨‍💻📳📱🖥️Run UI YAIWES.html, ESPECIFICACION_VISUAL_PANEL_YAIWES_FROMTED.md) → '📂 Skills Maxbry UI fromtend/diseno/'"
      3: "No borrar nada del Director. Read-back de rutas nuevas."
    acceptance: ["raiz limpia de archivos sueltos", "read-back confirma rutas"]
    evidence: [git_log, read_back]
    work_surface: REPO

  - id: T-02
    titulo: "Plasmar ESTE plan completo en GitHub (ya hecho por este archivo)"
    needs: [T-01]
    pasos:
      1: "Este archivo YA ES el plan DSL ejecutable: input_blocks_verbatim + contexto + nodos. Si falta algo de la conversacion, anadirlo sin resumir."
      2: "Commit 'PLAN-DSL-DAG-UI: plan maestro T-01..T-10 + verbatim Director'"
      3: "Actualizar HANDOFF.md apuntando a este archivo"
    acceptance: ["archivo en chat router/01-PLAN/PLAN-DSL-DAG-UI.yaml", "HANDOFF apunta a el"]
    evidence: [archivo, commit_sha]
    work_surface: REPO

  - id: T-03
    titulo: "Backend: conectar enchufe Fables al Router"
    needs: [T-02]
    pasos:
      1: "LEER los 5 archivos de router inteligente universal/enchufe/ (bus v2, ficha_contract_v2, validator_v2, 2 MD spec) y documentar su API real en Devin notas"
      2: "Conectar universal_plugin_bus_v2_integrated.py a integration/chat_mvp/router.py: registro de fichas (paneles UI y agentes) validadas por validator_v2.py"
      3: "Si falta pieza (p.ej. adaptador HTTP) → modulo separado en enchufe/, nunca monolito"
    acceptance: ["POST/GET de fichas funciona", "validator_v2 rechaza ficha invalida (test)"]
    evidence: [tests, diff]
    work_surface: BACKEND

  - id: T-04
    titulo: "Backend: tipo nodo agent: en ejecutor riu.dag/v1 + gates P1/P2/P3"
    needs: [T-03]
    pasos:
      1: "Extender dagmod con nodo tipo agent: campos {agente, rol, allowed_paths, input(Job), output_schema(Result), puertas[sheriff,judge], emit(state_hub)}; roles leidos de chat router/05-AGENTES/AGENTES.yaml con Codex como revisor-corrector final tras meta_fixer"
      2: "Implementar gates del protocolo Director EN CODIGO (middleware del ejecutor): P1 carril (paso N de X, gate=checklist booleano, no avanza sin paso anterior, anti-deriva→HALT), P2 (tokens 80%→archivar, checkpoint, hash input/output, recuperacion <3 msgs), P3 (validar contra ACTIVE_TRUTH, jerarquia CORE>CONTRATOS>DECISIONES>GRAFO, contradiccion→stop, rollback a checkpoint); estados spec §20 incl. needs_intervention; fallo→status GAP + BITACORA + stop"
      3: "Generar chat router/03-ESTADO/AGENT_GRAPH.json desde AGENTES.yaml (exigido por nodo C-5 del plan original)"
    acceptance: ["DAG de prueba con nodos agent: ejecuta y pasa gates", "agent_invalido es rechazado", "AGENT_GRAPH.json existe y valida"]
    evidence: [tests, AGENT_GRAPH.json, ejecucion]
    work_surface: BACKEND



  - - id: T-05  
    titulo: "Backend: endpoints de organizacion (solo lectura, alimentan UI)"  
    needs: [T-04]  
    pasos:  
      1: "En router inteligente universal/integration/chat_mvp/router.py agregar GET  
          /chat/org/graph (sirve chat router/03-ESTADO/AGENT_GRAPH.json),  
          GET /chat/org/queue (lee chat router/EVIDENCIA/cola/tareas.json y  
          workers.json de chat router/runtime/cola.py),  
          GET /chat/org/bitacora (tail N lineas de 03-ESTADO/BITACORA.jsonl),  
          GET /chat/org/dag/{id} (ledger completo de un run ejecutado)"  
      2: "GET /chat/org/connectors (fichas del bus enchufe: id, status, health,  
          puertos — spec §10.10-10.14), GET /chat/org/templates (DAG LOCKED  
          §10.3-10.7, solo seleccion+ejecucion), GET /chat/org/engineering  
          (toggles §10.9), GET /chat/org/files (adjuntos HF /memoria/* +  
          anclas archivo→nodo DAG, registro MCP por proyecto)"  
      3: "Todo endpoint es solo lectura y emite evento por State Hub; ninguna  
          mutacion de estado sin Sheriff; errores devuelven JSON  
          {status, detail} determinista, nunca texto libre"  
    acceptance:  
      - "cada endpoint responde 200 con datos reales o lista vacia"  
      - "ningun endpoint muta estado (test de no-escritura)"  
      - "respuestas validan contra schema fijo (contrato Event doc24)"  
    evidence: [tests, respuestas_json]  
    work_surface: BACKEND  
  
  - id: T-06  
    titulo: "Frontend: shell + 4 paneles modulares + sub-vistas spec (archivos separados, NO monolito)"  
    needs: [T-05]  
    pasos:  
      1: "chat router/ui/shell.{html,css,js}: sidebar + topbar segun spec  
          §15-16; tema V07 grises #1B1B1B/#202020/#2A2A2A/#3C3C3C/#484848,  
          acento #0848F7 solo en elemento activo; monta los paneles como  
          fichas del bus enchufe (T-03); router de vistas interno; un unico  
          cliente api.js que apunta a endpoints T-05 (NUNCA proveedores  
          directos, NUNCA llave en el navegador)"  
      2: "panel-chat.{js,html}: composer con modos Rapido/Pensar/Equilibrado,  
          boton adjuntar, comandos slash, selector de rama (spec §9.1-9.3);  
          fusionar funciones existentes de router inteligente universal/  
          vercel-ui/index.html (selectores modelo/agente/GitHub/grupo,  
          switch con-agente, botones pausa/reanudar/emergencia/encender  
          router, orden programada); envia ordenes a /chat/* del Router"  
      3: "panel-archivos.{js,html}: vista AUDITOR de Run UI YAIWES.html  
          (buscar/anclar/enviar a agente); adjuntos → HF /memoria/* via  
          /chat/org/files; cada ancla crea arista archivo→nodo en  
          AGENT_GRAPH.json; registro MCP de archivos por proyecto"  
      4: "panel-seguimiento.{js,html}: TREN (vagones = nodos del DAG en  
          ejecucion con estado vivo) + VENTANAS (IN/OUT por paso +  
          breakpoints) + ORQUESTA (pila de funciones, salida JSON) de  
          Run UI YAIWES.html; mapa mental 10 vistas renderizado desde  
          STATE.json/CRAZY_WALL.json (Vision Global, Arquitectura, Posicion  
          Actual, Rompecabezas, Proposito, Entrada/Salida, Desbloquea,  
          Madurez, Microflujo P1, Ensamblaje); estados de evidencia  
          CREATED→TESTED→VERIFIED→READY→MERGED→BLOCKED (spec §11)"  
      5: "panel-canvas.{js,html}: visor de imagenes/video/animacion con  
          componentes RUI ya descargados (grid-reveal, fluid-orb,  
          matrix-orb, step-player); fuente = adjuntos de panel-archivos"  
      6: "sub-vistas del spec como modulos propios: conectores  
          §10.10-10.14, templates LOCKED §10.3-10.7, run §10.8 (REGLA: solo  
          seleccion+ejecucion, nunca editar DAG en runtime, SENTINEL  
          bloquea), engineering §10.9, automatizaciones §7.11, habilidades  
          §7.5. Datos solo de T-05; cero decision LLM en frontend; toda  
          logica de estado en JS determinista"  
    acceptance:  
      - "shell monta los 4 paneles + sub-vistas sin errores de consola"  
      - "cada panel consume su endpoint T-05 correspondiente"  
      - "ningun archivo supera 500 LOC (R02); sin dependencias nuevas sin RDC"  
      - "tema V07 verificado por read-back de colores en CSS"  
    evidence: [screenshots, read-back_css, tests_endpoints]  
    work_surface: FRONTEND


Handoff completo: YAML plan + ejecución T-01..T-10
Repositorio: maxbry123-commits/router-universal-router-inteligente- (ref: main). Recuperar el YAML completo de la conversación de planificación: escribir chat router/01-PLAN/PLAN-DSL-DAG-UI.yaml con input_blocks_verbatim (IB-01..IB-17 con las órdenes literales del Director) + nodos T-01..T-10, donde T-05 y T-06 usan EXACTAMENTE el texto del parche de arriba (eran las secciones truncadas). Luego ejecutar T-01..T-10 en loop sin preguntar: T-01 mover archivos sueltos de raíz a 📂 Skills Maxbry UI fromtend/ (componentes/, diseno/) incluyendo ESPECIFICACION_VISUAL_PANEL_YAIWES_FROMTED.md; T-03 enchufe Fables→Router; T-04 nodo agent:+gates P1/P2/P3+AGENT_GRAPH.json; T-05/T-06 como el parche; T-07 solo RDC; T-08 trazabilidad por nodo

ESPECIFICACION_VISUAL_PANEL_YAIWES_FROMTED.md; T-03 enchufe Fables→Router; T-04 nodo agent:+gates P1/P2/P3+AGENT_GRAPH.json; T-05/T-06 como el parche; T-07 solo RDC; T-08 trazabilidad por nodo (BITACORA+STATE+CRAZY_WALL+HANDOFF+Devin notas+Claude notas); T-09 verificación vs spec sección por sección; T-10 cierre read-back, Vercel APAGADO. Reglas: reuse>patch>adapt>generate, max 500 LOC/bloque, evidencia+read-back, Judge/Sheriff en código, secrets solo como secrets (registrar rotación de los 4 tokens filtrados).


