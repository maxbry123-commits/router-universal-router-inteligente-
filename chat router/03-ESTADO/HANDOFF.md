# HANDOFF — CHAT YAIWES (leer primero si continúas este trabajo)
Actualizado: 2026-09-27 02:53 UTC por Opus. Director: Max.

## Orden de lectura (formato del plan de agentes)
1. `../01-PLAN/PLAN-DSL-DAG-00-CONTRATO.yaml` (reglas R01-R12, fuente de verdad M#/doc#, gobernanza, gap ladder, 12 goals, ask council, flags)
2. `../01-PLAN/PLAN-DSL-DAG-01-NODOS.yaml` (DAGs 0, A, B, C, D, E con pasos por nodo, orden y estado)
3. `../02-ARQUITECTURA/📂readme chat Arquitectura.md`
4. `../00-INSTRUCCIONES/` (verbatim del Director)
NO EJECUTAR (superseded): `../01-PLAN/PLAN-MAESTRO-CHAT.yaml`, `../01-PLAN/PLAN-DSL-DAG-CHAT-AGENTES-INFRA.yaml`, `../01-PLAN/ORQUESTADOR-DE-TRABAJO.yaml` (su contenido está integrado en los nodos C-1..C-3).

## Nodo en curso y checkpoint
- **V-1 (verbatim literal)**:
  - paso 1 ✅ `INPUT-BLOCK-VERBATIM-PARTE-5-B-DOCS-22-23.md` y `INPUT-BLOCK-VERBATIM-PARTE-5-C-DOCS-24-26-M40.md` (literal completo).
  - paso 2 ⏳ SIGUIENTE: subir `INPUT-BLOCK-VERBATIM-PARTE-2.md` con los documentos completos del 25-sep: guía de agentes (M2), Harness + Mapa Mental v3.0 (M7), docs HF 2-3-4 y M10 completo, docs 5-6-7 (M16), doc 9 completo con descripciones (M17), doc 8 micro resúmenes, doc 10 (M18), y mensajes M12, M13, M14 completos. Fuente: conversación de Opus 25–26 sep.
  - paso 3 pendiente: auditoría cruzada 5 pasadas y lista de faltantes.
- **A-1 (OmniRoute)**: prueba relanzada 27-sep 02:40 (`prueba-omniroute-router.yml`, relee la dirección en cada intento). La 1ª prueba fue inválida (usó dirección vieja). Leer resultado.

## Hecho
Router en Job 16 GB de pago; OmniRoute arranca dentro (`router inteligente universal/keeper/start_omniroute.sh`) con puerta `/omniroute/*`; conector MCP sin OAuth; forks OpenClaw y Hermes; raíz ordenada; limpieza; plan en formato del plan de agentes (contrato + nodos).

## Flags abiertos
FLAG-1 `ui_bridge.py` DATA → `chat router/03-ESTADO/data` (nodo B-1) · FLAG-2 enlace del chat de Manus (nodo D-1) · FLAG-3 Groq sin clave · FLAG-4 parte 2 del verbatim (nodo V-1 paso 2).

## STATE
```json
{"schema":"yaiwes.state/v1","proyecto":"chat-yaiwes","actualizado":"2026-09-27T02:53Z","nodos_en_curso":["V-1","A-1"],"v1_paso":2,"siguientes":["V-1.2","A-1","B-1"],"flags":["FLAG-1","FLAG-2","FLAG-3","FLAG-4"]}
```

## CRAZY WALL (1 chat = 1 nodo)
```json
{"schema":"yaiwes.crazy-wall/v1","nodos":{"V-1":{"status":"CLAIMED","agente":"opus","fase":"PASO_2","siguiente":"subir PARTE-2 literal"},"A-1":{"status":"CLAIMED","agente":"opus","fase":"PRUEBA","siguiente":"leer prueba-omniroute-router"}}}
```

<!-- YAIWES STATE HUB START -->
## Estado operativo generado por State Hub
Revisión: 1
Proyecto/tarea: `chat-yaiwes` / `RIU-0119`
Estado: **RUNNING**
Fase: `B1_STATE_HUB_COMPLETE`

### Último checkpoint
B-1: State Hub local; BITACORA reconstruye STATE/CRAZY_WALL/HANDOFF. Chat: SQLite persiste conversación/adjunto/grafo; bucket solo sync simulado. 17 pruebas locales PASS. Sin credenciales ni escritura remota; PostgreSQL, Redis, Graphiti/FalkorDB, Memanto, Graphify y AgentDB siguen pendientes de conexión verificable.

### Siguiente
B2: conectar solo servicios disponibles y después cerrar B3 adjuntos
<!-- YAIWES STATE HUB END -->
