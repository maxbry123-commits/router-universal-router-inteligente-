# YAIWES — Tareas pendientes (auditoría X-Ray con verificación cruzada)

Actualizado 25-oct-2026. Fuente: todas las instrucciones de Antonio en este chat, cruzadas con el repo, Vercel y el reporte de Grok.
Leyenda: ✅ hecho y verificado · ⚠️ hecho en código, sin verificar en vivo · ⏳ pendiente · ❓ espera decisión de Antonio.
Cómo auditar: `git show <commit> -- <archivo>`. Historial completo: `chat/docs/*/CAMBIOS.md`.

## Índice
1. Organización · 2. Chatbot y componentes · 3. Motores · 4. Memoria y almacenamiento · 5. Chat (frontend) · 6. Chat (backend) · 7. Pruebas con Grok · 8. Reglas de trabajo

## 1. Organización
| # | Tarea | Estado | Evidencia |
|---|---|---|---|
| 1 | Dos raíces: `chat/frontend` y `chat/backend` | ✅ | `9c4e58e1a3`; auditor de cableado 5 corridas FAIL=0 |
| 2 | Raíz **Router en main**, fuera de la raíz chat router | ❓ aprobar | `chat/docs/ORGANIZACION_OBJETIVO.md` |
| 3 | Raíces propias: Harness Deepseek, **Memoria**, Agentes (+n8n, Prefect, Temporal, ruflo, rowboat, autogen, crewAI, langgraph, pydantic-ai, microsoft-agent-framework, haystack), Chatbot (solo GrokBot), Workflow Loop (con sus skills), Motores | ❓ aprobar | Tarea 7 |
| 4 | Eliminar OmniRoute (carpeta vacía) | ⏳ | `componentes/OmniRoute` sin archivos |
| 5 | MCP dentro del Router | ❓ aprobar | `mvp/mcp_route.py` ya es parte del Router |
| 6 | Router: incorporar FastAPI, Starlette, Uvicorn, HTTPX, Pydantic, PyYAML; descartar LiteLLM, pydantic-settings, vLLM-Router, vLLM-Semantic-Router, RouterArena | ❓ aprobar | LiteLLM 0 usos; HTTPX 5 archivos y falta en `requirements.txt` |
| 7 | Mover lotes grandes con los motores (copiar y mover están vacíos) | ⏳ | `plugins/motores/descarga-copia/*` sin código |

## 2. Chatbot y componentes
| # | Tarea | Estado | Evidencia |
|---|---|---|---|
| 8 | Descargar OpenBot (nightly-labs, ashhart), web-llm, transformers.js, wllama, pglite, sqlite-wasm a `componentes/chat-bot` con el motor 2 | ✅ | cola `VERIFIED_CLOSED` + readback (ver README del chatbot) |
| 9 | docs.x.ai/grok-bot y openbot.run | ❌ bloqueado | el sandbox no llega a esos dominios (HTTP 000) |
| 10 | Licencia de nightly-labs/openbot: PolyForm Noncommercial (no comercial) | ⚠️ aviso | LICENSE del repo |
| 11 | README de arquitectura del chatbot | ⏳ análisis | `componentes/chat-bot/ARQUITECTURA-CHATBOT.md` (esqueleto) |
| 12 | Chat SOS de emergencia (router mínimo + proyecto Vercel propio) | ❓ aprobar | propuesta en la respuesta del chat |
| 13 | Copiar a chatbot lo útil para la UI local (modelos embebidos y almacenamiento local) | ⏳ | web-llm, transformers.js, wllama, pglite, sqlite-wasm ya descargados |
| 14 | Confirmar ubicación de rowboat (Agentes) y llama_index | ❓ | — |

## 3. Motores
| # | Tarea | Estado |
|---|---|---|
| 15 | Integrar los motores en el chat como software: URL visible, busca, actualiza, copia y mueve; manual o como tool del LLM; temporal (se elimina al terminar; solo deja verificación o Gaps) | ⏳ |
| 16 | Construir `copiar` y `mover` (hoy vacíos) | ⏳ |
| 17 | Cada motor como función del chat (ventana `ventana-motor.js` ya existe) | ⚠️ |

## 4. Memoria y almacenamiento
| # | Tarea | Estado | Evidencia |
|---|---|---|---|
| 18 | Memoria en su propia raíz, cableada al Harness Deepseek → chat | ⏳ | el Harness solo tiene `almacen`; no hay herramienta de memoria |
| 19 | Cablear `plugins/memoria/memoria_yaiwes` como plugin del Harness | ⏳ | hoy solo llega al chat por `puente_chat` |
| 20 | Motor de cascada (disparador) hacia almacenamiento y memoria; Prometheus, PyGithub, Phoenix como fuentes | ⏳ | — |
| 21 | graphify, graphiti, memanto cableados (adaptadores por `RIU_*_URL`) | ⏳ | adaptadores existen, sin URL no operan; Parche 3: Graphiti «sin verificar» |
| 22 | Verificar que lo guardado llega al almacenamiento permanente de HF | ⏳ | `mvp/hf_store.py` probado con HF simulado; falta prueba en vivo |
| 23 | Propuesta de memoria y almacenamiento con 3 integraciones | ⏳ | en la respuesta del chat |

