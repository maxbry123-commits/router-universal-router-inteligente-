# RIU-0106 — ADENDA de evidencia (2026-09-20)

- Verify posterior a `33f191c`/`6bce6bd`: run `35523915544`, job `106112639510`: `57 passed, 2 warnings` (exit 0). El fallo anterior (contador de aciertos de caché reseteado al refrescar) quedó corregido.
- E2E del chat (mismo run): Kimi K3, DeepSeek V4 Flash, DeepSeek V4 Pro y MiniMax M3 = 200; documento leído por el modelo; modo con agente 200; caché por defecto activa (`second=True`); GitHub `ci-a`/`ci-b` 200 y `whoami[planeta123-usa]=planeta123-usa`; `usage calls=7 input=838 cached_input=192 resp_cache_hits=2`.
- `MiniMaxAI/MiniMax-M2.7` dio 503 en esta corrida (200 en las anteriores): proveedor intermitente, no error de código.
- DAG `ORDER-000-smoke`: PASS, resultado en `chat_orders/results/ORDER-000-smoke.result.json` (`ledger_valid=true`).
- Codespace `riu-chat-mvp-v6x6j9544g752x4gp`: seguía en `Provisioning` a los 23 min. Ya existe otro Codespace previo del repo (`obscure-engine-69j9xqp66r6934g9j`, apagado) que sí clonó bien.
