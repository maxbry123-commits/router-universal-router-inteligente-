# Índice del repositorio y del cierre

Este archivo es el índice de navegación del repo. Solo documenta; no cambia código ni cableado en runtime.

## Dibujo de la raíz (verificado en `main` `958ec38d9da5`)

```
/
├── .claude/                      carpeta de configuración del agente
├── .github/                      plantillas y carpeta de workflows (sin Actions nuevas)
├── .gitignore
├── AGENTS.md                     reglas de los agentes (35.537 B)
├── CODE_INDEX.md                 índice de navegación del código (8.010 B)
├── Main_Skills/                  skills (terceros según el inventario)
├── ROUTER MVP v1/                carpeta heredada
├── README.md                     portada del repo (4.807 B)
├── SYSTEM_WIRING_REGISTRY.yaml   registro maestro de cableado (19.967 B)
├── _quarantine/                  código en cuarentena, no se borra
├── audit/                        auditorías y carpeta cierre/
├── chat-router/                  chat, agentes, motores, harness, plugins
├── connections/                  inventario de conexiones y bitácora de cableado
├── dag.json                      DAG de cierre (2.791 B)
├── dsl.schema.json               esquema del DSL (1.488 B)
├── handoff/                      handoffs: INDEX.md, cierre/, docs/
├── input_block_verbatim.yaml     input block del cierre (1.302 B)
├── kernel/                       guía, estado y plan del kernel
├── llm system HF/                carpeta heredada de Hugging Face
├── memory_agente_minimax_02.md   memoria del agente (26.747 B)
├── ops/                          jobs y motores de auditoría
└── router-mvp/                   router MVP, fichas y componentes
```

## Índice de documentos del cierre

| # | Documento | Qué contiene |
|---|---|---|
| 01 | [`handoff/cierre/01_SISTEMA_CENTRAL_COMUNICACION.md`](handoff/cierre/01_SISTEMA_CENTRAL_COMUNICACION.md) | Estado del sistema central HTTP+MCP |
| 02 | [`handoff/cierre/02_HISTORIAL_CABLEADO.md`](handoff/cierre/02_HISTORIAL_CABLEADO.md) | Historial de cableado y su enlace |
| 03 | [`handoff/cierre/03_HANDOFFS.md`](handoff/cierre/03_HANDOFFS.md) | Handoff principal y sub-handoffs |
| 04 | [`handoff/cierre/04_URLS.md`](handoff/cierre/04_URLS.md) | URLs visibles con resumen |

## Registro previo

[`connections/registry.yaml`](connections/registry.yaml) contiene 38 conexiones (CON-001 a CON-038), todas en `pending_audit` y sin evidencia. Sirve solo como registro de lo que existía antes; no es un sistema activo.
