# INPUT BLOCK VERBATIM — PARTE 2-A (documentos del 25-sep, literal)
Contiene: guía del Director de conexión y activación de agentes (M2), documento DeepSeek Harness (M7), plantilla Mapa Mental v3.0 (M7), documentos 2, 3, 4 y mensaje M10 completo.
Claves → [CLAVE OMITIDA].

---

## M2 — GUÍA COMPLETA DEL DIRECTOR (literal)

# ROUTER INTELIGENTE UNIVERSAL — CONEXIÓN Y ACTIVACIÓN DE AGENTES

Repo: https://github.com/maxbry123-commits/router-universal-router-inteligente-  (rama main)

## 1. ENLACE DEL ROUTER Y CÓMO CONECTAR UN AGENTE

La URL del Router NO es fija: cambia si el Job se relanza. Siempre se lee aquí:
https://raw.githubusercontent.com/maxbry123-commits/router-universal-router-inteligente-/main/router%20inteligente%20universal/agents-yaiwes/ROUTER_JOB_PAUSE.flag
(línea LIVE_URL=...). Hoy: https://6ab3e2ad51992417dfcd7c95--8000.hf.jobs

Toda llamada lleva el token de Hugging Face en el header:
  Authorization: Bearer <HF_TOKEN>

Rutas:
- GET  <LIVE_URL>/health        → comprobar que está vivo
- POST <LIVE_URL>/chat/route    → pedir una respuesta al Router
- POST <LIVE_URL>/chat/jev      → decisión tipo Jev (choice / score / noul)

Ejemplo:
curl -H "Authorization: Bearer $HF_TOKEN" "$LIVE_URL/health"

Para que un agente quede registrado como conectado: al terminar, hace GET /health y guarda
"router_connected": true/false en su crazy_wall.state.json (los agentes del repo ya lo hacen solos con common/boot.py).

Pausa remota: poner PAUSED=true en ROUTER_JOB_PAUSE.flag y hacer push. PAUSED=false lo reanuda.
Modelo en uso: solo DeepSeek V4 Flash (agents-yaiwes/ROUTE.json). No cambiar sin autorización del Director.

## 2. COMANDO PARA ACTIVAR UN AGENTE (push → Webhook → cómputo en HF)

Crear o editar el chain.yaml del agente y hacer push a main. Eso solo lo activa.
Regla: un solo agente por push.

git clone https://github.com/maxbry123-commits/router-universal-router-inteligente-.git
cd router-universal-router-inteligente-
mkdir -p "router inteligente universal/agents-yaiwes/agent-30-mi-tarea"
# escribir ahí el chain.yaml (plantilla abajo)
git add "router inteligente universal/agents-yaiwes/agent-30-mi-tarea/chain.yaml"
git commit -m "agente 30: nueva tarea"
git push origin main

Plantilla mínima de chain.yaml:

schema: yaiwes.chain/v1
input_block: |
  <instrucción literal del Director>
agent:
  id: agent-30-mi-tarea
  framework: pocketflow        # o smolagents
  group: chat
  route: [deepseek_flash]
  fallback: []
  max_tokens: 2000
context:
  text: |
    <datos que el agente necesita>
steps:
  - id: paso_1
    task: |
      <qué debe entregar, exacto, de principio a fin>
    checks:
      - kind: min_chars
        value: 200
      - kind: no_secrets
edges: []

Dónde responde el agente:
- agents-yaiwes/agent-30-mi-tarea/crazy_wall.state.json   (CLOSED o BLOCKED, modelo usado, router_connected)
- agents-yaiwes/agent-30-mi-tarea/steps/paso_1/results/output.txt   (resultado real)

Nunca escribir claves ni tokens en ningún archivo del repo: es público.

Headers obligatorios en cada llamada al Router:
Authorization: Bearer <HF_TOKEN>
X-API-Key: [CLAVE OMITIDA]

Ejemplo:
curl -X POST "$LIVE_URL/chat/send" \
  -H "Authorization: Bearer $HF_TOKEN" \
  -H "X-API-Key: [CLAVE OMITIDA]" \
  -H "Content-Type: application/json" \
  -d '{"message":"hola","provider":"hf","model":"deepseek-ai/DeepSeek-V4-Flash","max_tokens":200}'

La clave también está guardada como secreto de GitHub: RIU_ROUTER_API_KEY.
No escribirla en ningún archivo del repo (es público).

# ACTIVAR UN AGENTE (push → Webhook → cómputo en Hugging Face)

