# REJECTED — no ejecutar
# Causa: SyntaxError (triples) + Job en máquina != 32 GB RAM (requisito Director).
# Agent-3 debe reescribir publish_live.py completo. Ver ../../ORDEN-ORCH-CHAT.md

def publish():
    raise RuntimeError(
        "REJECTED: rewrite publish_live.py — Job ONLY on HF 32GB RAM machine, "
        "port 8000, /health, Space riu-chat-yaiwes. Fix unterminated strings."
    )
