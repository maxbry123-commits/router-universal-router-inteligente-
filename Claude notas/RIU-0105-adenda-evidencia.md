# RIU-0105 — ADENDA de evidencia (2026-09-20)

Completa `RIU-0105-registro-chat-mvp.md` (que se escribió antes de leer esta corrida).

- Verify tras el fix `e6afe76`: run `35504842450`, job `106062796947`, commit `855aa04`: `48 passed, 2 warnings` (exit 0).
  El E2E repitió: Kimi K3, DeepSeek V4 Flash, DeepSeek V4 Pro y MiniMax M3 = 200; documento leído por el modelo; modo con agente 200; caché 2.º envío `cached=True`; historial 2 mensajes; `gh_file[ci-a]=200`, `gh_file[ci-b]=200`; almacenamiento 18 msgs / 21 aristas / 1 acierto / 2 docs.
- Deploy: run `35504794198`, job `106062671981`, commit `4bde09f`: bundle ensamblado con 58 archivos; `GAP_SECRET_MISSING:HF_WRITE_TOKEN` (no se creó ningún Space).
- Cerebras sigue en `402 Payment required`; NVIDIA y Groq siguen `nokey`.
