# REFERENCIAS ADJUNTAS AL INPUT BLOCK 05 — VERBATIM (2026-09-19/20)

Documentos que el Director adjuntó al mensaje del INPUT BLOCK 05 (`INPUT-BLOCK-05-chat-storage-grupos-VERBATIM.md`). Provienen de otro asistente (ChatGPT) y se guardan textuales como referencia para el Paso 3 ("los 3 métodos de procesamiento"). No son instrucciones ejecutables: el Director dijo que primero va la prioridad del chat.

---DOCUMENTO 1 (verbatim)---

Procesó durante 13s

Sí. Un solo Router puede encadenar los tres procesos. La forma más limpia es que el Router no sea una LLM que “piensa qué hacer”, sino un motor determinista de DAG + FSM que selecciona qué pipeline ejecutar y mantiene el estado.

Tu arquitectura podría quedar así:

INPUT
  ↓
NORMALIZER
  ↓
MODALITY DETECTOR
[TEXTO | CODE | IMAGEN | AUDIO | VIDEO]
  ↓
RESEARCH CONTROLLER
  ↓
SEARCH-1 ─┐
SEARCH-2 ─┤
SEARCH-3 ─┼→ EVIDENCE BUILDER → EVIDENCE_PACKET
SEARCH-4 ─┤
SEARCH-5 ─┘
  ↓
ROUTER POLICY ENGINE
  ↓
┌──────────────────────┬──────────────────────┬──────────────────────┐
│ METHOD-1             │ METHOD-2             │ METHOD-3             │
│ COUNCIL PARALLEL     │ CODE CHAIN           │ JEV-LIKE DECISION    │
│                      │                      │                      │
│ LLM1 ┐               │ LLM01 → LLM02 →     │ Decider-2B-Vision   │
│ LLM2 ├→ consensus    │ ... → LLM11          │       ↓              │
│ ...  │               │       ↓              │ NanoJev              │
│ LLM11┘               │ VERIFY               │       ↓              │
│                      │                      │ probabilities        │
└──────────┬───────────┴──────────┬───────────┴──────────┬───────────┘
           └──────────────────────┼───────────────────────┘
                                  ↓
                         FINAL VERIFIER
                                  ↓
                            OUTPUT API

El kernel del Router

Yo lo programaría alrededor de un único contrato de tarea:

task:
  id: task-uuid
  input:
    raw: "..."
    modality: auto

  research:
    enabled: true
    engines: 5
    mode: parallel_once

  evidence:
    immutable: true

  policy:
    pipeline: auto

  execution:
    timeout_ms: 120000
    retry_limit: 2
    fail_closed: true

  output:
    structured: true
    audit: true

La pieza fundamental es pipeline. El Router decide entre:

pipeline = council_parallel
pipeline = code_chain
pipeline = decision_fastpath

No necesitas tres routers.


---

METHOD 1 — Council paralelo

Aquí la investigación ocurre una sola vez. Eso es importante porque evita que 11 modelos gasten búsqueda y tokens buscando lo mismo.

INPUT
 ↓
Research Manager
 ↓
3-5 search engines
 ↓
Deduplicate
 ↓
Evidence Packet
 ↓
┌──────┬──────┬──────┬──────┬──────┐
LLM1  LLM2   LLM3   ...    LLM11
└──────┴──────┴──────┴──────┴──────┘
 ↓
Council Aggregator
 ↓
Consensus Engine
 ↓
Verifier
 ↓
OUTPUT

Cada modelo recibe exactamente:

{
  "task": "...",
  "evidence_packet": "...",
  "role": "...",
  "required_output_schema": {
    "answer": "string",
    "claims": [],
    "confidence": 0.0,
    "gaps": []
  }
}

Y el agregador no debería simplemente contar votos. Conviene calcular algo tipo:

FINAL_SCORE =
  evidence_support   × 0.35
+ agreement          × 0.20
+ verifier_score     × 0.25
+ confidence_quality × 0.10
+ independence       × 0.10

