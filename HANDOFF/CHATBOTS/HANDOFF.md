Fuente principal movida a chat router/chat bot/
# HANDOFF — Chat BOTS (orquestador de agentes) + ROOM CONFERENCIAS

Actualizado: 17-oct-2026 00:35, hora Bogotá (UTC-5). Dueño: **Antonio Mendoza**.

Leer antes de tocar nada:
1. [`README-ARQUITECTURA.md`](README-ARQUITECTURA.md) — arquitectura real (archivos, endpoints, memoria, límites, ROOM).
2. [`GROKBOT-FUNCIONAMIENTO-Y-MEJORAS.md`](GROKBOT-FUNCIONAMIENTO-Y-MEJORAS.md) — bloque de Antonio (verbatim; también al final de este archivo).
3. `HANDOFF/PARCHE-RECUPERACION.md`, `HANDOFF/PREFERENCIAS.md`, `HANDOFF/ARQUITECTURA.md`, `HANDOFF/TAREAS.md`.

Ramas: Chat BOTS = `orquestador-agentes-rebase` (`9dc637165f`). ROOM CONFERENCIAS + A−/A+ = `wip/room-conferencias-rebase2` (`a014c943c0`). Ninguna está en main.

## Reglas (obligatorias)

1. **Español, respuestas mínimas** a Antonio. Sin explicaciones largas.
2. **Tiempos siempre como `X s YYY ms`.**
3. **Nunca inventes.** Todo dato sale del código, de GitHub, del bucket o de una prueba tuya. Si no está, márcalo «por confirmar» y pregúntale a Antonio en una lista corta.
4. **Un agente por tarea, en su propia rama.** Sin trabajo doble.
5. **Revisión ×3:** otro agente revisa 3 veces, conecta y prueba en PC y Android.
6. **Prueba en vivo en Android (412 px, 4G), E2E real (Enviar → respuesta visible), antes de merge o deploy.** No se reporta como hecho sin esa prueba.
7. **Nunca borres nada sin el sí explícito de Antonio.**
8. **Nunca imprimas ni subas secretos** (tokens solo por nombre).
9. **No cambies la arquitectura:** COMPONENTE → HARNESS (puente_chat) → HTTP → FICHA → MODELO.
10. **En main solo va lo probado.** Lo que está a medias va en ramas `wip/…`.
11. **Un `git worktree` por rama** (sparse si el disco está justo). No toques los worktrees de otros agentes.
12. **Al terminar cada fase, actualiza `HANDOFF/TAREAS.md`** y la tabla PROGRESO de este archivo.
13. Frontend: cambios milimétricos; propuestas como HTML funcional o imágenes, no maquetas.

## INSTRUCCIONES DE ANTONIO (registro)

Registro de lo que Antonio pidió sobre Chat BOTS y ROOM. Añade una fila por instrucción nueva (fecha y hora Bogotá + texto lo más literal posible). No borres filas.

| Fecha hora (Bogotá) | Instrucción | Fuente |
|---|---|---|
| 16-oct-2026 (hora por confirmar) | Chat BOTS bajo el chat abierto; herramienta para crear agentes siempre visible | TAREAS §5 (t100) |
| 16-oct-2026 (hora por confirmar) | Sandbox con ejecución real + router de deploy (GitHub/HF/Vercel solo con token) | TAREAS §5 (t100) |
| 16-oct-2026 (hora por confirmar) | 50 agentes por sección | TAREAS §5 (t100) |
| 16-oct-2026 (hora por confirmar) | Nada se pierde: agentes, chats y proyectos persisten en la memoria existente | TAREAS §5, ARQUITECTURA |
| 16-oct-2026 (hora por confirmar) | ROOM CONFERENCIAS: los modelos debaten entre ellos | TAREAS §5 (t100) |
| 16-oct-2026 (hora por confirmar) | A−/A+ tamaño de texto | TAREAS §5 (t100) |
| 16-oct-2026 ~23:15 | Pausa total (t101 «Detente», t102 «Pon todo en pausa…») | TAREAS |
| 17-oct-2026 (hora por confirmar) | Aprueba la creación de agentes + ficha de Chat BOTS | Orden al agente de docs |
| 17-oct-2026 (hora por confirmar) | Pendiente: mirror desde los enlaces del agente | Orden al agente de docs |
| 17-oct-2026 (hora por confirmar) | Propuesta de nuevo diseño del frontend de Chat BOTS | Orden al agente de docs |
| 17-oct-2026 (hora por confirmar) | «Todos participan» en ROOM | Orden al agente de docs |
| 17-oct-2026 (hora por confirmar) | Escribir sin esperar en Chat / ROOM / Chat BOTS | Orden al agente de docs |
| 17-oct-2026 00:35 | Esta documentación (docs a main por aprobación permanente) | Orden al agente de docs |
| 17-oct-2026 00:40 | Descargar Agent Zero, OpenManus, OpenHands, Agent-S y Browser Use (solo carpetas útiles) e inventariarlos: **el agente backend debe esperar esta descarga y reciclar componentes antes de escribir código** ([`COMPONENTES-OPENSOURCE.md`](COMPONENTES-OPENSOURCE.md)) | Orden al agente de descarga |

