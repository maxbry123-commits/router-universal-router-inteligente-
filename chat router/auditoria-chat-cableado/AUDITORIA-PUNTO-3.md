# PUNTO 3 — Auditoría memoria + almacenamiento + harness del chat cableado

Instrucción (verbatim): "Auditar memoria + almacenamiento + harness / Verificar ruta completa: chat → puente_chat/harness → memory_runtime → memoria_yaiwes → store / Comprobar save/load/search y recuperación después de reinicio. / Mejorarlo solo después de medir qué falla."

Medición real contra el Router vivo de `LIVE_URL.json` (Job y hora: 6ac78d2ae7a0dae8a27888b5 2026-10-08 20:22:07 -0500), entrando por la misma puerta que la UI cableada (`/plugins/puente_chat/call`). Script: `auditar_memoria_p3.py`. Resultado completo: `informe-auditoria-p3.json`.

| Eslabón | Resultado |
|---|---|
| Router /health | PASS |
| puente_chat/harness status (long_context 40 turnos) | PASS |
| memoria_yaiwes → store (SQLite CONNECTED + grafo CONNECTED) | PASS |
| Almacenamiento persistente: bucket HF `yaiwes-memoria-storage` configurado con escritura | PASS |
| chat → puente_chat → memory_runtime: `memoria_guardada=true` | PASS |
| store → `/chat/history` devuelve el turno (scope `chat-ui:chat:<sesion>`) | PASS |
| Recuperación de contexto desde memoria (la UI solo envía el último mensaje) | PASS |
| Aislamiento: otra sesión no ve esa memoria | PASS |
| /memoria/save · /memoria/load · /memoria/search | PASS |
| Recuperación después de reinicio del Job | PENDIENTE |

## Qué falla (medido) y qué se mejoró
- Backend: ningún eslabón falló, así que no se cambió nada del backend ni de Hugging Face.
- Chat cableado (medido con Playwright en los puntos 1 y 2): el chat inactivo seguía visible (CSS) y al recargar la conversación desaparecía. Se corrigieron en los commits de los puntos 1 y 2.
- Recuperación después de reinicio: no se puede medir sin reiniciar el Job, y tocar Hugging Face no está autorizado. Las sesiones de prueba quedan en `estado-auditoria-p3.json`. Después del próximo cambio de Job (la renovación de las 04:00 COT), al volver a correr `python3 auditar_memoria_p3.py --estado estado-auditoria-p3.json` se comprueba si esos turnos siguen ahí.