Así evitas:

7 modelos dijeron lo mismo
=
automáticamente correcto

porque siete modelos pueden repetir el mismo error.


---

METHOD 2 — cadena CODE

Aquí sí usaría una FSM secuencial, porque la salida de una etapa es entrada de la siguiente.

EVIDENCE_PACKET
      ↓
LLM-01 FACTS
      ↓
FACTS.json
      ↓
LLM-02 INTERPRETATION
      ↓
INTERPRETATION.json
      ↓
LLM-03 CONSTRAINTS
      ↓
LLM-04 SOLUTION_A
      ↓
LLM-05 SOLUTION_B
      ↓
LLM-06 REFUTATION
      ↓
LLM-07 GAPS
      ↓
LLM-08 PLAN
      ↓
LLM-09 ARCHITECTURE
      ↓
LLM-10 VERIFY
      ↓
LLM-11 INDEPENDENT_ALTERNATIVE
      ↓
FINAL CODE DECISION

Pero hay una mejora importante: no pases todo lo anterior como texto libre.

Cada nodo produce un artefacto estructurado:

01_facts.json
02_interpretation.json
03_constraints.json
04_solution_a.json
05_solution_b.json
06_refutation.json
07_gaps.json
08_plan.json
09_architecture.json
10_verification.json
11_independent.json

Por ejemplo:

{
  "node": "LLM-07",
  "role": "gap_detector",
  "input_refs": [
    "03_constraints.json",
    "04_solution_a.json",
    "05_solution_b.json",
    "06_refutation.json"
  ],
  "result": {
    "gaps": [],
    "severity": {},
    "blocking": false
  }
}

Así tu Router controla exactamente qué información puede leer cada etapa.

Para CODE yo añadiría además:

LLM solution
     ↓
STATIC CHECK
     ↓
BUILD
     ↓
TEST
     ↓
FAIL?
 ┌───┴───┐
NO      YES
↓         ↓
PASS    repair-loop
          ↓
       KAT-Coder

Eso encaja muy bien con tu idea anterior de Qwen3.5-9B como CODE local y KAT-Coder como reparación/escalamiento.


---

METHOD 3 — JEV-LIKE

Aquí la arquitectura cambia completamente porque no quieres texto generado. Quieres:

estado
+
candidatos
       ↓
modelo
       ↓
scores/logits
       ↓
probabilidades
       ↓
decisión

Y esto sí tiene una base técnica bastante cercana a lo que describes.

Mapika/decider-2b-vision existe actualmente: está basado en Qwen3.5-2B, tiene unos 2B parámetros, licencia Apache-2.0 y está diseñado para producir probabilidades calibradas sobre opciones en una sola pasada en vez de funcionar como chat tradicional. 

NanoJev también existe como proyecto independiente; usa una base Qwen3-0.6B con heads de decisión, acepta candidatos dinámicos y devuelve distribuciones de probabilidad sin decodificación normal de tokens. No es la implementación oficial de Jev, sino una réplica/investigación independiente. 

Jev, por su parte, describe públicamente justamente el patrón estado no estructurado → decisión probabilística tipada, en vez de generación conversacional. 

Yo convertiría tu METHOD-3 en:

INPUT
 ↓
NORMALIZER
 ↓
RESEARCH ONCE
 ↓
CONTEXT PACKET
 ↓
MODALITY DETECTOR
 ↓
TASK CLASSIFIER
 ↓
CANDIDATE GENERATOR
 ↓
DECIDER-2B-VISION
 ↓
HIGH-LEVEL PROBABILITIES
 ↓
NanoJev
 ↓
MICRO DECISIONS
 ↓
POLICY ENGINE
 ↓
CONFIDENCE GATE
 ↓
DECISION
 ↓
API

La diferencia importante es que Decider y NanoJev no deberían ejecutar herramientas directamente.

Deben producir algo así:

{
  "decision": "CODE_PIPELINE",
  "probabilities": {
    "COUNCIL": 0.04,
    "CODE_PIPELINE": 0.91,
    "DIRECT": 0.03,
    "RESEARCH_MORE": 0.02
  },
  "confidence": 0.91
}

Y entonces el Router determinista ejecuta:

if decision == "CODE_PIPELINE":
    run("method_2")

Nunca:

Decider
 ↓
ejecutar shell directamente

Eso te permite mantener la separación:

AI = decidir

ROUTER = autorizar

EXECUTOR = ejecutar


---

La pieza que une los tres métodos

Yo crearía un PolicyEngine.

Conceptualmente:

def select_pipeline(task, decision):

    if task.modality == "code":
        return "code_chain"

    if decision.confidence < 0.65:
        return "council_parallel"

    if task.complexity == "high":
        return "council_parallel"

    return "decision_fastpath"

Pero la regla real debe vivir en configuración, no hardcodeada:

routing_policy:

  CODE:
    primary: code_chain
    fallback: council_parallel

  ARCHITECTURE:
    primary: council_parallel
    fallback: decision_fastpath

  SIMPLE_DECISION:
    primary: decision_fastpath
    fallback: council_parallel

  IMAGE_DECISION:
    primary: decider_2b_vision
    fallback: council_parallel

  LOW_CONFIDENCE:
    threshold: 0.65
    action: council_parallel

Entonces puedes cambiar el sistema sin tocar código.


---

Tu capa JEV externa

La estructura que propones yo la modificaría ligeramente:

ENTRADA
 ↓
SYSTEM-ONE WRAPPER
 ↓
MODEL ADAPTER
 ↓
OPEN MODEL
 ↓
HIDDEN STATE / LOGITS
 ↓
DECISION HEAD
 ↓
SOFTMAX / SIGMOID
 ↓
PROBABILITIES
 ↓
JEV-LIKE POLICY ENGINE
 ↓
SKILLS / RULES
 ↓
CONFIDENCE GATE
 ↓
DECISION
 ↓
ROUTER
 ↓
API / EXECUTOR

Eso es mejor que:

modelo → software JEV → ejecutar

porque mantiene una frontera de seguridad y control.

El DecisionHead puede soportar tres interfaces, igual que NanoJev:

CHOICE
A | B | C | D
→ [0.05, 0.10, 0.78, 0.07]

BOOLEAN
true | false
→ [0.93, 0.07]

SCORE
0 | 1 | 2 | 3 | 4
→ [0.01, 0.04, 0.15, 0.60, 0.20]

NanoJev documenta precisamente decisiones Choice, Boolean y Ordered Score, con distribuciones completas sobre candidatos. 


---

Arquitectura de software que programaría

Una estructura limpia sería:

router/
│
├── kernel/
│   ├── dag_engine.py
│   ├── fsm.py
│   ├── scheduler.py
│   └── state_store.py
│
├── ingress/
│   ├── normalizer.py
│   └── modality_detector.py
│
├── research/
│   ├── search_router.py
│   ├── parallel_search.py
│   ├── deduplicator.py
│   └── evidence_builder.py
│
├── policy/
│   ├── task_classifier.py
│   ├── pipeline_selector.py
│   ├── confidence_gate.py
│   └── policies.yaml
│
├── pipelines/
│   ├── council/
│   │   ├── fanout.py
│   │   ├── consensus.py
│   │   └── score.py
│   │
│   ├── code/
│   │   ├── chain.py
│   │   ├── verifier.py
│   │   └── repair.py
│   │
│   └── decision/
│       ├── decider_adapter.py
│       ├── nanojev_adapter.py
│       ├── candidate_builder.py
│       └── probability_engine.py
│
├── models/
│   ├── registry.yaml
│   ├── litellm_adapter.py
│   ├── hf_adapter.py
│   └── local_adapter.py
│
└── api/
    ├── routes.py
    └── schemas.py

Y el flujo transversal completo queda:

INPUT → NORMALIZE → RESEARCH×5 → EVIDENCE_PACKET → CLASSIFY → POLICY_ENGINE → [COUNCIL×11 || CODE-CHAIN×11 || JEV-LIKE] → CONFIDENCE/VERIFY → EXECUTOR → OUTPUT

La idea clave es que METHOD 1, METHOD 2 y METHOD 3 no compiten. Son tres niveles distintos:

METHOD 3
= decisiones rápidas / routing / microdecisiones

METHOD 1
= deliberación paralela / consenso / problemas ambiguos

METHOD 2
= ingeniería CODE / producción secuencial verificable

Y ahí el Router Universal se convierte realmente en el control plane de los tres.

---FIN DOCUMENTO 1---

---DOCUMENTO 2 (verbatim)---

La ubicación exacta dentro de Hugging Face que quedó comprobada es distinta de GitHub:

Cuando un Job descarga pesos, estos viven temporalmente en el filesystem/cache del contenedor, normalmente:

~/.cache/huggingface/hub/models--<autor>--<modelo>/

Almacenamiento persistente HF: revisamos dos Storage Buckets: COMAND-CENTER-1/claude-github-mcp-backup-storage COMAND-CENTER-1/yaiwes-v54

yaiwes-v54 conserva el manifiesto de la biblioteca remota (HF-V5.4-REMOTE-LIBRARY), no los pesos: persistent_external_weights=false y weights_copy_count=0.

Por tanto: HF Jobs → cache temporal de cada Job es donde estuvieron físicamente los modelos descargados; COMAND-CENTER-1/yaiwes-v54 conserva información persistente de la biblioteca remota.

No. Esa dirección:

~/.cache/huggingface/hub/models--<autor>--<modelo>/

es la caché interna temporal del contenedor de un Hugging Face Job. No es una carpeta permanente de tu cuenta que puedas abrir desde la web de Hugging Face. Cuando el Job termina, ese filesystem puede desaparecer.

Para que puedas entrar en Hugging Face y ver permanentemente el inventario de tus modelos remotos, necesitamos guardar el registro en un recurso persistente de tu cuenta, por ejemplo COMAND-CENTER-1/yaiwes-v54.

Confirmado con evidencia directa:
✅ HF Jobs usa caché local tipo ~/.cache/huggingface/hub/models--<autor>--<modelo>/; el filesystem del Job es efímero y se elimina al terminar. �
Hugging Face +1
✅ Monté directamente COMAND-CENTER-1/yaiwes-v54: contiene gates/closure.json y gates/github-actions-rw-xray-1788467151.txt. Job de verificación: 6aad088051992417dfcc6818.
✅ closure.json declara contrato HF-V5.4-REMOTE-LIBRARY, persistent_external_weights=false, weights_copy_count=0 y zero_persistent_external_weights=true.

Trazabilidad de los modelos: está principalmente en Hugging Face Jobs → historial → command/logs. Ahí los Jobs contienen los repo_id utilizados mediante from_pretrained, llama-cli -hf, model_info, etc.
Inventario base confirmado: los 20 HF-M01→HF-M20 que te enumeré están persistidos en GitHub router inteligente universal/integration/huggingface/model_registry.json; HF Jobs proporciona la evidencia de ejecuciones/referencias.


Procesó durante 36s

Sí. Sin mezclarlo con RSI: hay dos formas distintas de copiar la idea de Jev.

Jev no funciona como un chatbot. En vez de escribir una respuesta palabra por palabra, recibe un estado + preguntas + opciones permitidas y devuelve probabilidades directamente. TypeSafe lo describe como un System One Model: decisiones tipadas para que otro software pueda actuar sobre ellas. 

1. Alternativas abiertas donde el propio MODELO es tipo Jev

Proyecto	Qué es	Cómo funciona