## PROGRESO

**Todo agente actualiza esta tabla al EMPEZAR y al TERMINAR** (una fila nueva o cambia el estado de la suya). Estados: `en curso`, `hecho (rama)`, `revisión`, `probado Android`, `en main`, `bloqueado`, `fallo`.

| Fecha hora (Bogotá) | Agente / rama | Tarea | Estado | Evidencia |
|---|---|---|---|---|
| 16-oct-2026 22:51 | integrador / `orquestador-agentes-rebase` | Chat BOTS v2: backend + frontend + tool `crear_agente` + pruebas v1 | hecho (rama), sin main | commits `a1e299e446`…`9dc637165f` |
| 17-oct-2026 (hora por confirmar) | capturas / `orquestador-agentes-rebase` | Capturas del orquestador (412 px) | hecho | Fallos: el panel abierto no se oculta; el campo repo se borra al repintar (`pintar()` no lo restaura); solapes; la tira queda encima del chat |
| 17-oct-2026 (hora por confirmar) | Antonio | Creación de agentes + ficha | aprobado | — |
| 17-oct-2026 (hora por confirmar) | por asignar | Mirror desde los enlaces del agente | pendiente | No existe en el código |
| 17-oct-2026 (hora por confirmar) | rama por confirmar | Propuesta de nuevo diseño del frontend Chat BOTS | en curso | — |
| 17-oct-2026 (hora por confirmar) | `wip/room-todos` (`604b2866f2`) | «Todos participan» en ROOM | en curso | Commit: chip «Todos», botón Intervenir; «Todos x1 (12 modelos) sin errores, 2x2 con intervención» (sin revisión ×3) |
| 17-oct-2026 (hora por confirmar) | `feat/escribir-sin-esperar`, `wip/room-escribir-sin-esperar` | Escribir sin esperar en Chat / ROOM / Chat BOTS | en curso | Ramas locales; Chat BOTS: por confirmar |
| 17-oct-2026 00:13 | `wip/room-conferencias-rebase2` (`a014c943c0`) | ROOM CONFERENCIAS + A−/A+ | probado 412 px headless | 2×1 = 9 s 249 ms; 3×2 = 72 s 703 ms; recarga conserva historial; Chat 1 OK. Android real: por confirmar |
| 17-oct-2026 00:35 | docs / `docs/chatbots-handoff` | Documentación HANDOFF/CHATBOTS | en main | Este archivo |
| 17-oct-2026 00:40 | descarga / `docs/componentes-os` | Descarga + inventario de componentes open source (Agent Zero, OpenManus, OpenHands, Agent-S, Browser Use) | en main | [`COMPONENTES-OPENSOURCE.md`](COMPONENTES-OPENSOURCE.md); código en el box `/workspace/componentes-os/` (32 MB, no va al repo) |
| 17-oct-2026 00:45 | docs / `docs/tareas-separadas` | 5 tareas en archivos separados: [`HANDOFF/TAREAS/`](../TAREAS/README.md) (01–05) | en main | `HANDOFF/TAREAS/README.md` |

## Cómo retomar

1. Lee la fila más reciente de PROGRESO de tu tarea. Si está `en curso` con otro agente, no la dupliques.
2. Crea tu worktree desde la rama de la tarea (o `wip/<tarea>` nueva desde main).
3. Añade tu fila en PROGRESO (`en curso`).
4. Trabaja, prueba 412 px 4G E2E, pide la revisión ×3.
5. Actualiza PROGRESO y `HANDOFF/TAREAS.md`. Reporta a Antonio en español, mínimo, con tiempos `X s YYY ms`.

## BLOQUE DE ANTONIO (verbatim)

# GROK BOT — FUNCIONAMIENTO + PROPUESTAS DE MEJORA

## 1. CÓMO FUNCIONA GROK BOT

