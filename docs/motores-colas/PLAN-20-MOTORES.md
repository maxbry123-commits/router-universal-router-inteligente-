# Plan: 20 motores (10 por tarea) — orden de Hy 2026-11-13 04:34

Orden literal de Hy: "divide las dos tareas 20 motores, 10 por cada tarea, 3 agente por cada tarea, delega 2 grupos". Motores: solo los inmutables del skill (motor_2 descarga+extraccion, motor_4 mover). Sin GitHub Actions, sin LFS, sin sandbox de Claude, sin Vercel para descargar.

## Grupo A — Tarea 1: copiar imput sharck a Yaiwes main / imput sharck/ (motor_2)
3 agentes. 2 supervisores. 10 motores (cada uno = 1 cola):
- A01 `queues/code.json` (hecho)
- A02 `queues/docs.json` (hecho; falta fusion de Documentos en un solo archivo + handoff)
- A03 `queues/core-1.json` (8/9 hecho; falta core-01-09)
- A04 `queues/core-2.json` (10/11; core-02-08 qdrant: SOURCE_LFS_POINTER_GAP, decide Hy)
- A05 `queues/core-3.json` (4/11; faltan 7) — A05a: items 01-06, A05b: items 07-11 (division para ir mas rapido)
- A06 `queues/core-4.json` (hecho)
- A07 `queues/core-5.json` (hecho)
- A08 `queues/core-6.json` (hecho)
Los motores A05a y A05b son la division de core-3 (mismas rutas, dos colas). Los items ya publicados se saltan solos (ALREADY_PRESENT_VERIFIED).

## Grupo B — Tarea 2: mover "todos los componentes en la raiz" a "➡️ core kernel Yaiwes/" (motor_4)
3 agentes. 2 supervisores. 10 motores.
Texto literal de Hy: "Necesito todos los componentes en la raiz pasarlo a ➡️ core kernel Yaiwes/ — Usas los motores de mover — Dividelo en 10 o 20 motores — 5 agentes en Imput shark y 5 en Yaiwes componentes — 2 supervisores por tareas".
Estado: NO empezada. Las colas B01..B10 aun no existen porque origen exacto (raiz de Imput shark y raiz de Yaiwes componentes) y destino exacto de `➡️ core kernel Yaiwes/` no estan fijados en rutas.

## Lugar de ejecucion
El skill no lo define. Pendiente de Hy. No se ejecuta nada hasta que lo indique.

## Estado actual
Ningun motor corriendo. Sandbox de Claude detenido (borrado pendiente de aprobacion humana).
Vercel: no usado.
