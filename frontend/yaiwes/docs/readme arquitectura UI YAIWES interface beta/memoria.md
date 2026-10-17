# Memoria de continuidad — UI YAIWES frontend

## Estado actual

- Proyecto: `UI YAIWES interface`.
- Alcance: frontend modular.
- Backend: solo frontera de contrato; no se implementa aquí.
- Originales: bloqueados y no tocar.
- Método: pieza por pieza, canvas local, discusión, aprobación por ID e integración posterior.
- Primer vertical slice: `RUN-01 / CASCADE`.
- Estado: `ACTIVE_REVIEW`.

## Documentos de control

- `PLAN-DE-TRABAJO-UI-YAIWES.md`: guía maestra.
- `CRAZY-WALL-BITACORA-STATE.json`: tablero de estado, eventos y decisiones.
- `HANDOFF-FRONTEND-UI-YAIWES.json`: contrato para el siguiente equipo o IA.
- Arquitectura existente: carpeta `readme arquitectura UI YAIWES interface beta/`.

## Arquitectura que no se debe romper

```text
Usuario → Panel A/B → UI Contract → Action Bus → Bridge → Backend frontera → Eventos → Canvas
```

El frontend no debe duplicar proveedores, router, scheduler, memoria backend, secretos u orquestación interna.

## Reglas de colaboración

1. Leer el plan, la bitácora, el handoff y esta memoria antes de actuar.
2. Auditar las fuentes de la pieza asignada.
3. Mantener originales intactos.
4. Registrar cada pieza con ID.
5. Mostrar primero un canvas reversible.
6. Explicar qué es real, stub y frontera backend.
7. No integrar sin `OK <ID>`.
8. Si hay contradicción, marcar `BLOCKED`; no inventar.
9. Actualizar bitácora, handoff y memoria después de una decisión.
10. Usar componentes del catálogo solo con procedencia y propósito claros.

## Decisiones pendientes

- Elegir dirección visual: `A-Matte-Control`, `B-Holographic-Glass` o `C-Little-Factory`.
- Confirmar que Little azul queda fijado en `#2563eb` para UI YAIWES.
- Confirmar `RUN-01` como primer vertical slice.

## Registro

### 2026-09-27

Se auditó la arquitectura, el índice de 39 ventanas, las referencias de fotos, `Run.html`, la fábrica de componentes y los skills de diseño. Se creó el plan modular, el estado Crazy Wall y el handoff JSON para continuidad entre equipos.

## Plantilla de entrada para el siguiente equipo

```text
ID:
Objetivo:
Fuentes leídas:
Componentes candidatos:
Qué no tocaré:
Canvas mostrado:
Decisión solicitada:
Estado:
Pruebas:
Handoff actualizado: sí/no
```


## Norma FIFA — formato de salida (instrucción del usuario)

El método oficial de salida queda fijado así:

1. `index.html` funcional y autocontenido: snapshot, referencia visual y respaldo rápido.
2. Proyecto fuente separado: componentes, estilos, lógica, assets, configuración y dependencias.
3. Flujo obligatorio: `Diseño en Manus → HTML funcional de referencia → código fuente por componentes → guardar versión → seguir editando`.
4. Nunca guardar únicamente el HTML cuando la pieza vaya a continuar evolucionando.
5. Mantener HTML funcional, fuente modular, assets, dependencias y versión.
6. Todo el código debe permanecer separado por partes para editar una función sin romper las demás.


## Hallazgos visuales incorporados — lote actual

El lote completo actual contiene 158 imágenes en `01-original/FOTOS-REF/`. Se observaron patrones repetidos que pasan a ser requisitos visuales del Panel 1: chat móvil oscuro; composer persistente; selector de modo; botones de imagen, archivo y audio; menús desplegables; estados de ejecución; tarjetas de archivos; conectores; respuestas largas; paneles técnicos; controles de configuración; vistas de código; navegación compacta; y layouts de doble panel. Las imágenes se usan como referencia de composición y comportamiento visible, no como sustituto de contratos backend.

El primer prototipo `PANEL-01 / CHAT-01` se construye sin la etiqueta `<canvas>`, con acciones nativas reales del navegador y frontera explícita para `send_message`, `upload_file`, `transcribe_audio` y `cancel_run`.

## 2026-09-27 — PANEL-01-CHAT v0.2.0

- Se leyó arquitectura frontend, plan maestro, handoff/bitácora, `frontend-design.SKILL.md`, `Image-to-Code/SKILL.md` y referencias visuales reales de Manus/Grok/FOTOS-REF.
- Se completó la fuente modular de `PANEL-01-CHAT` y se sincronizó con un `index.html` autocontenido.
- Funciones locales implementadas: chats, modo Heavy/Expert/Fast/Auto, tool sheet, toggles, archivos/imágenes/cámara, audio MediaRecorder, mensajes, cancelación, renombrado, exportación, borrado, persistencia y responsive.
- El frontend emite acciones tipadas y mantiene fail-closed cuando no existe bridge; no fabrica respuestas de IA.
- Se añadieron `ACCEPTANCE.md` y prueba Playwright.
- Smoke Chromium: PASS en render, nuevo chat, modo, envío/fail-closed, tools, rename, rail móvil; 0 errores de consola en la corrida válida.
- Estado: REVIEW. No integrar núcleo/backend hasta `OK PANEL-01-CHAT`.

