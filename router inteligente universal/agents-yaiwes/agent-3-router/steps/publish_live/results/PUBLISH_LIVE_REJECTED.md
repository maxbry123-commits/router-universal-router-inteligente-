# BLOCKED — no usar este archivo

Razones (Revisor + Orquestador Chat):
1. SyntaxError: string triple sin cerrar.
2. `flavor="cpu-basic"` incumple requisito Director de **32 GB RAM**.

Agent-3 debe REESCRIBIR `publish_live.py` completo con:
- flavor que cumpla 32 GB (= `cpu-upgrade` en HF)
- puerto 8000, GET /health, Space riu-chat-yaiwes
- cero strings triples rotos

Ver `../../ORDEN-ORCH-CHAT.md`.
