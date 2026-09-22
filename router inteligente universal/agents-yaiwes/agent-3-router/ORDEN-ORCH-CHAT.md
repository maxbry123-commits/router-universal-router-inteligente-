# ORDEN ORCH-CHAT → agent-3 (P1) — listo para dispatch

**META:** chat desplegado · **Deadline ~19:22 COT**

## Hecho
space_readme · space_index · deploy_script

## Falta (único)
publish_live — BLOCKED (3 intentos)

## Causas a corregir
1. SyntaxError (~L76): string triple sin cerrar (HTML/README embebido).
2. Job en hardware que NO es 32 GB RAM (p.ej. el de 2 vCPU / 16 GB). **Incumple Director.**

## Orden (verbatim Director: «procesador / Jobs HF de 32 GB RAM», «8 vCPU / 32GB»)
1. Reescribe `publish_live.py` completo, **sin** strings triples rotos (usa Path.write_text / join de líneas).
2. Lanza el Job del Router **solo** en la máquina HF de **32 GB RAM** (8 vCPU / 32 GB). Cualquier otra máquina = rechazo / fail-closed.
3. Puerto 8000 → GET `/health` 200.
4. Publica Static Space `riu-chat-yaiwes` con `API_BASE` = endpoint real del Job.
5. Anota en crazy_wall: `space_url` + `router_endpoint` + evidencia de RAM 32 GB.
6. Smoke: POST `/chat/send`. Sin token o sin /health → fail-closed.

No inventes nombres de flavor «del Director». Solo el requisito: **32 GB RAM**.
No P2. No reabrir pasos CLOSED.
