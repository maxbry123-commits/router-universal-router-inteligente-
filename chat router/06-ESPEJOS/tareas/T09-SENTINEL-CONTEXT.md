# T09 — CONTEXTO DEL SENTINELA

OBJETIVO: Suite multi-chat sin reescritura + Hermes/OpenClaw por puente T06.
MIRROR: mirror/T09
EJECUTOR: GPT-5.6 Sol manual; no GitHub Actions.

FUENTES VERIFICADAS:
- Open WebUI existente en router: commit fuente 8bd8b4fac5e059578ac0c74b3c18d11139f88b7d.
- LibreChat descargado en frontend: 968950a4bdb3929c9381b80290720972cb936134.
- big-AGI descargado en frontend: 7413983159ddb7056bde035d98446d33573bfa0a.
- Jan descargado en frontend: e2185dbc7db3a002da35b3688b57910ec6fd87b2.

GATES:
1. código fuente de las cuatro UIs no se reescribe;
2. los tres chats alternativos deben quedar fijados a los commits exactos mediante gitlinks;
3. gateway solo expone yaiwes/hermes y yaiwes/openclaw;
4. gateway reutiliza puente_asistentes.py;
5. tests + bash -n + py_compile + git ls-tree deben dar exit 0;
6. no declarar PASS sin read-back de main después del cierre.
