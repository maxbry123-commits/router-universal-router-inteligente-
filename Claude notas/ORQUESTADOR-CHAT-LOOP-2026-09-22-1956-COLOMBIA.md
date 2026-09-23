# ORQUESTADOR CHAT — LOOP PRIORIDAD ABSOLUTA

Hora de activación: 2026-09-22 7:56 PM Colombia (America/Bogota)

## Mandato del Director
- Única prioridad operativa: llevar el CHAT del Router Inteligente Universal a 100% funcional conforme a las instrucciones ya registradas.
- El orquestador NO implementa código del chat.
- El orquestador audita, registra estado, define gates y ordena a los agentes ejecutores.
- No declarar CLOSED/100% sin evidencia runtime real.
- Continuar en LOOP; no desviar recursos a tareas no-chat mientras existan gaps bloqueantes del chat.

## Fuente de verdad auditada
- `Claude notas/INPUT-VERBATIM-2026-09-20-chat-mvp.md`
- `Claude notas/PLAN-MAESTRO-CHAT-MVP.md`
- `Claude notas/PLAN-ANEXO-A-SECRET-BANK.md`
- `Claude notas/PLAN-ANEXO-B-STORAGE-Y-CHAT-OPEN-SOURCE.md`
- `Claude notas/INPUT-VERBATIM-2026-09-21-q-cadena-de-pasos-chat-hf.md`
- `Claude notas/INPUT-VERBATIM-2026-09-21-u-auditar-4-pasadas-chat-modelos.md`
- `Claude notas/RIU-0128-auditoria-4-pasadas-benchmark-real.md`
- `Claude notas/HANDOFF-COMPLETO-2026-09-22.md`
- `router inteligente universal/agents-yaiwes/agent-5-auditor/AUDIT-CHECKLIST.md`
- `router inteligente universal/agents-yaiwes/agent-5-auditor/DELEGACION.md`
- `router inteligente universal/agents-yaiwes/WATCHDOG/STATUS.md`

## Estado auditado al activar el LOOP
- agent-1-chat-hf: CLOSED 3/3.
- agent-2-chat-hf-smol: CLOSED 3/3.
- agent-3-router: PENDING_VERIFY 3/4; smoke actual FAIL (API/PAGE 401 y .hf.space 404 sin auth); Space no puede declararse live.
- agent-5-auditor: BLOCKED 2/4; lens_models agotó tiempo; lens_cross pendiente.
- Auditoría consolidada: 6 HECHO, 15 PARCIAL, 4 PENDIENTE, 3 AMBIGUO; 0 REFUTADO.

## ORDEN DE EJECUCIÓN PARA LOS AGENTES — prioridad de la próxima hora
### P0 — PUBLICACIÓN LIVE DEL CHAT
Responsable principal: agent-3-router.
Orden:
1. Resolver el Space real del chat sin regenerar trabajo ya validado.
2. Verificar identidad/namespace correcto de Hugging Face antes de marcar publicación.
3. Entregar URL real accesible.
4. Smoke obligatorio: GET/HEAD del front y llamada real al endpoint del Router.
5. Prohibido CLOSED si el host devuelve 404 o si la prueba depende solo de archivos locales.

Gate P0: URL real + front accesible + Router accesible + evidencia de smoke.

### P1 — SELECTOR + AGENTE/SIN AGENTE + PROVEEDORES
Responsable: agent-1-chat-hf.
Orden:
- Confirmar en el chat el selector de modelos/proveedores solicitado: DeepSeek V4 Flash, DeepSeek V4 Pro, Kimi K3, MiniMax M3 y ruta NVIDIA cuando corresponda.
- Confirmar modo con agente y sin agente.
- Confirmar selector/cambio de cuenta GitHub mediante referencias, nunca secretos.
- Reusar paneles existentes; no duplicar UI.

Gate P1: interacción desde el chat real y evidencia de que el Router recibe la selección.

### P2 — ARCHIVOS / MEMORIA / ALMACENAMIENTO
Responsables: agent-1-chat-hf + agent-2-chat-hf-smol.
Orden:
- Panel persistente Archivos/Memoria dentro del mismo chat.
- PostgreSQL como verdad/estado persistente.
- Redis como caché/TTL/locks/rate limits/dedup.
- Graphiti con FalkorDB como backend.
- AgentDB como memoria especializada.
- Adjuntos: subida -> ingestión -> referencias -> recuperación.
- Graphty permanece NO BLOQUEANTE/backend-only salvo orden posterior del Director.

Gate P2: un adjunto se sube, queda referenciado y puede recuperarse desde el chat; health/readback de capas mínimas.

### P3 — SECRET BANK
Responsables: agentes de chat existentes según DELEGACION.
Orden:
- Completar el camino del banco ya iniciado, sin exponer valores.
- El chat debe poder seleccionar credential_ref; ningún secreto debe aparecer en UI/logs/Redis.
- No duplicar vault ya validado.

Gate P3: operación del chat a través del broker/credential_ref y prueba de no filtración.

### P4 — AUDITORÍA FINAL
Responsable: agent-5-auditor.
Orden:
- Reanudar desde lo pendiente, no repetir lens_chat/lens_storage ya cerrados.
- Cerrar lens_models y lens_cross.
- Refutar cualquier "CLOSED" sin URL/runtime/evidencia.
- Emitir checklist final SOLO para requisitos del chat.

Gate P4: 0 requisitos bloqueantes del chat en PENDIENTE/PARCIAL/AMBIGUO.

## Criterio de 100% CHAT
No usar porcentaje documental. CHAT=100% solo si:
1. URL live accesible;
2. conversación real pasa por Router;
3. selector de modelo/proveedor funciona;
4. con agente y sin agente funciona;
5. banco de secretos funciona sin exponer claves;
6. panel Archivos/Memoria funciona;
7. adjunto se ingiere y recupera;
8. almacenamiento mínimo requerido responde;
9. prueba E2E y auditor final PASS.

## Anti-deriva
Mientras P0-P4 estén abiertos:
- no priorizar Jev/Vercel, video, imagen, OmniRoute, UI factory ni tareas generales del Router;
- no reconstruir piezas CLOSED;
- no declarar éxito por presencia de archivo;
- cada cierre exige evidencia runtime.
