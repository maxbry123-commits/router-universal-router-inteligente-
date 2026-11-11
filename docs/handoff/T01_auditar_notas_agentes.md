# T01 — Auditar notas de agentes en el repo

Estado verificado: AUDITADO. Accion de limpieza PENDIENTE de confirmacion del owner.

## Inventario (solo lectura, por API)
- `chat-router/agentes/` en `main`: 1 archivo de notas a nivel raiz, `LEEME.md` (91 lineas). URL: https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/main/chat-router/agentes/LEEME.md
- Subcarpetas (nivel 2) sin archivos de notas tipo nota/notas/readme/handoff.
- En `ccr-f01c3de9-bmry0s`, `chat-router/agentes/` tiene otras carpetas (donors, rowboat, ruflo) y no tiene `LEEME.md`.

## Clasificacion de `LEEME.md`
- Contenido: mezcla documentacion de codigo (estructura, runtime, adaptadores) con registros de estado fechados ("Completado ... 2026-10-31", tablas de versiones, "Estado verificado en este sandbox").
- Regla del owner: solo codigo, README, handoffs y cableado. `LEEME.md` es README por nombre, pero contiene registros de estado y referencias a rutas de sandbox (`/tmp/a2-inst`, `/dev/shm/riu-agentes/`). Esos registros no deben quedar en el repo.
- Propuesta: separar en dos. Dejar la parte de codigo/README. Mover los registros de estado a un handoff. Requiere confirmacion antes de tocar `main`.

## Faltante
- Confirmacion del owner para editar `LEEME.md` en `main`.
- Revisar otros directorios de notas fuera de `chat-router/agentes/` (no auditado en esta vuelta).