Un push a main con el chain.yaml del agente lo activa solo. Un solo agente por push.

## Comando
git clone https://github.com/maxbry123-commits/router-universal-router-inteligente-.git
cd router-universal-router-inteligente-
mkdir -p "router inteligente universal/agents-yaiwes/agent-30-mi-tarea"
# escribir ahí el chain.yaml (plantilla abajo)
git add "router inteligente universal/agents-yaiwes/agent-30-mi-tarea/chain.yaml"
git commit -m "agente 30: nueva tarea"
git push origin main

## Plantilla chain.yaml
(idéntica a la de arriba)

## Dónde responde el agente
- agents-yaiwes/agent-30-mi-tarea/crazy_wall.state.json            → CLOSED o BLOCKED, modelo usado, router_connected
- agents-yaiwes/agent-30-mi-tarea/steps/paso_1/results/output.txt  → resultado real.

---

## M7 — DOCUMENTO "DEEPSEEK HARNESS COMO CEREBRO CENTRAL DEL CHAT YAIWES" (literal)

# 🧠 DEEPSEEK HARNESS COMO CEREBRO CENTRAL DEL CHAT YAIWES

## COMPONENTE PRINCIPAL

**DeepSeek Harness (`dsh`)**

Repositorio oficial:
DeepSeek AI → `deepseek-ai/deepseek-harness`

Licencia:
MIT

Estado:
Developer Preview.

Función:
Convertir el Chat YAIWES de:

CHAT → ROUTER → MODELO

a:

CHAT
↓
DEEPSEEK HARNESS
↓
CORDIS KERNEL
↓
PLUGINS
↓
MODELOS / AGENTES / MEMORIA / TOOLS / SKILLS / SANDBOX / SCHEDULER
↓
VERIFICACIÓN
↓
RESPUESTA

# 1. QUÉ SERÍA EL "CEREBRO"

DeepSeek Harness NO debe entenderse como otra LLM.

La LLM sigue razonando.

DeepSeek Harness se convierte en el **cerebro operativo / Control Plane** que decide cómo trabajar alrededor de la LLM.

La separación sería:

LLM
= razonamiento

DeepSeek Harness
= sistema operativo del agente

Cordis Kernel
= núcleo del sistema

Router YAIWES
= selección de modelos/proveedores

Sheriff
= verificación

Memory
= conocimiento persistente

Tools / Skills
= capacidades

Scheduler / Loops
= continuidad y ejecución

# 2. NÚCLEO: CORDIS

DeepSeek Harness está construido sobre **Cordis**.

Cordis administra:

- montaje de plugins;
- desmontaje;
- dependencias;
- servicios;
- eventos;
- ciclo de vida.

El kernel NO necesita contener directamente todas las funciones.

Las capacidades viven como plugins.

MICROFLUJO:

INPUT
→ CORDIS
→ descubrir servicios/plugins necesarios
→ montar capacidades
→ ejecutar agente
→ recibir eventos/resultados
→ desmontar/liberar cuando corresponda
→ OUTPUT

# 3. DEEPSEEK HARNESS COMO CENTRO DE YAIWES

Arquitectura propuesta:

                         ┌───────────────────┐
                         │    CHAT YAIWES    │
                         │ Open WebUI / UI   │
                         └─────────┬─────────┘
                                   ↓
                         ┌───────────────────┐
                         │ API / CHAT BRIDGE │
                         └─────────┬─────────┘
                                   ↓
                    ┌──────────────────────────┐
                    │     DEEPSEEK HARNESS     │
                    │      CONTROL PLANE       │
                    └────────────┬─────────────┘
                                 ↓
                    ┌──────────────────────────┐
                    │      CORDIS KERNEL       │
                    └────────────┬─────────────┘
                                 │
          ┌──────────────────────┼──────────────────────┐
          │                      │                      │
          ↓                      ↓                      ↓
       MODELOS                 AGENTES                TOOLS
          │                      │                      │
          ├─ Router YAIWES       ├─ Agent 14            ├─ GitHub
          ├─ DeepSeek            ├─ Agent 16            ├─ Web
          ├─ Qwen                ├─ Agent 17            ├─ MCP
          ├─ Gemma               ├─ Agent 18            ├─ Files
          └─ otros               └─ otros               └─ CLI
                                 │
          ┌──────────────────────┼──────────────────────┐
          ↓                      ↓                      ↓
        SKILLS                 MEMORY               SANDBOX
          │                      │                      │
          ├─ ECC                 ├─ PostgreSQL          ├─ local
          ├─ Prompt Master       ├─ Redis               ├─ container
          ├─ Ponytail            ├─ Graphiti            └─ remoto
          ├─ Agent Skills        ├─ FalkorDB
          └─ otros               ├─ AgentDB
                                 └─ Storage Bucket
                                 │
                                 ↓
                         ┌──────────────────┐
                         │ SHERIFF/VERIFIER │
                         └────────┬─────────┘
                                  ↓
                         RESPUESTA VALIDADA

