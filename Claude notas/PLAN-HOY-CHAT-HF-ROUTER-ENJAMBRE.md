# PLAN DE HOY — CHAT + HF + ROUTER MVP + ENJAMBRE (2026-09-21, 14:25 UTC)

Instrucción textual: `INPUT-VERBATIM-2026-09-21-s-tareas-modelos-locales-hoy.md`. Este archivo es la LISTA DE TAREAS completa. Los agentes las llevan hasta el final; Claude solo reparte (DSL DAG en `agents-yaiwes/<agente>/chain.yaml` y `ROUTE.json`), lee `WATCHDOG/STATUS.md` y `AUDIT-CHECKLIST.md` y corrige.

## Cómo se va más rápido (sin sobre-ingeniería)
1. Modo velocidad: `ROUTE.json` pone DeepSeek V4 Flash y MiniMax M3 primero (orden del Director) hasta que el chat esté operativo y los modelos locales instalados; entonces se quitan las dos primeras entradas y se sigue con Groq, NVIDIA, Cerebras y locales de HF.
2. Ningún agente cuelga la ronda: 12 min por paso, 75 s por llamada, 30 min por agente; las rondas retoman solo lo pendiente.
3. Lo que es infraestructura (Jobs de HF, benchmark, despliegue) lo escribe Claude una vez y se ejecuta con workflows; el código de módulos lo hacen los agentes y lo valida el Sheriff.
4. Enjambre: cada agente es una carpeta con `chain.yaml`; añadir agentes = añadir carpetas (los workflows corren en paralelo; GitHub limita a ~20 simultáneos).

## A. CHAT operativo (meta: URL pública que responda hoy)
| # | Tarea | Quién | Estado |
|---|---|---|---|
| A1 | Paneles JS: banco, estado del Router, cableado | agente 1 | HECHO (3/3) |
| A2 | Panel de trabajos en paralelo | agente 2 | pendiente (ronda en curso) |
| A3 | Plantilla fija + Crazy Wall encadenado | agente 2 | pendiente |
| A4 | Static Space (README OAuth, index.html, script de despliegue) | agente 3 | HECHO (3/3) |
| A5 | Router en un Job de HF con puerto expuesto (`RIU Router Job`) + CORS | Claude (infra) | lanzado, ver resultado |
| A6 | Publicar el Static Space apuntando a la URL del Job | Claude + agente 3 | siguiente |
| A7 | Prueba de humo del chat público (POST /chat/send) | Claude (workflow) | siguiente |
| A8 | Auditoría final del chat | agente 5 | ronda en curso |

## B. MODELOS LOCALES en HF (pesos remotos, una copia por servidor, ranuras)
| # | Tarea | Quién | Estado |
|---|---|---|---|
| B1 | Registro de modelos (Qwen3.5-0.8B Q4_0 563 MB `ggml-org/Qwen3.5-0.8B-GGUF`; LFM2.5-1.2B Instruct/Thinking Q4_K_M 731 MB; Gemma 4 E2B QAT q4_0 3.3 GB `google/gemma-4-E2B-it-qat-q4_0-gguf`; Qwen3-0.6B Q8; SmolLM3-3B `ggml-org/SmolLM3-3B-GGUF`; Nanbeige, NanoJev, Decider) | agente 4 | pendiente (ronda en curso) |
| B2 | Especificación del Job (`hf://…:/model:ro`, llama-server `-np 4 -cb --cache-prompt --cache-reuse 256 -fa -ctk/-ctv q8_0`, borrador para decodificación especulativa) | agente 4 | pendiente |
| B3 | Monitor de nodos GREEN/YELLOW/DRAIN/CLOSED y elección de nodo | agente 4 | pendiente |
| B4 | Medir tokens/s reales (llama-bench + 1/4/8 solicitudes simultáneas) | Claude (workflow `RIU Llama Bench`) | lanzado |
| B5 | Lanzar 1 servidor por nodo en HF (3 nodos × 4 ranuras) y medir | Claude + agente 4 | siguiente |
| B6 | Espejo (mirror) por modelo de API: si Groq/Cerebras/NVIDIA no responden, el Router usa el local equivalente; registro `local-<modelo>` | agente 3/4 | siguiente |
| B7 | Aceleradores por probar en CPU: OpenVINO INT4/INT8, ONNX Runtime INT8, TorchAO, bitsandbytes CPU, Static KV cache + torch.compile, HQQ; decodificación especulativa (borrador / Universal Assisted); MTP solo si el modelo lo soporta | agente 4 (benchmarks en runner) | después de B5 |

## C. ROUTER MVP
| # | Tarea | Estado |
|---|---|---|
| C1 | Resiliencia (picos, respaldo, cortacircuitos), `/chat/route` | HECHO (39 pruebas) |
| C2 | Proveedor `local` con varias URL de nodos (HF-01..03) usando el monitor de nodos | pendiente (depende de B5) |
| C3 | Ruta de agentes con `local` como último respaldo (agentes no se paran) | pendiente (depende de B5) |
| C4 | Enchufe Universal de Fables (`UniversalPluginBus`) | pendiente |
| C5 | Puente con Jev | BLOQUEADO (Vercel de solo lectura) |
| C6 | Muse Glimmer 30B + 4 agentes de Meta (DSL DAG con bucle) | pendiente (Director dirá qué harán) |

## D. ENJAMBRE / AUTOMATIZACIÓN
D1 Watchdog cada hora (HECHO). D2 Auditor con checklist (ronda en curso). D3 Añadir agentes 6–N cuando los pendientes de A/B/C se conviertan en pasos.

## Reglas
Nada fuera de las instrucciones del Director; consumo de pago mínimo al terminar el modo velocidad; claves solo por el banco; todo lo no resuelto es GAP.
