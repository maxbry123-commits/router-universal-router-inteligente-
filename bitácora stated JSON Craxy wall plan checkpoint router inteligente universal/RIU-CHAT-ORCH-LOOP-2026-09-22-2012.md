# RIU CHAT — ORCHESTRATOR LOOP — 2026-09-22 8:12 PM Colombia

Contrato: `tel.workflow/v3` · modo `FAIL_CLOSED_LOOP`.

## Estado
`CHAT_GLOBAL_CLOSED=false`.

## Fuente
`Claude notas/ORQUESTADOR-CHAT-LOOP-2026-09-22-2009-COLOMBIA.md`.

## Hechos auditados
- agent-1-chat-hf = CLOSED 3/3.
- agent-2-chat-hf-smol = CLOSED 3/3.
- agent-3-router = PENDING_VERIFY; Space registrado no demostrado live.
- agent-5-auditor = BLOCKED 2/4.
- `integration/chat_mvp/` contiene el runtime completo del Chat MVP; no reconstruir funciones existentes sin un test que demuestre el gap.
- La publicación Static actual no basta si evita el Router y llama directamente al proveedor.

## Gaps
1. CHAT_SPACE_LIVE = OPEN.
2. CHAT_ROUTER_BACKEND_LIVE = OPEN.
3. CHAT_E2E_SEND_200 = OPEN.
4. CHAT_BROWSER_ACCEPTANCE = OPEN.
5. STORAGE_F4_EXACT = OPEN.
6. FINAL_AUDIT_CROSS = OPEN.

## Orden
`agent-3 -> agent-1/2 -> agent-5 -> final gate`.

## Regla de cierre
No aceptar `CLOSED` por workflow success ni por código presente. Requerir evidencia runtime externa y read-back.