# 4. FLUJO DE UNA PETICIÓN

USUARIO
↓
Open WebUI
↓
DeepSeek Harness
↓
Cordis recibe evento
↓
SESSION PLUGIN identifica conversación
↓
MEMORY PLUGIN recupera contexto
↓
ROUTER YAIWES decide modelo
↓
SKILL ROUTER decide skills
↓
TOOL ROUTER decide tools
↓
AGENT LOOP ejecuta
↓
SANDBOX ejecuta acciones cuando sea necesario
↓
SHERIFF valida
↓
¿PASS?
├─ NO → corrección / retry / otro agente
└─ SÍ
    ↓
MEMORY WRITE
↓
SESSION WRITE
↓
RESPUESTA AL CHAT

# 5. EL ROUTER YAIWES NO DESAPARECE

No recomiendo eliminar tu Router YAIWES.

Se conecta COMO servicio/plugin del Harness.

DEEPSEEK HARNESS
↓
MODEL ROUTER PLUGIN
↓
ROUTER YAIWES
↓
┬ DeepSeek
├ Qwen
├ Gemma
├ modelos locales
├ APIs externas
└ Council

De esta forma:

DeepSeek Harness decide **qué capacidad necesita**.

Router YAIWES decide **qué modelo/proveedor debe ejecutarla**.

# 6. MEMORIA COMO PLUGINS

DeepSeek Harness permite convertir la memoria en servicios enchufables.

MEMORY SERVICE
↓
┬ CHAT MEMORY
├ PROJECT MEMORY
├ GLOBAL MEMORY
├ AGENT MEMORY
└ EPISODIC MEMORY

Backend:

CHAT / PROJECT STATE
→ PostgreSQL

CACHE / SESSION / LOCK
→ Redis

RELACIONES / TIEMPO
→ Graphiti + FalkorDB

EXPERIENCIAS DEL AGENTE
→ AgentDB / MemRL

ARCHIVOS GRANDES
→ HF Storage Bucket

SECRETOS
→ Secret Bank / credential_ref

# 7. AUTOEVOLUCIÓN

No pondría todos los frameworks dentro del camino crítico de cada mensaje.

Los usaría como una capa exterior:

                    ┌─────────────────────────┐
                    │   EVOLUTION CONTROLLER  │
                    └────────────┬────────────┘
                                 ↓
                         DEEPSEEK HARNESS
                                 ↓
                            EJECUCIONES
                                 ↓
                       TRACES + RESULTADOS
                                 ↓
                    EVOLUTION / OPTIMIZATION

## Continual Harness
Función: **Reset-free self-improvement.**
Puede modificar durante la operación: prompt; subagentes; skills; memoria; estado del harness.
USO YAIWES: RUN → error/éxito → Continual Harness → actualizar contexto/harness → siguiente RUN
Repositorio: `sethkarten/continual-harness`

## Meta-Harness
Función: Optimizar automáticamente el código alrededor del modelo.
El framework oficial de Stanford busca mejores harnesses para decidir: qué almacenar; qué recuperar; qué mostrar; cómo ejecutar.
Repositorio oficial: `stanford-iris-lab/meta-harness`
Existe además una implementación experimental con: Postgres checkpoints; cross-run memory; branching; rewind; fork; replay; time-travel; dashboard visual.
Repositorio: `ManagementMO/Meta-Harness`
USO: TRACE → detectar problema → generar variante de Harness → benchmark → comparar → conservar mejor variante

## MemRL
Función: **Runtime Reinforcement Learning usando memoria episódica.**
No necesita cambiar los pesos de la LLM.
Usa: Two-Phase Retrieval + feedback del entorno + utility de memoria
USO: episodios → recuperación semántica → filtro de utilidad → estrategia más útil → ejecutar → reward → actualizar utilidad
Repositorio: `MemTensor/MemRL`

