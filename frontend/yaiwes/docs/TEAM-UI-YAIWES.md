# TEAM-UI-YAIWES.md

1. Director — Product Owner.
2. Codex — Executor + Improver.
3. v0 — Visual Bootstrap opcional.
4. Reference Reader — referencias/source.
5. Design System Agent — tokens/primitives.
6. Builder — código modular.
7. Meta Visual Reviewer — adapter Meta cuando exista runtime real.
8. Sheriff — policy.
9. Validator — schema/contract/manifest.
10. Verifier — Playwright/browser.
11. Sentinel Web Auditor — investigación y auditoría externa.
12. Guardian — cierre.

Codex no sustituye al Director/referencia. v0 no decide arquitectura. Meta Review no se reclama sin evidence. Sentinel no cambia código: devuelve findings. Guardian solo PASS/FAIL/BLOCKED.


## Trazabilidad activa — CHAT-DONORS-01

- Estado: `READY_FOR_CODEX`.
- Director: ordenó copiar sin reescribir 3 chats descargados debajo de `CHAT-01` y cablearlos a Hermes/OpenClaw.
- Executor asignado por arquitectura: `Codex — Executor + Improver`.
- Handoff actualizado primero: commit `d6fa8aecd64d9deb88272f004bb69d2ed80b9de7`.
- TaskContract: `workflow/TASK-CHAT-DONORS-01.contract.json`.
- Commit del contrato: `6fde5d73b73cce4499df1aeaff6c26038b02958b`.
- Motor obligatorio: `motor_3_copy_batches.py` blob `3689924361ce4a1a9fde4ae2b6f6009c37a6042d`.
- Donors: `_chat-ui-main`, `__open-chat-ui-main`, `_chat-ui-react-master`.
- Destino: `PANEL-01-CHAT/chat-variants/{chat-ui,open-chat-ui,chat-ui-react}`.
- Wiring: adapter externo → `YAIWES_BRIDGE` → `hermes|openclaw`.
- Sheriff: donor code + Motor3 + `01-original` bloqueados para edición.
- Validator: contrato creado; ejecución aún no reclamada.
- Sentinel: pendiente después de implementación.
- Verifier: pendiente browser desktop/mobile.
- Guardian: pendiente; no PASS hasta 100%.
- Gap operativo: no se encontró runner automático que consuma órdenes Codex en este repo. No declarar `RUNNING` hasta claim real.