NanoJev 0.6B	Modelo Jev-like real, MIT	Qwen3-0.6B + cabezas de decisión. Puede recibir varios estados/preguntas y devolver Choice, booleanos y Score en un forward pass, sin generar tokens de salida. 
Jevlike	Modelo pequeño construido específicamente con la forma de Jev, MIT	texto + N opciones → probabilidad para cada opción. Cada opción atiende al contexto y un softmax produce la distribución final. 
Verdict / OpenJev 151M	Motor de decisión no autoregresivo	Basado en ModernBERT de 151M. Evalúa varias preguntas tipadas en una pasada y devuelve Choice/Score/binario con incertidumbre, en lugar de texto libre. 


Repos:

[NanoJev — GitHub](https://github.com/TianyuCodings/NanoJev?utm_source=chatgpt.com)

[Jevlike — GitHub](https://github.com/vinnylarouge/jevlike?utm_source=chatgpt.com)

[Verdict / OpenJev 151M — GitHub](https://github.com/Heman10x-NGU/Verdict-open-jev?utm_source=chatgpt.com)

El concepto es:

ESTADO → PREGUNTAS → OPCIONES PERMITIDAS → MODELO JEV-LIKE → LOGITS → PROBABILIDADES → DECISIÓN TIPADA

Ejemplo sencillo:

ESTADO:
"El test del programa ha fallado."

PREGUNTA:
"¿Qué hacemos?"

OPCIONES:
A = RETRY
B = DEBUG
C = ABORT

MODELO
→ RETRY  10%
→ DEBUG  84%
→ ABORT   6%

SOFTWARE
→ DEBUG

No necesita generar:

"Creo que lo mejor sería intentar depurar el código..."

Simplemente devuelve una distribución que tu programa puede consumir.


---

2. Alternativas donde Jev es una CAPA EXTERNA

Aquí no necesitas entrenar un modelo Jev especial.

Tomas un modelo abierto normal y colocas delante una capa que transforma su inferencia en decisiones Jev-like.

Capa	Qué aporta

OpenJev	Convierte modelos abiertos como Qwen en un motor de decisiones. Lee directamente los logits de las opciones; no genera JSON ni frases. El código es MIT. 
System One Lite	Servidor HTTP + SDK Python/JS. Puedes enviar texto/JSON y preguntas Choice, Score o Noul; utiliza modelos open-weight Qwen detrás. Código MIT y modelos soportados Apache 2.0. 


Repos:

[OpenJev — GitHub](https://github.com/TheoLeeCJ/openjev?utm_source=chatgpt.com)

[System One Lite — GitHub](https://github.com/snellingio/system-one?utm_source=chatgpt.com)

Aquí el flujo cambia:

TU APLICACIÓN → CAPA SYSTEM-ONE → QWEN / OTRO MODELO → LEER LOGITS → PROBABILIDADES → RESPUESTA TIPADA → TU APLICACIÓN

Por ejemplo, OpenJev usa un modelo normal como Qwen3.5-4B pero evita la generación autoregresiva. En su benchmark con RTX 3090, el mismo modelo produjo 21 decisiones mediante lectura directa de logits en una mediana de ~1.0 s, frente a ~5.3 s cuando tenía que generar un array de texto/JSON. Es una medición concreta de ese proyecto, no una garantía universal. 

Diferencia esencial

LLM NORMAL
ENTRADA → MODELO → GENERA TOKEN → TOKEN → TOKEN → TOKEN → TEXTO/JSON → PARSER → DECISIÓN

JEV-LIKE
ENTRADA → MODELO → LOGITS/PROBABILIDADES → DECISIÓN

CAPA EXTERNA JEV-LIKE
ENTRADA → WRAPPER SYSTEM-ONE → MODELO ABIERTO → LOGITS → DECISIÓN → API

Por eso NanoJev/Jevlike/Verdict son interesantes si quieres que la inteligencia de decisión esté en el propio modelo, mientras que OpenJev/System One Lite son interesantes si quieres instalar una capa reutilizable alrededor de modelos que ya tienes.

Para una arquitectura modular, System One Lite es especialmente claro como capa externa: ya trae servidor, API, cliente Python, cliente TypeScript, evaluaciones y tipos Choice / Score / Noul; no tienes que convertir todo tu agente en otro modelo. 

## 5. Decider-2B-Vision
Modelo base: Qwen3.5-2B Vision
Tamaño: ~2B
Licencia: Apache-2.0
Tipo: System-One multimodal

QUÉ AÑADE:
IMAGEN + ESTADO + PREGUNTA + OPCIONES
→ una sola pasada
→ probabilidades
→ decisión

Puede analizar:
→ capturas de pantalla
→ diagramas
→ interfaces
→ frames
→ texto

Hugging Face:
https://huggingface.co/Mapika/decider-2b-vision

NANOJEV 0.6B

APORTA:
→ Microdecisiones muy frecuentes
→ Decisiones paralelas
→ 2–255 candidatos
→ YES / NO
→ CHOICE
→ SCORE
→ Ranking probabilístico
→ Procesamiento por lotes
→ Servidor persistente

URL PESOS:
https://huggingface.co/C-Tianyu/NanoJev

URL CÓDIGO:
https://github.com/TianyuCodings/NanoJev


                    ┌→ ¿usar herramienta A?
                    ├→ ¿usar herramienta B?
ESTADO → NanoJev ───┼→ ¿aceptar patch?
                    ├→ ¿ejecutar test?
                    └→ ¿llamar LLM grande?

        TODO EN PARALELO
              ↓
       PROBABILIDADES
              ↓
          ROUTER
NanoJev declara precisamente este patrón: varios estados, preguntas y caminos candidatos pueden evaluarse reutilizando una sola pasada del backbone. �
GitHub
Cómo los combinaría con otras LLM
No reemplazaría los modelos grandes. Les daría trabajos diferentes:

USUARIO
→ DECIDER-2B [QUÉ HACER / QUÉ LLM USAR]
→ ROUTER
→ LLM ESPECIALISTA [RAZONAR / PROGRAMAR / INVESTIGAR]
→ NANOJEV [MICRODECISIONES / VALIDAR / RANKING]
→ DECIDER-2B [ACEPTAR / RETRY / CAMBIAR MODELO]
→ RESULTADO

                         ┌→ LLM CODE
                         ├→ LLM REASONING
ENTRADA → DECIDER-2B ────┼→ LLM VISIÓN
                         └→ LLM RÁPIDA
                              ↓
                           RESULTADO
                              ↓
                           NanoJev
                              ↓
                [PASS / FIX / RETRY / ROUTE]

Mi primera opción sería Decider-2B como coordinador general porque ya fue entrenado explícitamente con selección de herramientas, trayectorias de agentes y situaciones→acción, además de tener probabilidades calibradas. �
Hugging Face
NanoJev lo pondría debajo como motor ligero de microdecisiones paralelas, especialmente cuando el agente tenga que tomar decenas o cientos de decisiones estructuradas sin gastar generación de un LLM grande.

USUARIO → ROUTER → DECIDER / NANOJEV → LLM ESPECIALISTA → RESULTADO → ROUTER → SIGUIENTE ACCIÓN
El router es quien conecta y coordina todo. Puede decidir:
qué modelo llamar
en qué orden
cuándo usar Decider-2B
cuándo usar NanoJev
cuándo escalar a una LLM grande
cuándo repetir
cuándo cambiar de modelo
cuándo aceptar una salida
cuándo ejecutar una herramienta
cuándo terminar

Mientras tanto:
ROUTER
→ orquesta

DECIDER-2B
→ toma decisiones de alto nivel

NANOJEV
→ toma muchas microdecisiones rápidas

LLM GRANDE
→ razona / programa / genera

TOOLS
→ ejecutan acciones

TESTS / EVALUADORES
→ devuelven evidencia
El flujo completo sería:
ENTRADA
→ ROUTER
→ DECIDER-2B [QUÉ HACER]
→ ROUTER
→ LLM ESPECIALISTA
→ TOOLS / TESTS
→ NANOJEV [PASS / FAIL / RETRY / SCORE]
→ ROUTER
→ SIGUIENTE MODELO O ACCIÓN
→ RESULTADO

Así que sí: el router sería el centro de control, y Decider/NanoJev serían motores de decisión que el router consulta. El router no necesariamente “piensa”; aplica reglas, estado, prioridades y las decisiones probabilísticas que recibe.

CON ROUTER + DECISION MODELS
TAREA
→ ROUTER
→ MODELO PEQUEÑO DECIDE
→ SOLO SI HACE FALTA → LLM GRANDE
→ RESPUESTA

PREGUNTA SIMPLE
→ NanoJev / Decider
→ decisión en una pasada
→ FIN

PREGUNTA COMPLEJA
→ Decider
→ router selecciona LLM grande
→ LLM procesa
→ resultado

Procesó durante 18s

Sí, puede funcionar, y tu idea tiene sentido si la divides en vía rápida y Ask Council. La mejora importante es que los 11 modelos pequeños no deberían estar activos para cada pregunta: solo se dispara el consejo cuando el router detecta complejidad suficiente.

# ASK COUNCIL — ARQUITECTURA PROPUESTA

ENTRADA
→ NORMALIZAR INPUT
→ DETECTAR [TEXTO | CODE | IMAGEN | AUDIO | VIDEO]
→ ROUTER
→ DECIDER-2B [decisión de alto nivel]
→ NanoJev [microdecisiones / scores / confidence]

──────────────────────────────────────────────────────────────────────

RUTA SIMPLE
→ LLM PEQUEÑO
→ RESPUESTA

Ejemplos:
→ Gemma 3 1B
→ Liquid LFM2.5 1.2B
→ Qwen3 0.6B

──────────────────────────────────────────────────────────────────────

RUTA COMPLEJA — ASK COUNCIL

INPUT
→ INVESTIGACIÓN / CONTEXTO ÚNICO
→ EVIDENCE PACKET
→ SHARD DEL MISMO CONTEXTO
→ 11 LLM / AGENTES EN PARALELO

LLM-01 → hechos
LLM-02 → interpretación
LLM-03 → restricciones
LLM-04 → solución A
LLM-05 → solución B
LLM-06 → refutación
LLM-07 → riesgos/gaps
LLM-08 → planificación
LLM-09 → arquitectura
LLM-10 → verificación
LLM-11 → alternativa independiente

→ NanoJev [score/ranking]
→ Decider-2B [aceptar / combinar / investigar más / escalar]
→ LLM-12 SINTETIZADOR
→ UNA SOLA SALIDA

La parte importante de tu Paso 1 sería hacer la investigación una sola vez y entregar el mismo paquete de evidencia a todos los miembros del consejo. Así no haces 11 búsquedas repetidas y reduces muchísimo coste y latencia.

INPUT
→ RESEARCH ONCE
→ EVIDENCE PACKET
→ ┬→ LLM-1
  ├→ LLM-2
  ├→ LLM-3
  ├→ ...
  └→ LLM-11
→ CONSENSO / SCORE
→ SALIDA

Sobre el 5%: si quieres una ejecución determinista, normalmente usarías temperature=0/greedy. Si quieres aproximadamente un 5% de exploración, ya no sería estrictamente determinista; puede reservarse una rama pequeña para buscar alternativas.

Modelos pequeños

Tu idea de Gemma + Liquid encaja bien. Actualmente están disponibles:

Gemma 3 1B Instruct: pequeño modelo general para respuestas rápidas. 
https://huggingface.co/google/gemma-3-1b-it

Liquid LFM2.5 1.2B Instruct: diseñado para inferencia eficiente/edge y disponible también en ONNX. 
https://huggingface.co/LiquidAI/LFM2.5-1.2B-Instruct

Qwen3 0.6B: muy pequeño y útil para clasificación, routing y tareas cortas. 
https://huggingface.co/Qwen/Qwen3-0.6B

Liquid además tiene tamaños 350M, 700M, 1.2B y 2.6B, y su familia está orientada explícitamente a dispositivos locales/edge. 

Modalidades

También encaja exactamente lo que propones:

┌→ TEXTO → SMALL LLM / ASK COUNCIL
                             ├→ CODE → CODE MODEL
INPUT → MODALITY ROUTER ─────┼→ IMAGE → VISION MODEL
                             ├→ AUDIO → AUDIO MODEL
                             └→ VIDEO → VISION + AUDIO PIPELINE

TODOS
→ DECISION LAYER
→ AGENTS / SKILLS / TOOLS
→ VERIFICACIÓN
→ SALIDA ÚNICA

Para code, no necesitas tener un coding LLM grande trabajando todo el tiempo:

REQUISITO
→ SMALL LLM [entender]
→ AGENTES/SKILLS [planificar]
→ DECIDER [seleccionar ruta]
→ NanoJev [microdecisiones]
→ CODE LLM GRANDE [solo cuando hay que escribir/modificar código]
→ TEST
→ SMALL MODELS [revisión]
→ SALIDA

Eso es probablemente lo más valioso de tu diseño: el modelo pesado deja de ser el sistema operativo del agente y pasa a ser simplemente un especialista que se invoca cuando hace falta.

Y hay un detalle importante para modelos locales: no cargaría 11 modelos distintos físicamente en paralelo salvo que tengas mucha RAM/VRAM. Puedes tener 4–6 modelos pequeños reales y crear 11 miembros del consejo mediante roles/agentes diferentes sobre esos mismos pesos. Eso conserva diversidad de análisis sin multiplicar por 11 la memoria requerida.

11 MIEMBROS DEL CONSEJO
≠
11 PESOS DIFERENTES OBLIGATORIAMENTE

Ejemplo:

Gemma 3 1B ─────→ Agente 1 / 2 / 3
LFM2.5 1.2B ────→ Agente 4 / 5 / 6
Qwen3 0.6B ─────→ Agente 7 / 8
Otro small LLM ─→ Agente 9 / 10 / 11

→ 11 PERSPECTIVAS
→ 4 MODELOS CARGADOS
→ MUCHA MENOS RAM

Esa versión es bastante más eficiente para construir el Ask Council de 12 etapas que estás planteando.
Auditoría ejecutada solo dentro de Hugging Face:

1. La información está en COMAND-CENTER-1 → Jobs: [abrir Jobs HF](https://huggingface.co/jobs/COMAND-CENTER-1?utm_source=chatgpt.com).


2. Job auditor 6aac7d015c02253cfb1452fd: resultado literal MODELS 0 / DATASETS 0 / SPACES 3. [prueba](https://huggingface.co/jobs/COMAND-CENTER-1/6aac7d015c02253cfb1452fd?utm_source=chatgpt.com)


3. Los 3 Spaces encontrados son claude-github-mcp-backup, owner_HF_1 y yaiwes-ui-factory.


4. Por tanto, los LLM remotos no están almacenados como repos de modelos de tu cuenta; su trazabilidad aparece en comandos/logs de Jobs.


5. Encontré además Jobs que consultan modelos mediante model_info, from_pretrained, Router HF y otras llamadas; esos son los registros que hay que separar entre consulta y ejecución real.


6. La consulta disponible me entrega exactamente 100 Jobs; no voy a llamar a esos 100 “modelos”.


7. El Job 6aad0a29... que contiene 20 nombres es una lista wanted=[...] escrita dentro del comando: no prueba autorización ni instalación, por lo que queda escrita dentro del comando: no prueba autorización ni instalación, por lo que queda excluida como inventario.


8. Resultado forense actual: ubicación encontrada = HF Jobs; repos propios = 0; inventario de LLM realmente ejecutados todavía requiere filtrar los comandos/logs de esos Jobs uno por uno.

---FIN DOCUMENTO 2---
