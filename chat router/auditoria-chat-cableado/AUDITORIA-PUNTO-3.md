# PUNTO 3: auditoría de memoria, almacenamiento y harness del chat cableado

Instrucción (verbatim): "Auditar memoria + almacenamiento + harness / Verificar ruta completa: chat → puente_chat/harness → memory_runtime → memoria_yaiwes → store / Comprobar save/load/search y recuperación después de reinicio. / Mejorarlo solo después de medir qué falla."

Medición real contra el Router vivo de `LIVE_URL.json` (Job y hora: 6ac78d2ae7a0dae8a27888b5 2026-10-08 21:03:31 -0500). Entra por la misma puerta que usa la UI cableada (`/plugins/puente_chat/call`).

- Script: `auditar_memoria_p3.py --sesiones-previas router-live-e2e-20261008,kernel-sentinela`.
- Resultado completo: `informe-auditoria-p3.json`.

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
| Recuperación después de reinicio del Job | PASS |

## Recuperación después de reinicio
No hizo falta reiniciar nada ni tocar Hugging Face. El Job vivo `6ac78d2a…` nació el 2026-10-08 a las 07:31:38 COT (la fecha sale del propio id del Job; `LIVE_URL.updated` es de las 07:32:58 COT). En ese Job se leen completos, desde `/chat/history`, turnos que se escribieron en Jobs anteriores:

- `router-live-e2e-20261008`: 3 turnos. El primero es de las 05:14:09 COT; se escribió en el Job `6ac766f8…`.
- `kernel-sentinela`: 6 turnos. El primero es de las 04:49:48 COT.

Esos turnos estaban en la memoria SQLite del Job anterior, pasaron por el snapshot al bucket y volvieron con la restauración al arrancar el Job vivo.

## Qué falla (medido) y qué se mejoró
- **Backend:** ningún eslabón falló, así que no se cambió nada del backend ni de Hugging Face.
- **Chat cableado** (medido con Playwright en los puntos 1 y 2): había dos fallos. El chat inactivo seguía visible por el CSS, y al recargar se perdía la conversación. Los dos se corrigieron en los commits de los puntos 1 y 2.