Grok Bot funciona como un agente persistente que combina un modelo de IA con una computadora propia en la nube, memoria, herramientas y capacidad de ejecutar tareas durante periodos largos.

### MICROFLUJO GENERAL

USUARIO → OBJETIVO → GROK BOT → PLAN → TOOLS / NAVEGADOR / TERMINAL / APPS → EJECUCIÓN → RESULTADO → MEMORIA

### COMPONENTES PRINCIPALES

1. **Bot persistente**
   - No funciona solamente como un chat.
   - Mantiene identidad y contexto.
   - Puede continuar trabajando sobre un objetivo.
   - Puede conservar memoria entre tareas.

2. **Computadora en la nube**
   - Cada Bot puede trabajar dentro de un entorno de cómputo.
   - Puede utilizar navegador.
   - Puede utilizar terminal.
   - Puede trabajar con archivos.
   - Puede interactuar con software y servicios.

3. **Chat**
   - El usuario entrega instrucciones.
   - El Bot pregunta cuando necesita información.
   - El usuario puede supervisar el trabajo.
   - Puede recibir nuevas instrucciones mientras ejecuta.

4. **Memoria**
   - Conserva información útil del trabajo.
   - Puede reutilizar contexto anterior.
   - Puede aprender preferencias y formas recurrentes de ejecutar tareas.

5. **Tools**
   - Navegador.
   - Terminal.
   - Archivos.
   - APIs.
   - Aplicaciones.
   - Integraciones.
   - Herramientas de programación.

6. **Skills**
   - Una forma de definir capacidades o procedimientos reutilizables.
   - Permiten repetir una forma determinada de ejecutar una tarea.

7. **Routines**
   - Automatizan tareas repetitivas.
   - Una rutina puede ejecutarse nuevamente sin reconstruir todo el proceso.

8. **Computer Use**
   - El Bot puede interactuar con interfaces visuales.
   - Puede abrir páginas.
   - Pulsar controles.
   - Introducir información.
   - Navegar aplicaciones.

9. **Ejecución de código**
   - Puede inspeccionar repositorios.
   - Leer código.
   - Modificar archivos.
   - Ejecutar comandos.
   - Ejecutar pruebas.
   - Investigar errores.

10. **Varios Bots**
    - Puede haber varios Bots trabajando al mismo tiempo.
    - Cada uno puede encargarse de una tarea diferente.
    - Pueden colaborar dentro del mismo trabajo.

11. **Permisos**
    - Determinadas acciones pueden permitirse.
    - Otras pueden necesitar aprobación.
    - Otras pueden bloquearse.

12. **Artefactos**
    - El trabajo puede producir:
      - código;
      - archivos;
      - documentos;
      - análisis;
      - resultados de herramientas;
      - modificaciones sobre proyectos.

### ARQUITECTURA SIMPLIFICADA

USUARIO → BOT → MODELO → PLAN → TOOL → COMPUTADORA → ARCHIVOS/APPS → RESULTADO

### PROBLEMA PRINCIPAL

Una parte importante del control todavía depende del comportamiento del agente y del modelo.

Eso puede provocar:

PLAN DEMASIADO GRANDE → CAMBIOS INNECESARIOS → MÁS TOKENS → MÁS LATENCIA → MAYOR RIESGO DE ERROR

También pueden aparecer:

TAREA → EJECUCIÓN → PROCESO BLOQUEADO → ESTADO RUNNING → SIN RECUPERACIÓN AUTOMÁTICA

O:

MODELO DICE "HECHO" → NO EXISTE EVIDENCIA SUFICIENTE → RESULTADO NO VERIFICADO


# 2. MEJORAS PROPUESTAS PARA GROK BOT

1. **GOAL LOCK**
   - Congelar el objetivo original.
   - Ningún agente puede modificar silenciosamente la misión.

2. **PLAN LOCK**
   - Crear el plan antes de ejecutar.
   - Validarlo.
   - Congelarlo.
   - Modificaciones importantes requieren una nueva revisión.

   OBJETIVO → PLAN → VALIDATE → LOCK → EXECUTE

3. **TASK COMPILER**
   - Convertir una tarea grande en microtareas pequeñas.
   - Cada tarea debe tener entrada, salida y condición de PASS.

4. **DAG DETERMINISTA**
   - Definir dependencias antes de ejecutar.

   T01 → T02 → T03
          ↘ T04
   T03 + T04 → T05

