# ORDEN ORCH-CHAT → agent-3 (P1) — FALLBACK OPCIÓN 3 (post #36)

**META:** space_url público YA · deadline ~19:22 COT

## Decisión
Opción 2 (Static+Job 32GB) falló #33/#36: LLM corrompe publish_live.py antes de python_exec.
**Carril YA = INPUT-l opción 3:** Static Space + OAuth HF + Inference Providers (sin Job permanente).

## Hecho
space_readme · space_index · deploy_script (Static)

## Orden P1 opción 3
1. Restaura/asegura Static Space `riu-chat-yaiwes` (sdk static + hf_oauth scopes: inference-api; jobs opcional).
2. index.html: chat usa token OAuth del usuario; llama Inference Providers (DeepSeek/MiniMax/Kimi/NVIDIA según disponible). NUNCA keys en secrets del Space.
3. API_BASE = endpoint Inference Providers (no placeholder). Smoke: enviar mensaje = 200.
4. Anota space_url + evidencia OAuth en crazy_wall CLOSED.
5. PROHIBIDO: regenerar publish_live con prosa; lanzar Job ≠32GB; P2.
6. publish_live.py: si lo tocas, SOLO bytes del TEMPLATE limpio (primera línea `"""`, CERO fences). Preferible NO tocarlo en esta ronda — cierra Space+OAuth+Providers primero.

## PASS
space_url usable + GET health o smoke chat 200 + fail-closed sin OAuth.
