┌─────────────────────────────────────────────────────────────────────────────┐
│  FRONTEND (chat/frontend)                                                   │
│  Botón / panel “SWE CODE FREE”                                              │
│       │                                                                     │
│       ▼                                                                     │
│  POST /api/chat/send  (Vercel reescribe al Router)                          │
└─────────────────────────────┬───────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  ROUTER (Router 1 · datos)                                                  │
│  /chat/send  →  Harness DeepSeek                                            │
└─────────────────────────────┬───────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  HARNESS DEEPSEEK (chat-router/chat/backend/deepseek_harness/server.py)     │
│  Bucle de hasta 8 pasos                                                     │
│  Si el modelo pide tool “swe_code_free” → ejecuta                           │
└─────────────────────────────┬───────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  TOOL MCP “swe_code_free” (NUEVO: engine/swe_code_free_tool.py)            │
│  - Recibe issue/tarea                                                       │
│  - Invoca agente SWE (basado en princeton-nlp/SWE-agent)                    │
│  - Devuelve parche + tests                                                  │
└─────────────────────────────┬───────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  MODELO (LLM System HF / manager)                                           │
│  Genera el código o la corrección                                           │
└─────────────────────────────┬───────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  RESULTADO → Router → Harness → Frontend                                    │
│  Se muestra parche + tests en el panel                                      │
└─────────────────────────────────────────────────────────────────────────────┘