5. **1 TAREA = 1 WORKER**
   - Cada agente recibe únicamente una tarea.
   - Contexto mínimo.
   - Tools mínimos.
   - Permisos mínimos.

6. **SCOPE FIREWALL**
   - Definir exactamente qué archivos, aplicaciones o recursos puede modificar cada tarea.
   - Evitar cambios fuera del objetivo.

7. **EVIDENCE GATE**
   - Ninguna tarea puede declarar DONE solamente porque el modelo lo afirma.
   - Debe presentar evidencia real.

   RESULTADO → ARCHIVO/DIFF/TEST/LOG → VERIFY → PASS

8. **RECEIPTS**
   - Registrar cada acción importante.

   WHO → WHAT → TOOL → INPUT → OUTPUT → TIME → HASH

9. **WATCHDOG**
   - Detectar automáticamente:
     - procesos congelados;
     - workers muertos;
     - loops;
     - sesiones huérfanas;
     - estados RUNNING falsos;
     - locks abandonados.

10. **RECOVERY OS**
    - Sistema específico para recuperar tareas interrumpidas.

    RUNNING → FAIL → FREEZE → RECOVERY → RETRY/ROLLBACK → VERIFY → CONTINUE

11. **CHECKPOINTS**
    - Guardar el estado después de cada tarea correcta.

    T01 PASS → CHECKPOINT
    T02 PASS → CHECKPOINT
    T03 FAIL → RECUPERAR CHECKPOINT T02

12. **ROLLBACK AUTOMÁTICO**
    - Si una modificación rompe el sistema:
      - cancelar;
      - restaurar;
      - diagnosticar;
      - intentar nuevamente.

13. **DIFF BUDGET**
    - Limitar cuánto código puede modificar un agente.
    - Si un error necesita cambiar 5 líneas, impedir una reescritura de cientos de líneas sin autorización.

14. **TOKEN GOVERNOR**
    - Presupuesto independiente por tarea:
      - input;
      - output;
      - reasoning;
      - cache;
      - tools;
      - total.

15. **LOOP DETECTOR**
    - Detectar cuando el agente repite:
      - razonamiento;
      - búsquedas;
      - herramientas;
      - archivos;
      - intentos;
    sin generar progreso.

16. **MEMORY ROUTER**
    - Separar la memoria por niveles:

    MEMORIA USUARIO
    + MEMORIA PROYECTO
    + MEMORIA AGENTE
    + MEMORIA TAREA
    + MEMORIA SESIÓN

17. **TOOL REGISTRY**
    - Inventariar automáticamente:
      - tools;
      - MCP;
      - plugins;
      - skills;
      - APIs;
      - permisos;
      - versiones;
      - capacidades.

18. **DETECTOR DE COLISIONES DE TOOLS**
    - Comprobar nombres, schemas y versiones antes de ejecutar.
    - Evitar que dos herramientas diferentes utilicen identificadores incompatibles.

19. **CAPABILITY DISCOVERY ENGINE**
    - Antes de asignar una tarea a un agente:

    AGENTE → INSPECCIÓN → CAPACIDADES → TOOLS → WORKFLOWS → LIMITACIONES → PERFIL

    Después el Scheduler decide si ese agente es adecuado.

20. **INDEPENDENT VERIFIER**
    - El agente que crea algo no debe ser el único que lo aprueba.

    WORKER → RESULTADO → VERIFICADOR INDEPENDIENTE → PASS/FAIL

21. **SHADOW EXECUTION**
    - Ejecutar primero los cambios críticos dentro de una copia o sandbox.

    CAMBIO → SANDBOX → TEST → PASS → PRODUCCIÓN

22. **MULTI-AGENT SCHEDULER**
    - El modelo no administra la cola.
    - Un scheduler determinista controla:
      - prioridades;
      - dependencias;
      - concurrencia;
      - reintentos;
      - recursos.

23. **QUEUE MANAGER**
    - Separar agentes registrados de agentes activos.

    100 TAREAS → COLA → N WORKERS ACTIVOS → TERMINA UNO → ENTRA SIGUIENTE

24. **PERMISSION TOKENS DE UN SOLO USO**
    - Una autorización para una acción concreta no debe convertirse en permiso permanente.

25. **IDEMPOTENCIA**
    - Repetir accidentalmente una tarea no debe duplicar cambios.

    TASK-ID + ESTADO + HASH → DETECTAR DUPLICADO → NO REPETIR

26. **OUTPUT FIREWALL**
    - Antes de entregar el resultado:
      - comprobar formato;
      - evidencia;
      - archivos;
      - tests;
      - alcance;
      - errores.

