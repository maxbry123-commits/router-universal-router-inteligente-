# Nota de Claude — 2026-09-29 (02:50 Bogotá)
Textos del Director, tal cual: `Readme arquitectura router inteligente universal/INPUT-BLOCK-VERBATIM-2026-09-29-director.md`.
Tareas y estado: `router inteligente universal/HANDOFF-PROVISIONAL-ROUTER.md` (T-11 a T-19 y sección "Órdenes 2026-09-29").
Radiografía del Router: `Readme arquitectura router inteligente universal/HUELLA-DIGITAL-ROUTER.md`.

## Hallazgos verificados (leídos en el código de main, commit 39709cf5)
- Autoescalado 16→32 GB: NO construido. Solo existe la lógica pura de elegir HF1/HF2/HF3 (`hf_scheduler.py`, tope 95 % RAM), sin conexión.
- Chat del Router: solo NVIDIA Nemotron (y Groq Qwen 3.8 en el grupo g2). Kimi K3 / GLM-5 / DeepSeek V4 Flash con NVIDIA: solo en la prioridad de los agentes, no en el chat.
- Proveedor `local` ya existe (variables `RIU_LOCAL_BASE_URL`, `RIU_LOCAL_API_KEY`): así se conectará la IA local de 32 GB sin tocar el código.
- `omniroute_proxy` no existe en main; `app.py` lo intenta montar dentro de un `try` (no rompe).
- Los documentos de Opus (OPUS-PENDIENTE, RECUPERACION-OMNIROUTE) están solo en la rama `backup-antes-limpieza-20260929`.

## Reglas que sigo (del Director)
Seguir sus instrucciones textuales; no inventar; un solo Router; no crear otro Router; no reescribir código desde cero (podar, editar quirúrgico, cablear lo descargado); un solo Job/deploy al final; no tocar el Space del conector MCP; respuestas cortas en español sencillo; sin el widget de opciones.
