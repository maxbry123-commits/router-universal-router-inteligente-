# REJECTED by Orquestador Chat + Revisor — do not execute
# Reasons: SyntaxError (unclosed triples) + flavor=cpu-basic (not 32GB RAM)
# Agent-3 must rewrite this module with flavor that meets 32GB (cpu-upgrade), port 8000.

def publish():
    raise RuntimeError(
        "REJECTED: rewrite publish_live.py — use cpu-upgrade (32GB RAM), port 8000, "
        "fix /health, Space riu-chat-yaiwes. cpu-basic forbidden."
    )