## 5. Chat (frontend)
| # | Tarea | Estado | Evidencia |
|---|---|---|---|
| 24 | Los modelos aparecen en el selector (Groq muestra «sin conexión con el Router») | ⚠️ | captura 10:55: Router «Sin conexión»; fichas-externas carga Groq/NVIDIA solo con el Router vivo |
| 25 | Revisar el cableado de cada botón | ⚠️ | batería e2e 0 FAIL; falta móvil real |
| 26 | Pendientes como tool para el agente y el LLM | ⚠️ | `pendientes` está en el Harness y en MCP; probar en vivo |
| 27 | Todas las funciones del chat que puedan ser tool lo sean (lista abajo) | ⏳ | — |
| 28 | Selector de modelos como ventana + indicador externo del modelo | ❓ | el revert del composer quitó los 3 selectores; decidir |
| 29 | Ganar espacio metiendo los selectores dentro de un selector | ❓ | choca con «volver a como estaba» |
| 30 | Botón de encender, apagar y reiniciar el Router (HF) | ⚠️ | `HF_TOKEN_1` existe en Vercel producción; falta prueba real |
| 31 | Botones mal ubicados | ❓ | se restauró el diseño de la base |
| 32 | El modelo debe mostrar lo que va haciendo | ⏳ | el Router no emite pasos en chat de texto |
| 33 | Formato de salida sin mensajes innecesarios y con tu formato | ⏳ | avisos «Modelo solicitado…», «Aviso: sin selector…» son del chat; capa de formato en `_chat_ficha` |
| 34 | Límite de la ventana de entrada y salida | ⏳ | sin constante de límite en el servidor; el editor crece hasta `max-height` |
| 35 | Botón «Nuevo proyecto» | ⏳ | solo en el panel superior |
| 36 | Etiquetas de modo originales | ✅ | `d932b7a88d` |
| 37 | Cubo de pensamiento y Detener visibles | ✅ | `d932b7a88d`, `chat/e2e/original.js` 15 PASS |

**Funciones del chat que deben ser tool (27):** pendientes, sala, agente, llm, yaiwes_md, almacén, memoria (falta), motor de descarga/copia/mover (falta), proyecto, ancla, archivos, sandbox, servidor (encender/apagar/reiniciar), conexiones, permisos.

## 6. Chat (backend)
| # | Tarea | Estado |
|---|---|---|
| 38 | Respuestas con la identidad del modelo elegido | ⚠️ `6d79e78b25`; verificar en vivo con «¿qué modelo eres?» |
| 39 | Claves Groq/NVIDIA en el Space | ⏳ `salud` las cuenta; sin confirmar |
| 40 | Narración en vivo de pasos | ⏳ |
| 41 | Pruebas para `/chat/agents`, `/chat/github/accounts`, `mcp_cliente.py`, `sala_turno.py` | ⏳ |
| 42 | Paneles Archivos, Canvas, Organización, Seguimiento llaman a `/chat/documents` y `/chat/org/*` que el Router MVP no sirve | ❓ |

## 7. Pruebas con Grok
| # | Tarea | Estado |
|---|---|---|
| 43 | HTTP + MCP: conectividad 16/16, `tools/list` 13, `salud`, alias | ✅ reporte de Grok sobre `b6ae4a2545` |
| 44 | t1–t6 en 10 modelos de texto más | ⏳ |
| 45 | t4 con IA ON (la enciende Antonio) | ⏳ |
| 46 | Modelos de imagen y voz (`--medios`) | ⏳ |
| 47 | Revisión visual en el móvil real (cubo, Detener, selectores, chips) | ⏳ Antonio o Grok con navegador |

## 8. Reglas de trabajo
48. PASS solo con salida real. 49. Todo a `main`. 50. Respuestas cortas y bloques copiables. 51. No avanzar sin aprobación cuando Antonio lo pida. 52. Cada arreglo con su prueba; no romper lo demás.

## Enlace con el chat
El `yaiwes.md` del chat vive en el servidor (herramienta `yaiwes_md`). Para vincularlo, escribe en él esta línea con la herramienta (`accion: escribir`):
`Pendientes: https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/main/chat/docs/YAIWES_PENDIENTES.md`
