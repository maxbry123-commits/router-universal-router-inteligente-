# PLAN — Pasos 1 a 5 (Chat YAIWES, almacenamiento, LLM locales, proveedores, pendientes de Claude Code 4)

Estado: 2026-11-09 · Rama: `ccr-f01c3de9-bmry0s` · Modo: loop hasta cerrar; sin escalar; bloqueos se marcan 🚩 al final.

## Reglas de ejecución
1. Orquestador delega; no implementa directamente.
2. Cada sub-agente recibe un DSL DAG de máximo 3 tareas.
3. Sandbox: solo lo usa el sub-agente de frontend y el centinela 1 (tests). Centinela 2 verifica al final que el sandbox quedó limpio.
4. Supervisor/juez/guardián/centinela/sheriff verifica el input block verbatim (`kernel/INPUT_BLOCK_YAIWES_CABLEADO.md`, rama `ccr-4806d6f4-xv37ed`) y que nadie salga de las instrucciones.
5. Sin escalar. Un bloqueo se registra como 🚩 y se deja para el final.
6. Toda evidencia se publica con URL de GitHub (commit o blob).

## Roles
| Rol | Función |
|---|---|
| Orquestador | Reparte tareas, consolida, marca PASS/🚩. |
| Supervisor-juez-guardián-centinela-sheriff (S-1) | Verifica input block y reglas. Vigila que nadie use sandbox fuera de frontend/centinela 1. |
| Centinela 1 | Ejecuta tests en sandbox (único). |
| Centinela 2 | Investiga gaps, revisa organización y cableado; al final verifica que el sandbox quedó limpio. |
| Sub-agentes de trabajo | Un DAG de ≤3 tareas cada uno. |

## DSL DAG maestro

```dsl
DAG pasos_1_a_5
  p1  cablear_swe_code_free        -> selector > chat > plugins harness DeepSeek HTTP > Router MVP v1 y Router LLM HF
  p1b cablear_chat_yaiwes_ui       -> UI Chat YAIWES con toda la rama
  p1c espejo_openclaw              -> espejo del chat con UI OpenClaw
  p2  almacenamiento_memoria       -> harness DeepSeek MCP > Router MVP v1 MCP > almacenamiento Hugging Face
  p3  llm_locales_swe_code         -> harness DeepSeek > LLM locales > SWE CODE
  p4  selectores_nvidia_groq_qwen  -> harness DeepSeek > Router LLM HF; cableados: computo, MCP, LLM/API (llaves NVIDIA/Groq), HTTP, almacenamiento/memoria
  p5  pendientes_claude_code_4     -> sub-agentes sobre tareas A2, A3, B, C, D y limpieza HF

  deps: p1 -> p1b -> p1c
        p1 -> p2
        p1 -> p3
        p3 -> p4
        p2 -> p4
        p5 -> independiente (pero requiere S-1 antes de cualquier escritura)
```

## Tareas por sub-agente (máx. 3 por agente)

| Agente | Tareas | Sandbox | Entregable |
|---|---|---|---|
| S-1 supervisor | verificar input block; revisar que nadie use sandbox fuera de regla | no | informe PASS/🚩 |
| A-1 frontend | p1b (UI Chat YAIWES) y p1c (espejo OpenClaw) | sí | commit + URL |
| A-2 backend-router | p1 (cadena SWE CODE → harness → Router MVP v1 / LLM HF) | no | commit + URL |
| A-3 almacenamiento | p2 (MCP harness → Router MVP v1 MCP → HF) | no | commit + URL |
| A-4 llm-locales | p3 (LLM locales con SWE CODE) | no | commit + URL |
| A-5 proveedores | p4 (selectores NVIDIA/Groq/Qwen y sus 5 cableados) | no | commit + URL |
| A-6 pendientes-CC4 | p5: A2 X-Ray, A3 skill "Maxbry UI frontend", B ventana, C mapa, D revisión | no | informe + commit |
| C-1 centinela 1 | ejecuta tests (único con sandbox) | sí | resultados PASS/FAIL |
| C-2 centinela 2 | investiga gaps; al final verifica sandbox limpio | no | informe de gaps y limpieza |

## Nodos y criterios de cierre

| Nodo | Criterio de cierre (todos obligatorios) |
|---|---|
| p1 | Cadena selector → chat → harness → Router MVP v1 y LLM HF cableada en código; URL de commit; test de C-1. |
| p1b | Chat YAIWES usa la rama completa; URL de commit; prueba de C-1. |
| p1c | Espejo con OpenClaw funcional; URL de commit. |
| p2 | Harness → MCP → Router MVP v1 → HF cableado; URL de commit. |
| p3 | LLM locales conectadas a SWE CODE; URL de commit. |
| p4 | Los 5 cableados de la lista; claves NVIDIA/Groq nunca en archivos; URL de commit. |
| p5 | A2, A3, B, C, D con evidencia por URL o 🚩. |
| Cierre | S-1 PASS y C-2 sandbox limpio. |

## 🚩 abiertos (no escalar; se entregan al final)
1. **Lista de limpieza de Hugging Face para MiniMax:** no existe en el repo. El owner la buscará; queda pendiente de su entrega.
2. **Llaves NVIDIA y Groq:** no se usan en esta sesión; el cableado usa variables de entorno.
3. **Input block YAIWES (12 fases):** sin auditar; S-1 lo verifica antes de cerrar.
4. **Autorización de sandbox:** confirmada por el owner solo para A-1 y C-1.

## Estado
- Plan registrado: este archivo.
- Ejecución de p1–p5: pendiente. No hay sub-agentes lanzados todavía.