27. **STATE MACHINE EXPLÍCITA**
    - Cada tarea debe encontrarse exactamente en un estado:

    QUEUED → CLAIMED → RUNNING → VERIFYING → PASS
                                ↘ FAIL → RECOVERY

28. **HEARTBEAT DE WORKERS**
    - Cada worker informa periódicamente que sigue funcionando.
    - Si desaparece:

    HEARTBEAT LOST → WATCHDOG → KILL → RECOVERY → REQUEUE

29. **CIRCUIT BREAKER**
    - Si una herramienta falla repetidamente:
      - detener llamadas;
      - evitar gastar tokens;
      - cambiar ruta;
      - informar al sistema.

30. **COST ROUTER**
    - Escoger modelo según dificultad.

    TAREA SIMPLE → MODELO PEQUEÑO
    TAREA MEDIA → MODELO MEDIO
    TAREA COMPLEJA → MODELO GRANDE

31. **CONTEXT COMPILER**
    - No enviar todo el proyecto al modelo.
    - Construir únicamente el contexto necesario para cada tarea.

32. **FILE OWNERSHIP TEMPORAL**
    - Mientras un worker modifica un archivo, otros agentes no pueden modificar simultáneamente la misma zona sin coordinación.

33. **TEST CONTRACT**
    - Cada tarea debe conocer antes de empezar cómo será validada.

    INPUT → EXECUTE → TEST CONTRACT → PASS/FAIL

34. **FAILURE CLASSIFIER**
    - Clasificar automáticamente:

    FAIL_MODEL
    FAIL_TOOL
    FAIL_NETWORK
    FAIL_PERMISSION
    FAIL_TEST
    FAIL_TIMEOUT
    FAIL_DEPENDENCY

35. **RETRY INTELIGENTE**
    - No repetir exactamente la misma operación cuando ya falló.

    FAIL → CLASIFICAR → CAMBIAR ESTRATEGIA → RETRY

36. **HUMAN APPROVAL GATE**
    - Reservar confirmación humana para acciones realmente importantes:
      - producción;
      - eliminar archivos;
      - pagos;
      - credenciales;
      - cambios irreversibles.

37. **TRACE COMPLETO**
    - Poder reconstruir exactamente:

    QUIÉN → DECIDIÓ → QUÉ → POR QUÉ → TOOL → RESULTADO → VERIFICACIÓN

38. **AGENT HEALTH SCORE**
    - Medir por agente:
      - éxito;
      - fallos;
      - tokens;
      - tiempo;
      - reintentos;
      - calidad;
      - cumplimiento de scope.

39. **AUTO ROUTING POR CAPACIDAD**
    - El Scheduler selecciona automáticamente el mejor agente según:
      - especialidad;
      - tools;
      - costo;
      - velocidad;
      - historial.

40. **GOBERNANZA FUERA DEL LLM**
    - La mejora principal:

    LLM = RAZONA / PROPONE / GENERA

    CODE DETERMINISTA = CONTROLA / PROGRAMA / AUTORIZA / VERIFICA / RECUPERA


# ARQUITECTURA PROPUESTA

USUARIO
→ GOAL LOCK
→ ARCHITECT
→ PLAN LOCK
→ TASK COMPILER
→ DAG
→ SCHEDULER
→ QUEUE
→ WORKER
→ TOOL
→ SANDBOX
→ TEST
→ VERIFIER
→ EVIDENCE GATE
→ RECEIPT
→ CHECKPOINT
→ MEMORY
→ DONE


# MICROFLUJO DE FALLO

FAIL
→ WATCHDOG
→ FREEZE
→ FAILURE CLASSIFIER
→ CHECKPOINT
→ RECOVERY
→ RETRY / ROLLBACK
→ VERIFY
→ CONTINUE


# IDEA CENTRAL

GROK BOT ACTUAL:

OBJETIVO → AGENTE INTELIGENTE → EJECUCIÓN → RESULTADO

VERSIÓN MEJORADA:

OBJETIVO
→ CONTRATO
→ DAG
→ MICRO-TAREAS
→ WORKERS AISLADOS
→ EJECUCIÓN DETERMINISTA
→ PRUEBAS
→ EVIDENCIA
→ VERIFICACIÓN
→ RECUPERACIÓN
→ RESULTADO

El LLM piensa.

El sistema determinista controla.

El agente ejecuta.

El verificador comprueba.

La evidencia decide si realmente está DONE.
