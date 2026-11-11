# ANEXO — Input block 1 a 1 del frente de almacenamiento y memoria

Estado: RECEPCIÓN. Sin decisiones. Cada fuente se anota con su estado.

| # | Fuente (archivo recibido) | Contenido clave | Estado | Flags |
|---|---|---|---|---|
| F-01 | `dcc2852a…Sistema_para_que_agente_team_YAIWES…` | Análisis de Ruflo: AgentDB, Controller Registry (29 controladores en 5 niveles), herramientas MCP por dominio, capability discovery, map, preload, lazy loading. Propone Resource/Capability Brain con estados DISCOVERED → REGISTERED → HEALTHY → AUTHORIZED. | RECIBIDO | 🚩 Cifras de MCP (314/323) no verificadas. 🚩 Contrato C01–C08 con rutas de archivo sin verificar. 🚩 Commit `cdd5308` / v3.10.2 sin verificar. |
| F-02 | `66a1c977…Sistema_de_almacenamiento_y_memoria_Yaiwes.md` | — | NO LEÍDO | 🚩 Pendiente de lectura en la siguiente vuelta. |
| F-03 | `1d05a8f5…memoria_del_Wordflow…` | Memoria externa jerárquica para LLM pequeña; salida 3 de integración Workflow ↔ Memory/Audit; 65 principios; orden de programación de 23 pasos; criterio de éxito con contexto de 20 M. | RECIBIDO | 🚩 Contenido duplicado con F-04. |
| F-04 | `e25c6301…OSQUESTADOR_AUDITOR_MEMORIA_ARQUITECTURA_MAESTRA.md` | Mismo contenido que F-03 con encabezado de arquitectura maestra. | RECIBIDO | 🚩 Duplicado de F-03. Usar uno solo. |
| F-05 | `7b003 2c5…pendientes__sistema_de_loops_Obsidian_grapify_graphiti_n8n…` | Propuesta de kernel de extensión (Knowledge OS) sin base de datos de grafos: archivos JSON por entidad, índices separados, memoria por niveles, Workflow sin interfaz, Universal Storage Driver. Lista de eliminación: Neo4j, Redis, Milvus, Chroma, Graphiti, Graphify. | RECIBIDO | 🚩 Contradice F-06 (que propone absorber ideas de Graphiti y Graphify). 🚩 Meta de "90–95 % determinista" es objetivo, no medición. |
| F-06 | `329dd349…base_de_creacion_de_osquestador_auditor_y_memoria__.md` | Osquestador como capa de control determinista; kernel mínimo (ROUTE, INJECT); Resource Loop y Context Loop; Parte 1/6 con 18 componentes candidatos (SQLite, FTS5, BM25S, sqlite-vec, code-session-memory, Watchdog, NATS, Litestream, Git, OpenTelemetry, Tika, PaddleOCR, Tesseract, LadybugDB, Neo4j…); Parte 2/6 con 17 proyectos de memoria (AgenticMemory, Neo4j Agent Memory, agentmemory, Memoria, Memvid, HyperMem, cass-memory, MemOS, Acontext, Mnemon, Engram…). | RECIBIDO | 🚩 Enlaces con `?utm_source=chatgpt.com`: limpiar antes de usar. 🚩 Ningún proyecto verificado (licencia, mantenimiento, existencia). 🚩 Parte 3–6 no recibidas. |

## Reglas que se repiten en las fuentes (para el handoff)

- El kernel enruta e inyecta; no razona ni contiene motores.
- Fuente original siempre conservada; síntesis = capa derivada.
- La LLM no escribe memoria canónica: pasa por normalizador, validación, auditoría y delta.
- Recurso usable solo si AUTORIZADO.

## Flags generales del lote

1. 🚩 F-02 no leído.
2. 🚩 F-03 y F-04 duplicados.
3. 🚩 F-05 y F-06 se contradicen sobre Graphiti y Graphify.
4. 🚩 Ningún enlace de terceros verificado en esta vuelta.
5. 🚩 Cifras de referencia (314/323 MCP, 20 M de contexto, 90–95 %) no medidas.
