# RIU-0084 — Corrección de inventario HF

Fecha: 2026-09-17
Contrato: tel.workflow/v3 / FAIL_CLOSED

## Hallazgo
El registro histórico de 20 slots fue presentado incorrectamente como lista de modelos instalados. Esa inferencia no estaba soportada: los slots provenían del catálogo/Jobs del Router.

## Acción
Se retiraron del registro activo 13 IDs explícitamente rechazados por el usuario. No se borró evidencia histórica; queda como tombstone auditable en model_registry V9.

## IDs retirados
- unsloth/Qwen3-Coder-30B-A3B-Instruct-GGUF
- facebook/opt-125m
- Qwen/Qwen2.5-0.5B-Instruct
- Qwen/Qwen3-4B
- Qwen/Qwen2.5-3B-Instruct
- openai/gpt-oss-120b
- Qwen/Qwen3-32B
- dphn/dolphin-2.9.1-yi-1.5-34b
- deepseek-ai/DeepSeek-V4-Flash-0731
- ornith-ai/Ornith-1.0-9B-GGUF
- ornith-ai/Ornith-1.5-9B-GGUF
- Qwen/Qwen-72B
- Qwen/Qwen2.5-7B-Instruct-AWQ

## Evidencia
- model_registry previo blob: 97de25ba2a5bad16c21b9a1073fb69a5ebacbf36
- model_registry nuevo commit: 6fe587f7a392f3fa5512bad0652776bf34d6b9bd
- README índice nuevo commit: fbddc68b3384bf374162ebcaa79adbf5dcd7e7a1
- identidad HF autenticada: COMAND-CENTER-1
- model_search: backend no disponible; no equivale a cero modelos

## Estado
GAP_PENDING_FRESH_AUTHENTICATED_INVENTORY