## Life-Harness
Función: Mejorar el runtime alrededor de un modelo congelado.
NO modifica pesos.
Puede adaptar: realización de acciones; contratos del entorno; regulación de trayectoria; skills procedurales.
USO: FAIL recurrente → analizar fallo → crear intervención del harness → siguiente ejecución → verificar
Repositorio: `Tianshi-Xu/Life-Harness`

## MOSS
Función: **Source-level self-rewriting.**
A diferencia de optimizar solamente: prompts; skills; memoria; workflows;
MOSS puede modificar el propio código del harness: routing; hooks; invariantes; dispatch; state management.
FLUJO: fallos reales → agrupar evidencia → coding agent propone patch → crear candidato → replay en entorno aislado → pruebas → health check → aprobación → promoción → rollback si falla
IMPORTANTE: No dejaría MOSS modificar producción directamente.
YAIWES debería obligar: PATCH → TEST → SHERIFF → SANDBOX → DIFF → APROBACIÓN → PROMOTE
El paper es: `MOSS: Self-Evolution through Source-Level Rewriting in Autonomous Agent Systems`
No asumir un repositorio oficial público hasta verificar uno publicado por los autores.

## Bayesian-Agent
Función: Tratar cada Skill/SOP como una **hipótesis bayesiana**.
En lugar de: "este skill funcionó una vez, úsalo"
hace: SKILL → evidencia positiva/negativa → posterior bayesiano → fiabilidad contextual → PATCH / SPLIT / COMPRESS / RETIRE / EXPLORE
USO YAIWES: Skill Registry → Bayesian-Agent → score de confianza → DeepSeek Harness carga skills apropiados
Repositorio: `DataArcTech/Bayesian-Agent`

## MetaClaw
Función: Autoaprendizaje desde conversaciones reales.
Puede: extraer nuevos skills; memoria cross-session; resumir experiencia; realizar RL opcional; diferir entrenamiento a períodos ociosos.
USO: CHAT → experiencia → skill extraction → memory → evaluación → actualización
Repositorio oficial: `aiming-lab/MetaClaw`

## SCOPE
Función: Evolución automática del contexto/prompt.
Tiene dos memorias: TACTICAL = aprendizaje para la tarea actual; STRATEGIC = aprendizaje reutilizable entre tareas
FLUJO: TRACE → detectar error/mejora → generar guidelines → seleccionar mejores → Tactical / Strategic Memory → optimizar memoria → nuevo prompt
Repositorio: `JarvisPei/SCOPE`

## ZERA
Función: Optimización de prompts partiendo prácticamente desde cero.
Optimiza conjuntamente: system prompt; user prompt.
FLUJO: prompt inicial → ejecutar ejemplos → evaluación → crítica por principios → refinamiento → repetir → prompt optimizado
Repositorio: `younatics/zera-agent`

# 8. ORGANIZACIÓN QUE USARÍA

No: CHAT → 9 sistemas de evolución → LLM. Eso añadiría latencia y complejidad.

## CAMINO RÁPIDO
CHAT → DeepSeek Harness → Memory Retrieval → Router → LLM/Agent → Sheriff → OUTPUT

## CAMINO DE APRENDIZAJE ASÍNCRONO
TRACES ↓ ┬ MemRL ├ Bayesian-Agent ├ SCOPE ├ MetaClaw └ Continual Harness ↓ EVIDENCE PACKET ↓ EVALUATOR ↓ MEJORA VERIFICADA ↓ PLUGIN / SKILL / MEMORY / PROMPT actualizado

## CAMINO DE EVOLUCIÓN PROFUNDA
FAIL ESTRUCTURAL RECURRENTE ↓ Meta-Harness / Life-Harness ↓ si el problema está en código ↓ MOSS ↓ SANDBOX ↓ TEST ↓ SHERIFF ↓ APROBACIÓN ↓ PROMOTE / ROLLBACK

# 9. CEREBRO FINAL DEL CHAT

                    CHAT YAIWES
                         │
                         ▼
               ┌────────────────────┐
               │ DEEPSEEK HARNESS   │
               │   CONTROL PLANE    │
               └─────────┬──────────┘
                         │
                         ▼
                  CORDIS KERNEL
                         │
       ┌─────────────────┼─────────────────┐
       │                 │                 │
       ▼                 ▼                 ▼
    ROUTER             MEMORY            SKILLS
       │                 │                 │
       ▼                 ▼                 ▼
    MODELOS            STORES           TOOLS
       │                 │                 │
       └─────────┬───────┴────────┬────────┘
                 ▼                ▼
             AGENT LOOP        SANDBOX
                 │
                 ▼
              SHERIFF
                 │
                 ▼
             RESPUESTA
                 │
                 ▼
              TRACES
                 │
                 ▼
          EVOLUTION LAYER
                 │
     ┌───────────┼────────────────────────┐
     ▼           ▼          ▼             ▼
   MemRL      SCOPE     Bayesian      MetaClaw
     │           │          │             │
     └───────────┼──────────┴─────────────┘
                 ▼
          Continual Harness
                 │
                 ▼
         Meta/Life Harness
                 │
         fallo estructural
                 ▼
               MOSS
                 │
                 ▼
          TEST + SHERIFF
                 │
                 ▼
         NUEVA CONFIGURACIÓN

