# CHAT ORDER — LOOP 2026-09-22 22:18 COLOMBIA

Scope: CHAT ONLY.

Run in parallel:
- agent-16-chat-space-oauth
- agent-17-chat-backend-32gb
- agent-18-chat-final-auditor

Do NOT run agent-19: Open WebUI already exists and its canonical motor manifest is verified.

Rules:
- reuse Open WebUI and existing Chat MVP code
- zero overengineering
- max 3 steps
- no equivalent code from scratch
- external components only through canonical motors
- execute real changes, then real tests
- fail closed; no fake PASS
- preserve existing additional code
