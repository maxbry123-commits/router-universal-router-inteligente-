# ORQUESTADOR CHAT — LOOP ACTIVO — 2026-09-22 8:09 PM Colombia

## Mandato del Director
- Prioridad única: CHAT del Router Inteligente Universal al 100% funcional.
- El orquestador NO implementa el chat directamente.
- El orquestador AUDITA, registra, define gates y ORDENA a los agentes.
- Los agentes ejecutan. Ningún CLOSED sin evidencia runtime real.
- Modo LOOP: continuar sobre gaps del chat; no desviar recursos.

## Contexto auditado
Lectura completada de 77 archivos top-level de `Claude notas/`, su KIT cifrado (sin exponer secretos), los 17 archivos de Crazy Wall/STATE/CHECKPOINT/PLAN y el Handoff raíz.

## Estado real recuperado
- agent-1-chat-hf: CLOSED 3/3 (panel vault, panel router, cableado de paneles).
- agent-2-chat-hf-smol: CLOSED 3/3 (jobs panel, plantilla fija, Crazy Wall encadenado).
- agent-3-router: PENDING_VERIFY; la URL registrada `yaiwes/riu-chat-yaiwes` no está verificada.
- agent-5-auditor: BLOCKED 2/4; lens_models agotó tiempo y lens_cross queda pendiente.
- Runtime existente `integration/chat_mvp/` YA contiene UI, selector proveedor/modelo, con/sin agente, documentos, GitHub multi-cuenta, jobs, DAG, storage, Secret Bank API/bridge y 14 agentes Wordflow.
- Por tanto se prohíbe reconstruir esas piezas solo porque un checklist viejo las marque PARCIAL.

## Verificación HF del orquestador
La identidad HF conectada al orquestador es `COMAND-CENTER-1`. No aparece un Space verificable en:
- `yaiwes/riu-chat-yaiwes`
- `COMAND-CENTER-1/riu-chat-yaiwes`
Sí existe `COMAND-CENTER-1/yaiwes-ui-factory`, que pertenece a otro proyecto y NO se reutiliza.

## Gaps autoritativos del CHAT
P1. Publicación live real: Space + backend del Router accesibles; no paper CLOSED.
P2. El frontend publicado debe usar el runtime completo `integration/chat_mvp/`, no saltarse el Router llamando solo a Inference Providers.
P3. Smoke E2E: health + selector + con/sin agente + /chat/send real; auth fail-closed.
P4. Storage exacto del Plan F4 (PostgreSQL + Redis + Graphiti/FalkorDB + AgentDB + adjuntos recuperables) todavía no tiene evidencia completa; el store actual es SQLite + grafo/caché locales + documentos.
P5. Agent-5 debe reauditar contra el código real para eliminar falsos pendientes.
P6. Cierre final exige URL + prueba navegador/runtime + checklist sin gaps bloqueantes.

## Orden de ejecución
1. agent-3-router = prioridad P1: publicar el chat completo con identidad HF real y backend Router; ejecutar, no solo generar.
2. agent-1-chat-hf = prueba de aceptación del runtime/UI existente; solo parchear si la prueba demuestra un gap real.
3. agent-2-chat-hf-smol = auditar/ejecutar contrato de storage; distinguir MVP actual vs F4 exacto.
4. agent-5-auditor = completar lens_models + lens_cross y hacer refutación final usando rutas reales.

## Gate
`CHAT_100_PASS = URL_LIVE && ROUTER_BACKEND_LIVE && CHAT_SEND_200 && MODEL_SELECTOR && AGENT_DIRECT_MODES && DOCUMENTS && GITHUB_SELECTOR && SECRET_BANK && STORAGE_ACCEPTANCE && FINAL_AUDIT`.

No se declara 100% por workflow success, por archivo generado ni por status escrito por el propio agente.