# 10. IDEA CENTRAL

**DeepSeek Harness = cerebro operativo.** **Cordis = kernel.** **Router YAIWES = decisión de modelo/proveedor.** **LLM = razonamiento.** **Memory = conocimiento persistente.** **Skills/Tools = capacidades.** **Sheriff = control de calidad.** **MemRL/Bayesian/SCOPE/MetaClaw = aprendizaje continuo.** **Continual/Meta/Life Harness = evolución del harness.** **MOSS = última capa para cambios estructurales en código.**

Así no sustituyes todo YAIWES. Usas DeepSeek Harness como el centro donde se conectan y coordinan las piezas que ya tienes.

---

## M7 — PLANTILLA "NCT/APEX — Mapa Mental v3.0" (literal)
(texto íntegro registrado en `INPUT-BLOCK-VERBATIM-CHAT-Y-PANEL-PARTE-2` previa del chat; se transcribe aquí)

══════════════════════════════════════
🧩 NCT/APEX — Mapa Mental v3.0
══════════════════════════════════════
🌐 VISIÓN GLOBAL: DEFINIR MÉTODO ↓ DISEÑAR SISTEMA ↓ CONSTRUIR PIEZAS ↓ INTEGRAR TODO ↓ AUDITAR Y CERRAR → Para qué: ver el proyecto completo en 5 segundos → Sin esto: el modelo no sabe dónde termina el trabajo
🏗 ARQUITECTURA GLOBAL: Método → LEGO → APEX → Modos → Docs → Sistema Final → Para qué: entender cómo se conectan los 5 grupos → Sin esto: cada pieza parece independiente, no un sistema
📍 POSICIÓN ACTUAL: G1 Método ├─ P1 ← ACTUAL ├─ P2 └─ P3 → Para qué: saber exactamente dónde estamos → Sin esto: el modelo puede retrabalar algo ya aprobado
🔗 ROMPECABEZAS (dependencias cruzadas): P1 → P2 → P3 ↓ G2 → G3 → G4 → G5 ↓ Sistema Final → Para qué: ver qué bloquea qué → Sin esto: se construye en el orden equivocado
🎯 PROPÓSITO: P1: Que el modelo no improvise → Para qué: base de todo lo demás → Sin esto: nada del sistema funciona
📥 ENTRADA / SALIDA: P1 entrada: — salida: → P2 · P2 entrada: ← P1 salida: → P3 · P3 entrada: ← P2 salida: → G2 · G2 entrada: ← G1 salida: → G3 → Para qué: contrato exacto entre piezas → Sin esto: cada modelo interpreta las conexiones distinto
🚀 DESBLOQUEA: P1 listo → P2 arranca · P2 listo → P3 arranca · P3 listo → G2 (Sistema LEGO) → Para qué: entender consecuencias de terminar → Sin esto: el modelo no ve el valor de completar cada pieza
📊 MADUREZ: G1 Método ██░░░░░░░░ 20% · G2 LEGO ░░░░░░░░░░ 0% · G3 APEX ░░░░░░░░░░ 0% · G4 Modos ░░░░░░░░░░ 0% · G5 Docs ░░░░░░░░░░ 0% → Para qué: ver progreso real de un vistazo → Sin esto: no se sabe cuánto falta
⚙️ MICROFLUJO — P1: Define objetivo → Carga mínimo → Sigue orden → Verifica checklist → Muestra estado → Para si falla → Para qué: entender qué ocurre dentro de la pieza activa → Sin esto: el modelo improvisa el proceso interno
🧩 ENSAMBLAJE FINAL: G1 Método (cómo trabaja el modelo) ↓ G2 LEGO (cómo se construyen proyectos) ↓ G3 APEX (estructura obligatoria) ↓ G4 Modos (interfaz de trabajo) ↓ G5 Documentos (versión entregable) ↓ SISTEMA FINAL — se reconstruye y audita solo → Para qué: ver cómo todas las piezas forman un solo sistema → Sin esto: el modelo ve partes sueltas, no el resultado final
PROJECT DASHBOARD: TOTAL APROBADOS: 8 (todos los bloques) · TOTAL PENDIENTES: 0 · TOTAL BLOQUEADOS: 0 · POR RAMA: G1: 100% completo | modos: 2 activos · SIGMA: 1.00 · ACTUAL: G1_terminado | SIGUIENTE: iniciar_G2
LISTA DE BLOQUES ENTREGADOS: 1. P1 (21 ítems) 2. P2 (19 ítems) 3. P3 (20 ítems) 4. Mapa mental (10 vistas) 5. Lista de validación de última tarea 6. Modos de trabajo (2 modos) 7. State JSON de recuperación completo 8. Dashboard y cierre. TOTAL: 8 bloques copiables, todos completos.
FRONTERA ACTIVA: ACTUAL: sistema_operativo_listo · READY: [usar /arquitecto, usar /ejecutor, comenzar G2] · BLOCKED: []
MINI_STATE: { "modo":"final", "actual":"G1_completo_100%", "sigma":1.00, "aprobados":8, "pendientes":0 }
MODO DE TRABAJO: /arquitecto → Diseña estructura, tecnologías, módulos, dependencias y planos del proyecto. No genera código de implementación. · /ejecutor → Implementa, escribe código concreto, ejecuta pruebas, genera artefactos. No diseña arquitectura.
Checklist visual con emojis fijos: 🎯 OBJETIVO · 🏗️ TAREA_EN_CURSO · 💡 Planificación de objetivo y tareas antes de continuar · 📌👣 PRÓXIMOS PASOS A SEGUIR POR LA AI · 👣 Paso · 🧩 RESULTADOS QUE DEBO DE GENERAR · 🗂️ FORMATO DE SALIDA · ⚠️ PENDIENTES · 🔒 CERRADO · 📂 PARA_ARCHIVAR · 🚨 INGENIERIA · ⁉️ FALTA_INTEGRAR · ✅ INTEGRADO · 🆕 NUEVO
🎯 OBJETIVO: Auditoría completa de los JSON del método. 🏗️ TAREA_EN_CURSO: Revisar 355 veces y reemitir sin omisiones. 💡 Planificación: Comparar con referencia → Verificar reglas → Emitir. 📌👣 PRÓXIMOS PASOS: 👣 Mostrar plantilla íntegra. 👣 Esperar. ⚠️ PENDIENTES: Revisión del Director. 🔒 CERRADO: Omisiones previas en STATE_JSON y PARCHE_JSON. 🚨 INGENIERIA: Todas las secciones fijas, reglas y metadatos confirmados. ✅ INTEGRADO: Hasta R60, SECCIONES_FIJAS, ESTRUCTURA_NOTAS_DIRECTOR, CHECKLIST_EMOJIS. 🆕 NUEVO: Auditoría 355x.
LISTA DE VALIDACIÓN DE ÚLTIMA TAREA: ✅ P1: 21 ítems (control del modelo) ✅ P2: 19 ítems (anti-amnesia) ✅ P3: 20 ítems (verdad y ensamblaje) ✅ CORE.json v3.3 con elementos adicionales (roles, modos MASTER, fórmula, semáforo, ANCLA) ✅ 9 archivos externos (TASKS, DECISIONES, GRAFO, SEGMENTO_X, DSL, FAB, INVARIANTES, SELF_CHECK, CONTRATOS) ✅ Mapa mental 10 vistas con MAPA.json ✅ 2 modos operativos: /arquitecto y /ejecutor ✅ Verificación cruzada 3 roles ✅ Doble léxico 🗣️⚙️▶️ ✅ JSON state arrastre ✅ VMEF anti-sobreingeniería ✅ Formato de salida estándar (header + footer + JSON copiable) ✅ Kimi K format para documentos

---

## M10 — documentos 2, 3, 4 y mensaje completo
Los documentos 2 (arquitectura 100% bajo demanda), 3 (aceleradores) y 4 (router GitHub para varias cuentas HF) y el mensaje M10 completo se transcribieron literales en la sección "M10 — MENSAJES Y DOCUMENTOS COMPLETOS" de la conversación de Opus del 26-sep y se suben en PARTE-2-B (siguiente checkpoint del nodo V-1).
