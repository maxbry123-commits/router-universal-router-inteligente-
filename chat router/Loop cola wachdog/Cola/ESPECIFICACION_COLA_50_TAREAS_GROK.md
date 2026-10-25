# ESPECIFICACIÓN MAESTRA — COLA AVANZADA DE 50 TAREAS PARA EL CHAT

**Documento para ejecutar con Grok / Grok Code** · **Versión 1.0** · **25 de octubre de 2026**  
**Resultado exigido:** una cola real de ejecución, persistente, verificable e integrada en el chat existente; no una demostración visual.

> **Orden para Grok:** audita primero el repositorio y la UI real antes de editar. Implementa de forma quirúrgica reutilizando el chat, las referencias a archivos, el selector de skills, las rutas HTTP, el router y el sistema de autenticación existentes. Las rutas, archivos y nombres propuestos aquí son contratos de diseño: **no afirmes que ya existen**. Si la arquitectura encontrada difiere, adáptalos sin duplicar funciones. No reemplaces el frontend ni crees un segundo chat.

---

## 1. Qué hay que construir

Crear una **Cola Inteligente de Tareas (CIT-50)** que parta del comportamiento de la captura de Grok —varias instrucciones preparadas en una bandeja, cada una editable, eliminable y reordenable— y lo amplíe hasta ser un orquestador de trabajos.

**Capacidades obligatorias:**

1. Encadenar **hasta 50 tareas por cola**; no confundir 50 tareas con 50 llamadas simultáneas a un modelo.
2. Añadir una tarea escribiéndola en el compositor del chat, importándola de un mensaje o desde una plantilla.
3. Reordenar mediante arrastrar/soltar **y** botones de subir/bajar accesibles en móvil.
4. Anclar **los mismos archivos del chat** a una tarea, a varias tareas o a toda la cola; reutilizar sus IDs y permisos, no crear un almacenamiento paralelo improvisado.
5. Asignar a cada tarea una o varias skills habilitadas, herramientas permitidas, agente/modelo, dependencias y verificaciones.
6. Crear cadenas lineales, **DAG** con condiciones y tareas paralelas solo cuando sea seguro.
7. Controlar todo desde **un botón del chat y un panel principal** con pestañas y diálogos especializados, tanto en escritorio como en Android.
8. Ejecutar en modos **manual, secuencial, DAG, LOOP controlado y Watchdog** de 10 minutos a 48 horas, sujeto a infraestructura encendida.
9. Mostrar progreso, bitácora, resultados, costes, adjuntos, errores y comprobaciones **en tiempo real**.
10. Pausar, reanudar, cancelar, saltar (con justificación), editar lo pendiente, duplicar, guardar plantillas y exportar/importar.
11. Mantener estado al actualizar la página, abandonar el chat o perder conexión; recuperar la ejecución si el **worker/infraestructura** sigue disponible.
12. Ejecutar validación automática con hasta **tres comprobaciones independientes** antes de marcar una tarea «aprobada».
13. Proteger el código existente, conservar commits de referencia, pedir aprobación humana para operaciones de riesgo y no ejecutar de nuevo efectos externos duplicados.
14. Mantener separadas la capa de la interfaz, el motor de cola, el router de modelos y las herramientas/plugins.
15. Dar salida **PASS / FAIL / NO VERIFICADO** respaldada por pruebas reales, nunca por suposiciones.

### Principios innegociables

- **Reciclar antes de crear.** Un solo compositor, un solo catálogo de archivos, una sola capa de auth, una sola implementación de cada skill/tool.
- **No prometer 48 h por dejar abierta una pestaña:** el procesamiento largo exige un worker activo y una base de datos persistente.
- **No modificar el prompt del usuario al enviarlo:** conservar texto original, crear metadatos de ejecución aparte.
- **No ejecutar algo no autorizado:** permisos por tarea y por cola, confirmaciones para escrituras/despliegues/reversiones.
- **No aumentar complejidad innecesaria:** primer lanzamiento: una cola durable en el backend y un worker con concurrencia por defecto = 1; escalar solo si hace falta.
- **No marcar como terminado si faltan pruebas, dependencias, permisos o una salida obligatoria.**

---

## 2. Reutilización del comportamiento de la captura

La captura muestra: compositor del chat, bandeja superpuesta con varias instrucciones, acciones por fila, contador de tareas y control de ejecución. **No se copiarán marcas, iconografía exacta ni código propietario.** Se reutilizará la idea de interacción.

| En la referencia | En la CIT-50 mejorada |
|---|---|
| Bandeja flotante | Cajón deslizable con modo compacto/expandido/pantalla completa |
| Instrucciones apiladas | Tarjetas con título, prompt, estado, dependencias y prioridad |
| Orden manual | Arrastrar, subir/bajar, autoordenamiento topológico con aviso |
| Número de instrucciones | `12 / 50` con barra de capacidad |
| Quitar tarea | Quitar / archivar / deshacer, con restricciones si ya se ejecutó |
| Enviar tareas | Validar -> vista previa -> Iniciar cola -> monitoreo |
| Solo texto | Texto + archivos anclados + skills + herramientas + outputs |
| Poco seguimiento | Timeline, LOOP, checkpoints, tres validaciones y auditoría |

**Comportamiento mínimo del compositor:** botón `Cola` al lado de adjuntar y de enviar; `+ Añadir a cola` incorpora el texto actual como nueva tarea **sin mandarlo al modelo todavía**; se conserva el borrador al alternar chat/cola; `Enviar ahora` mantiene su comportamiento anterior. No secuestrar Enter ni cambiar los atajos actuales sin revisión.

---

## 3. Diseño de ventana: una entrada, seis pestañas

### 3.1. Botón de activación en el chat

- Nombre visible: **Cola**; icono pequeño consistente con el tema del chat.
- Estado `OFF`: la experiencia del chat normal queda exactamente igual.
- Estado `ON`: aparece contador `n/50`, botón `+ Añadir`, acceso a cajón y control `Iniciar`.
- Luz/acento **azul cuando está activo**, diseño blanco minimalista existente; no añadir emojis de teclado ni introducir un sistema visual ajeno.
- Persistir si la cola está abierta/cerrada por chat y usuario; **no** usar este interruptor para autorizar automáticamente herramientas peligrosas.
- Posición: junto al compositor sin tapar el teclado móvil. Se permite contraer a un chip de 44 × 44 px mínimo de objetivo táctil.

### 3.2. Boceto de ventana principal, escritorio

```text
┌──────────────────────────────────────────────────────────────────────────────┐
│ COLA DE TAREAS    Cola: Auditoría Chat    [Activa]     17/50       [×]       │
│ Chat actual [▼]   Proyecto [▼]  Motor [Secuencial ▼]   Estado [Pausada]      │
├──────────────────────────────────────────────────────────────────────────────┤
│ TAREAS | FLUJO | ARCHIVOS | SKILLS/TOOLS | ACTIVIDAD | CONFIGURACIÓN         │
├──────────────────────────────────────────────────────────────────────────────┤
│ Buscar [________________] [Filtrar ▼] [Expandir] [+ Tarea] [Importar]        │
│                                                                              │
│  ☷  01  [Pendiente]  Revisar commits            [3 archivos] [2 skills] [⋯]│
│      Depende de: —  |  Modelo: Auto  |  Prioridad: Alta                       │
│  ☷  02  [Pendiente]  Auditar cableado           [1 archivo] [1 skill]  [⋯]│
│      Depende de: T01 |  Validación: 3 pruebas                              │
│  ☷  03  [Bloqueada]  Corregir frontend          [0 archivos] [ECC]      [⋯]│
│      Depende de: T02 |  Aprobación antes de escribir                        │
│      ...                                                                     │
├──────────────────────────────────────────────────────────────────────────────┤
│ [Validar cola]  [Simular] [Iniciar] [Pausar] [Reanudar] [Detener] [Guardar]   │
│ 3/17 completadas  |  24 %  |  ETA aproximada  |  coste estimado / real       │
└──────────────────────────────────────────────────────────────────────────────┘
```

### 3.3. Diseño móvil Android

- Usar **bottom sheet** con tres tamaños: mini (contador + estado), medio (lista desplazable) y completo (todas las pestañas).
- No encerrar la bandeja detrás del teclado. Soportar safe area, navegación gestual, orientación vertical y pantallas estrechas.
- Cabecera fija, pie fijo opcional; **lista con desplazamiento propio**. El chat detrás no debe desplazarse accidentalmente al arrastrar una tarjeta.
- Para reordenar: asa `☷`, menú `Mover arriba` / `Mover abajo`; drag accesible con soporte táctil y cancelación.
- Cada tarjeta muestra en cerrado: orden, nombre corto, estado, adjuntos y skills; al expandir: prompt íntegro editable, dependencias, salidas y controles.
- Al cerrar el panel **no se cancela la cola**. Si el backend sigue ejecutando, el chip muestra estado/progreso.
- Mensajes de error/confirmación accesibles, sin ocultarlos bajo modales; estados anunciados con ARIA live.

### 3.4. Pestañas del mismo panel

**A. TAREAS:** CRUD de tareas, selección múltiple, reordenamiento, prioridad, dependencia, duplicar, plantillas, seleccionar modelo/agente, estado, salida, condiciones y acciones.

**B. FLUJO:** vista secuencial y diagrama DAG (nodos y flechas), bifurcaciones, bloques LOOP, grupos paralelos, ruta crítica, ciclos inválidos resaltados, condición de cierre y simulación sin usar herramientas reales.

**C. ARCHIVOS:** los adjuntos existentes en el chat; lista anclada en cola y por tarea; buscador; procedencia; versión/hash; permisos; vencimiento; botón `Anclar a tarea / a todas / solo contexto`; desanclar sin borrar el archivo de origen.

**D. SKILLS / TOOLS:** catálogo real ya instalado; switches ON/OFF por skill y por tarea; selector del modelo/harness; herramientas HTTP/MCP registradas; permisos `solo lectura`, `escritura con aprobación`, `deshabilitada`. Mostrar disponibilidad real y la razón de rechazo.

**E. ACTIVIDAD:** cola en ejecución, progreso por tarea/paso, tokens y coste si el proveedor los devuelve, bitácora, errores, retries, verificaciones, decisiones del Sheriff/Guardián/Centinela y eventos. Exportación JSON/Markdown con datos saneados.

**F. CONFIGURACIÓN:** motor, orden, límites, concurrencia, tiempos, watchdog, política de fallo, checkpoints, repetición, aprobaciones, archivo de salida, autoapagado y restauración.

### 3.5. Diálogos secundarios reutilizables

Crear **modales ligeros** (no seis aplicaciones independientes): `Editar tarea`, `Elegir adjuntos`, `Elegir skills`, `Resolver dependencia`, `Inspeccionar resultado`, `Aprobar acción sensible`, `Historial/checkpoints`, `Conexiones MCP/HTTP`, `Plantillas`, `Informe final`.

### 3.6. Barra de acciones y estados

| Control | Efecto |
|---|---|
| `+ Tarea` | añade fila pendiente; contador 50 |
| `Añadir mensaje` | crea tarea desde el texto del chat seleccionado |
| `Adjuntar` | invoca el selector **existente** del chat |
| `Agrupar` | crea subgrupo visual; no se cuenta como tarea ejecutable |
| `Encadenar` | enlaza salida de Tn con entrada de Tn+1 |
| `Validar` | dependencias, IDs, permisos, skills, presupuestos y archivos |
| `Simular` | vista previa de orden/rutas/tiempos sin efectos externos |
| `Iniciar` | arranca la cola validada, previa autorización necesaria |
| `Pausar` | pausa cooperativa antes del próximo paso seguro |
| `Reanudar` | retoma con checkpoint y permisos vigentes |
| `Detener` | cancela tareas pendientes y solicita cancelación activa |
| `Volver a intentar` | reintento controlado con idempotencia |
| `Revertir cambio` | propuesta de rollback sobre cambios propios + aprobación |
| `Guardar plantilla` | guarda estructura sin secretos ni URLs firmadas expirables |

---

## 4. Modelo funcional de la cola

### 4.1. Dos niveles de estado

**Cola (`run`)**: `draft`, `validating`, `ready`, `queued`, `running`, `pause_requested`, `paused`, `cancel_requested`, `cancelled`, `completed`, `completed_with_errors`, `failed`, `expired`, `needs_attention`.

**Tarea (`task`)**: `draft`, `pending`, `blocked`, `ready`, `claimed`, `running`, `waiting_approval`, `retry_wait`, `verifying`, `succeeded`, `failed`, `skipped`, `cancelled`, `needs_reconciliation`.

Guardar por separado `status`, `reason_code`, `display_message`, `updated_at` y la última transición. Evitar transformar errores en éxito. Todas las transiciones deben estar autorizadas por una tabla de estados central.

### 4.2. Tipos de tareas

- `chat_prompt`: enviar una instrucción por el router de chat actual.
- `skill_call`: ejecutar una skill **registrada**, con parámetros tipados.
- `tool_call`: llamar una tool/harness ya permitida.
- `http_action`: conectar por HTTP **solo a servicios allowlist**; no URL arbitraria introducida por el modelo.
- `mcp_tool`: usar un servidor MCP autorizado por el registro de conectores.
- `validation`: pruebas, smoke test, revisión de diff, comprobaciones de salida.
- `condition`: bifurcación por expresión declarativa limitada.
- `human_approval`: esperar respuesta y registrar quién aprobó.
- `handoff`: generar estado compacto/bitácora para la siguiente tarea.
- `delay`: esperar hasta fecha/hora (sin ocupar trabajador).
- `subqueue`: composición lógica; respetar tope global y profundidad acotada.

**No** permitir scripts shell arbitrarios como «herramienta libre». Si el sistema existente los admite para desarrollo, ejecutarlos únicamente en entornos aislados y con permisos restringidos.

### 4.3. Modes de ejecución

1. **Secuencial:** T01 -> T02 -> ...; concurrencia 1.
2. **DAG:** solo se ejecutan nodos con dependencias satisfechas.
3. **Paralelo limitado:** máximo configurable 1–4 **si el entorno soporta realmente concurrencia** y las tareas no escriben en el mismo recurso.
4. **LOOP:** reiterar un conjunto finito mientras `condición` y presupuestos lo permitan; toda iteración se registra. No crear tareas infinitas silenciosamente.
5. **Watchdog:** observa salud/progreso y hace checkpoints dentro del periodo configurado; no sustituye infraestructura persistente.
6. **Supervisado:** tareas de riesgo pasan por aprobación del usuario.

**Valores iniciales:** 50 tareas máximo, secuencial, concurrencia = 1, máximo 3 reintentos técnicos por tarea, 3 verificaciones independientes configurables, timeout por llamada según herramienta, presupuesto de llamadas/tokens, duración máxima del run declarada y 1 ejecución activa por chat (configurable luego).

### 4.4. Orden y dependencias

- `position` define orden visual.
- `depends_on[]` define **orden ejecutable**: una tarea no arranca antes de sus predecesoras.
- Ordenar visualmente no puede romper el DAG; mostrar advertencia y ofrecer cambiar dependencia explícitamente.
- Detectar ciclos (Kahn o DFS) antes de guardar/iniciar, no solo antes de ejecutar.
- Condición simple: `all_success`, `any_success`, `on_failure`, `always_with_ack`, o expresión declarativa segura validada. Evitar `eval()` y Python/JS arbitrario.
- `on_failure`: `stop_queue`, `skip_dependents`, `continue_independent`, `request_user`, `retry_then_stop`. **No** saltar errores implícitamente.
- `resources_locked[]` evita dos tareas de escritura simultáneas sobre la misma rama, archivo o despliegue.
- Tareas dependientes de una aprobación esperan sin consumir worker; el reloj de la cola sigue su política explícita.

### 4.5. Política de 50 tareas

- Máximo de **50 nodos ejecutables por cola**; grupos visuales no consumen cupo.
- La repetición LOOP no crea nodos indefinidos; las iteraciones se almacenan como `task_attempts`.
- No permitir crear la tarea número 51: devolver HTTP 422 + mensaje claro.
- Importación de más de 50: ofrecer dividir en lotes enlazados, **sin iniciarlos automáticamente** ni perder orden.
- No confundir `50 tareas` con `50 herramientas`, `50 conversaciones` o `50 ventanas`.

---

## 5. Anclajes de archivos: integración con el chat (imprescindible)

### 5.1. Fuente única de adjuntos

La cola debe consumir el **mismo identificador canónico de archivo** que el compositor/selector de archivos del chat. Antes de programar, Grok debe localizar la función actual de adjuntar, leer su contrato y reaprovecharla. Si el chat usa `attachment_id`, no inventar una URL de archivo; si usa `file_id`, usar ese ID con resolución mediante el backend autenticado.

**Clases de referencias admitidas:**

| Tipo | Anclaje | Verificación |
|---|---|---|
| `chat_attachment` | ID de adjunto del chat | propietario, acceso, MIME, hash, disponibilidad |
| `github_file` | repo, ruta, ref/SHA de commit | permisos y SHA inmutable |
| `hf_artifact` | referencia de artefacto privado autorizado | disponibilidad/permisos; evitar enlaces públicos |
| `run_artifact` | salida de una tarea anterior | task_id + artifact_id + checksum |
| `workspace_file` | referencia al catálogo actual | autorización, tamaño, versión |

### 5.2. Herencia controlada de anclajes

- `global_attachments[]`: contexto compartido por las tareas autorizadas de la cola.
- `task.attachments[]`: referencias específicas.
- `inherit_global_attachments`: `true`/`false` para cada tarea.
- `input_bindings[]`: vincula una salida concreta de otra tarea, no todo el historial indiscriminadamente.
- `read_scope`: `metadata`, `excerpt`, `full_content`, sujeto a permisos y tamaño.
- `mutable`: normalmente `false`; un cambio explícito requiere `write_scope` y aprobación.
- Crear vista `Adjuntos usados por T03`, con `Ir al origen en chat` y `Ver versión exacta`.

**Regla clave:** anclar **no** equivale a copiar automáticamente archivos binarios a cada prompt. El backend resuelve el archivo para cada herramienta solo cuando la tarea lo necesita. No reinyectar todo el contexto en las 50 tareas si no es necesario; optimizar por referencias, resúmenes acotados y contenido selectivo.

### 5.3. Archivo cambiado, eliminado o vencido

- Antes de arrancar: validar referencias y permisos.
- Antes de consumir: reevaluar existencia y vigencia.
- Si cambió SHA o versión: `waiting_approval` o `blocked` según la política, nunca sustituir silenciosamente.
- Si un enlace firmado venció: renovarlo por el backend autorizado o marcar `unavailable`, nunca insertar el token en logs.
- Al quitar el anclaje de una tarea **no** borrar el archivo original del chat.
- Limitar tamaño por proveedor y por tipo, aplicar validación MIME real y tratamiento seguro de nombres/paths.

### 5.4. Ejemplo de anclaje

```json
{
  "global_attachments": [
    {
      "source": "chat_attachment",
      "ref_id": "att_01",
      "read_scope": "excerpt",
      "sha256": "hash-servidor-real",
      "binding": "contexto_general"
    }
  ],
  "tasks": [
    {
      "id": "T03",
      "inherit_global_attachments": true,
      "attachments": [{"source": "github_file", "repo_ref": "repo_autorizado", "path": "mvp/app.py", "revision": "SHA_DEL_COMMIT"}],
      "input_bindings": [{"from_task": "T02", "output": "audit_report", "as": "audit_input"}]
    }
  ]
}
```

`att_01` y `SHA_DEL_COMMIT` son **valores ilustrativos**, no IDs reales. Resolverlos contra las interfaces ya existentes.

---

## 6. Activación de skills, herramientas y modelos

### 6.1. Reusar el catálogo, no crear otro motor de skills

Grok debe identificar primero dónde se registran skills y tools. Agregar **una capa de selección/permiso para la cola**, no un segundo cargador de plugins. Una skill solo es seleccionable cuando hay metadatos reales: `skill_id`, versión, compatibilidad, permiso requerido, herramientas que expone, precondiciones y estado.

**Panel Skills/Tools:** catálogo con búsqueda, descripción corta, versión, ON/OFF, estado (`disponible`, `requiere permiso`, `desconectada`), selector de alcance `cola/tarea`, botón `Probar conexión` no destructivo.

**Familias de skills que puede reutilizar si existen en el proyecto:**

- `/ecc-accessibility`, `/ecc-ai-regression-testing`, `/ecc-click-path-audit`
- `/frontend-design`, `/frontend-safety`, `/redesign`
- `/session-start-hook`, `/systematic-debugging`, `/test-driven-development`
- `/ui-ux-pro-max`, `/verification-before-completion`

**No asumir su instalación**: inspeccionar manifiestos y rutas. Si una skill no existe, marcarla «no disponible» y no fabricar una supuesta ejecución exitosa.

### 6.2. Tres niveles de permiso (mínimo)

1. `read`: lectura de estado, archivos, commits, herramientas de inspección.
2. `write_approved`: crear/editar/commitear tras verificar propiedad y autorización; aprobación explícita según reglas.
3. `destructive_approved`: borrar, desplegar, revertir, modificar secretos o repositorios: autorización puntual adicional y límites de alcance.

`OFF` elimina la capacidad de invocarla. `ON` significa **elegible**, no «autorizada para cualquier operación».

### 6.3. Enrutamiento a modelos

- `model_policy`: `inherit_chat`, `auto_router`, `fixed_model`, `fallback_chain`.
- Reutilizar el selector y el router **ya presentes**; las fichas del modelo conservan su configuración de herramientas, pensamiento, streaming y proveedor.
- Una tarea sin modelo fijado usa la selección del chat únicamente si fue guardada como política heredada; registrar el modelo elegido realmente en cada intento.
- Fallback **no debe** reejecutar por duplicado una acción externa que pudo completarse.
- Registrar `finish_reason` real; si `length`, tratar como incompleto y continuar solo bajo un límite y una estrategia válida; jamás inferir `success` por haber recibido texto.
- Herramientas invocadas por el modelo deben comprobarse contra la **lista permitida para esa tarea**, aunque el modelo solicite otras.

### 6.4. Arquitectura de dos edificios (si sigue vigente)

```text
EDIFICIO 1                                      EDIFICIO 2
Chat UI -> Router/Fichas -> API Cola  -------HTTP------> Host de plugins/Harness
              |                   autenticado             |     |
              |                                          Skills  Tools/MCP
              v
        BBDD de cola + worker
```

- No introducir imports Python directos entre ambos edificios si la regla del proyecto exige **HTTP únicamente**.
- Reutilizar la interfaz `POST /plugins/{plugin}/call/{accion}` **solo si existe y está confirmada**.
- Añadir `run_id`, `task_id`, `attempt_id`, `trace_id`, `idempotency_key` como metadatos de llamada, sin romper clientes anteriores.
- `X-API-Key` únicamente si ya es el mecanismo real, siempre desde secretos en servidor; nunca en frontend ni logs.
- Se puede integrar un conector MCP aparte, pero **MCP no es sinónimo del HTTP interno** del router; mantener los protocolos separados.

### 6.5. Conexiones MCP/HTTP dentro del panel

Pestaña Skills/Tools -> `Conectores`:

- Lista de servidores MCP y endpoints HTTP **previamente registrados**.
- Probar estado/versión/capacidades sin enviar datos sensibles de tareas.
- Activar por cola y por tarea; allowlist de herramientas.
- Para MCP remoto: usar **Streamable HTTP** a través de un cliente/SDK compatible con la versión que anuncia el servidor; autenticación, validación de `Origin` en servidor y autorización por usuario. No crear un «MCP bidireccional» propio incompatible.
- Para HTTP del harness existente: respetar contratos, tiempos de espera, claves y esquemas de respuesta.
- Prohibir URL interna arbitraria para evitar SSRF y acceso no autorizado a metadatos/servicios.

---

## 7. Plan, objetivos, LOOP, verificación y roles

### 7.1. Campos opcionales de contexto estructurado

Cada cola puede almacenar:

```yaml
plan: "Resultado esperado y estrategia resumida"
objetivo: "Condición final verificable"
reglas: ["Solo tocar archivos autorizados", "No exponer secretos"]
protocolo: "Edición quirúrgica, commit de referencia, pruebas"
profile: "Backend/Frontend/Router según tarea"
criterios_de_cierre:
  - "Todos los nodos requeridos tienen resultado verificado"
  - "Pruebas unitarias, integración y UI pasan"
bitacora: true
handoff: true
contexto_compacto: true
crazy_wall: false
```

El **micro-kernel organizador**, si ya existe, puede generar **únicamente** fichas de plan, objetivos, dependencias, handoff, índice, lista de tareas, bitácora y resúmenes compactos cuando haga falta. **No** iniciar otro agente pesado para tareas triviales ni convertir ese micro-kernel en ejecutor de herramientas.

### 7.2. LOOP controlado

Configuraciones:

- `max_iterations`: entero acotado, por defecto 1; ejemplo 3–10, nunca infinito.
- `stop_when`: condición verificable (e.g., suite de pruebas supera umbral y no quedan fallas bloqueantes).
- `retry_strategy`: retroceso exponencial con jitter para fallos transitorios, distinto de las iteraciones de razonamiento.
- `checkpoint_every`: después de cada tarea o paso con efectos externos.
- `context_compaction`: conservar decisiones, resultados, IDs y próximos pasos, sin perder evidencia ni instrucciones.
- `budget`: tiempo, tokens, llamadas y coste máximo.
- `no_progress_threshold`: detectar estancamiento y suspender/solicitar intervención.

### 7.3. Tres verificaciones antes de PASS

No significa repetir tres veces el mismo clic sin inspección. Preferir **tres capas distintas**:

1. **V1 — técnica:** schema, tipos, lint, pruebas unitarias de la función modificada.
2. **V2 — integración:** ruta real chat -> cola -> router -> plugin/harness -> respuesta, con datos controlados.
3. **V3 — funcional/regresión:** recorrido de usuario desde la UI móvil/escritorio, reload y verificación de que no se rompió el chat existente.

Para tareas que no modifican software, configurar verificadores alternativos: existencia/consistencia, fuente cruzada, comprobación de artefacto. Registrar salida cruda, duración, `exit_code` y referencia a evidencias; `PASS` solo si todas las verificaciones requeridas aprobaron. Una verificación que no se pudo ejecutar es `NO_VERIFICADO`, no `PASS`.

### 7.4. Roles opcionales, sin crear procesos duplicados

- **Sheriff:** valida alcance/permisos, bloquea escalado, operaciones no autorizadas y herramientas prohibidas.
- **Centinela:** monitoriza cumplimiento del plan/LOOP, estado real del cableado, trazas y desviaciones.
- **Guardián:** comprueba tareas incompletas, dependencias, criterios de cierre y no permite falsos PASS.
- **Orquestador:** coordina cola, checkpoints, estado, bitácora, handoff y resumen final.

Implementar primero como **políticas/verificadores o adaptadores reutilizables**, no como cuatro LLM permanentes cobrando por cada paso. Solo convocar agentes distintos cuando aporten valor verificable y tengan autorización.

---

## 8. Contratos de datos y validación

### 8.1. Modelo recomendado de cola (contrato JSON)

```json
{
  "schema_version": "cit50.v1",
  "queue_id": "q_ejemplo",
  "chat_id": "chat_actual",
  "project_id": "proyecto_actual",
  "title": "Auditoría + reparación quirúrgica",
  "revision": 1,
  "mode": "dag",
  "concurrency": 1,
  "max_tasks": 50,
  "max_duration_seconds": 3600,
  "run_policy": {
    "on_failure": "request_user",
    "max_attempts_per_task": 3,
    "verification_checks": 3,
    "approval_for_writes": true,
    "allow_auto_rollback": false
  },
  "watchdog": {
    "enabled": true,
    "duration_minutes": 60,
    "heartbeat_seconds": 30,
    "no_progress_minutes": 10
  },
  "global_attachments": [],
  "skill_allowlist": ["verification-before-completion"],
  "status": "draft",
  "tasks": [
    {
      "id": "T01",
      "position": 1,
      "title": "Revisar historial",
      "type": "chat_prompt",
      "prompt": "Revisa los últimos commits y entrega evidencia con archivo:línea.",
      "depends_on": [],
      "model_policy": "inherit_chat",
      "attachments": [],
      "skill_ids": [],
      "tool_ids": [],
      "priority": 10,
      "requires_approval": false,
      "produces": ["commit_audit"],
      "status": "pending"
    },
    {
      "id": "T02",
      "position": 2,
      "title": "Auditar el cableado",
      "type": "chat_prompt",
      "prompt": "Audita el cableado actual con evidencia; no modifiques archivos.",
      "depends_on": ["T01"],
      "input_bindings": [
        {"from_task": "T01", "output": "commit_audit", "as": "historial"}
      ],
      "attachments": [],
      "skill_ids": [],
      "tool_ids": [],
      "priority": 10,
      "requires_approval": false,
      "produces": ["wiring_audit"],
      "status": "pending"
    },
    {
      "id": "T03",
      "position": 3,
      "title": "Proponer diff frontend",
      "type": "chat_prompt",
      "prompt": "A partir de la auditoría, prepara un cambio mínimo y muestra el diff; no apliques todavía.",
      "depends_on": ["T02"],
      "input_bindings": [
        {"from_task": "T02", "output": "wiring_audit", "as": "auditoria"}
      ],
      "attachments": [],
      "skill_ids": [],
      "tool_ids": [],
      "priority": 8,
      "requires_approval": false,
      "produces": ["proposed_diff"],
      "status": "pending"
    },
    {
      "id": "T04",
      "position": 4,
      "title": "Aprobar cambios",
      "type": "human_approval",
      "prompt": "Solicitar aprobación del diff exacto y sus rutas.",
      "depends_on": ["T03"],
      "attachments": [],
      "skill_ids": [],
      "tool_ids": [],
      "priority": 10,
      "requires_approval": true,
      "produces": ["approval_id"],
      "status": "pending"
    },
    {
      "id": "T05",
      "position": 5,
      "title": "Aplicar y verificar",
      "type": "skill_call",
      "prompt": "Aplicar solo el diff aprobado, ejecutar V1/V2/V3 y emitir informe.",
      "depends_on": ["T04"],
      "attachments": [],
      "skill_ids": ["verification-before-completion"],
      "tool_ids": [],
      "priority": 8,
      "requires_approval": true,
      "produces": ["verification_report"],
      "status": "pending"
    }
  ]
}
```

**Nota:** contrato de referencia. Grok debe adaptar `chat_id`, `attachments`, `skill_id` y acciones a IDs reales. Una tarea de tipo `skill_call` necesita parámetros tipados reales antes de ejecutarse; el ejemplo **no** autoriza su ejecución automática.

### 8.2. Campos mínimos de tarea

| Campo | Tipo | Reglas |
|---|---|---|
| `id` | UUID interno + alias visible T01 | inmutable; alias puede cambiar al reordenar sin romper enlaces |
| `queue_id` | UUID | pertenencia y autorización obligatorias |
| `position` | entero | único por cola al guardar versión |
| `title`, `prompt` | texto | preservar caracteres y saltos; límites configurables |
| `type` | enum | catálogo de tipos conocido |
| `depends_on` | array UUID | sin ciclos, sin referencias a otras colas salvo contrato explícito |
| `condition`, `on_failure` | enums/esquema | evaluador declarativo sin `eval` |
| `attachments` | array referencias | acceso validado antes de uso |
| `skill_ids`, `tool_ids` | array IDs | intersección con allowlist y permisos |
| `model_policy` | enum/objeto | nunca pasar claves de API al cliente |
| `priority` | entero | dentro de DAG listo, prioridad secundaria |
| `retry`, `timeout` | objeto | límites superiores del servidor |
| `input_bindings` | referencias tipadas | salidas compatibles con entradas |
| `outputs` | metadatos de artefactos | no volcar grandes binarios en JSON |
| `verification` | array resultados | V1/V2/V3, trazas, evidencia |
| `status`, `reason_code` | enum | transición validada |
| `created_at`, `updated_at` | UTC | formato ISO-8601 |

### 8.3. Eventos de ejecución

```json
{
  "event_id": 182,
  "type": "task.verification.completed",
  "queue_id": "q_ejemplo",
  "run_id": "run_ejemplo",
  "task_id": "T05",
  "attempt_id": "attempt_ejemplo",
  "timestamp": "2026-10-25T11:30:00Z",
  "trace_id": "trace_ejemplo",
  "payload": {
    "check": "V2",
    "status": "passed",
    "evidence_ref": "artifact_ref"
  }
}
```

El evento es **append-only** con secuencia incremental por cola para reanudar conexiones sin duplicar eventos visibles.

---

## 9. API interna: propuestas sin romper rutas existentes

Ruta nueva de referencia **solo si el repositorio no tiene ya un módulo equivalente:** `/api/task-queues`. Todas las rutas exigen sesión/autorización y validación `queue_id -> dueño/chat/proyecto`.

| Método | Endpoint propuesto | Función |
|---|---|---|
| `POST` | `/api/task-queues` | crear cola borrador |
| `GET` | `/api/task-queues?chat_id=...` | listar colas autorizadas |
| `GET` | `/api/task-queues/{qid}` | recuperar cola completa |
| `PATCH` | `/api/task-queues/{qid}` | título, modo, políticas, con revisión |
| `POST` | `/api/task-queues/{qid}/tasks` | añadir tarea si < 50 |
| `PATCH` | `/api/task-queues/{qid}/tasks/{tid}` | editar pendiente o no reclamada |
| `DELETE` | `/api/task-queues/{qid}/tasks/{tid}` | borrar solo si estado lo permite |
| `PUT` | `/api/task-queues/{qid}/order` | orden + revisión optimista |
| `POST` | `/api/task-queues/{qid}/validate` | comprobar DAG/permisos/adjuntos |
| `POST` | `/api/task-queues/{qid}/simulate` | análisis sin ejecución real |
| `POST` | `/api/task-queues/{qid}/start` | iniciar y devolver run_id |
| `POST` | `/api/task-queues/{qid}/pause` | solicitar pausa |
| `POST` | `/api/task-queues/{qid}/resume` | reanudar |
| `POST` | `/api/task-queues/{qid}/cancel` | solicitar cancelación |
| `POST` | `/api/task-queues/{qid}/tasks/{tid}/retry` | nuevo intento controlado |
| `POST` | `/api/task-queues/{qid}/approvals/{aid}/decision` | aprobar/rechazar (idempotente) |
| `GET` | `/api/task-queues/{qid}/events?after=182` | obtener eventos desde cursor |
| `GET` | `/api/task-queues/{qid}/stream` | SSE autenticado con reconexión |
| `GET` | `/api/task-queues/{qid}/artifacts` | salidas y evidencias autorizadas |
| `GET` | `/api/task-queues/{qid}/export` | JSON/Markdown saneado |
| `POST` | `/api/task-queues/import` | importar y validar antes de activar |

**Integración:** el frontend llama solo a la API del backend; el backend resuelve chat, permisos, herramientas, archivos, modelo y worker. No llamar desde navegador a claves privadas de GitHub, HF, MCP o proveedores LLM.

### 9.1. Errores estructurados

```json
{
  "error": {
    "code": "QUEUE_LIMIT_REACHED",
    "message": "La cola ya contiene 50 tareas.",
    "details": {"limit": 50},
    "trace_id": "trace_actual"
  }
}
```

Casos esenciales: `INVALID_DAG`, `MISSING_ATTACHMENT`, `SKILL_UNAVAILABLE`, `UNAUTHORIZED_TOOL`, `REVISION_CONFLICT`, `QUEUE_ALREADY_RUNNING`, `APPROVAL_REQUIRED`, `RUN_EXPIRED`, `TASK_LOCKED`, `IDEMPOTENCY_CONFLICT`.

### 9.2. Control de concurrencia en ediciones

- Cada cola tiene `revision` incremental. El cliente envía `If-Match` o `revision` esperada.
- Al editar simultáneamente desde móvil/escritorio, responder `409` y ofrecer fusionar cambios, no sobrescribir.
- Toda mutación de tareas escribe un evento de auditoría; no se permite mutar las tareas ya completadas de forma retroactiva.
- Si una cola está ejecutándose, edición solo de tareas `pending/blocked` no reclamadas y de sus dependencias si siguen válidas.

---

## 10. Persistencia y estructura mínima de base de datos

**Para funcionamiento real:** la cola/los eventos y el progreso viven en el backend, **no solamente en `localStorage`**. IndexedDB puede guardar borradores de interfaz, pero no es fuente de verdad de ejecuciones.

Tablas lógicas necesarias (crear migraciones solo si no hay equivalentes):

```sql
-- SQL ILUSTRATIVO: adaptar al motor elegido, tipos y migrador real.
CREATE TABLE task_queues (
    id TEXT PRIMARY KEY,
    owner_id TEXT NOT NULL,
    chat_id TEXT NOT NULL,
    project_id TEXT,
    title TEXT NOT NULL,
    status TEXT NOT NULL,
    mode TEXT NOT NULL,
    revision INTEGER NOT NULL DEFAULT 1,
    config_json TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE queue_tasks (
    id TEXT PRIMARY KEY,
    queue_id TEXT NOT NULL REFERENCES task_queues(id),
    position INTEGER NOT NULL,
    status TEXT NOT NULL,
    task_json TEXT NOT NULL,
    claimed_by TEXT,
    lease_until TEXT,
    current_attempt INTEGER NOT NULL DEFAULT 0,
    version INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE INDEX ix_task_queue_status ON queue_tasks(queue_id, status);

CREATE TABLE queue_attempts (
    id TEXT PRIMARY KEY,
    queue_id TEXT NOT NULL,
    task_id TEXT NOT NULL REFERENCES queue_tasks(id),
    attempt_number INTEGER NOT NULL,
    status TEXT NOT NULL,
    idempotency_key TEXT NOT NULL UNIQUE,
    started_at TEXT,
    finished_at TEXT,
    checkpoint_json TEXT,
    result_ref TEXT,
    error_code TEXT
);

CREATE TABLE queue_events (
    id TEXT PRIMARY KEY,
    queue_id TEXT NOT NULL REFERENCES task_queues(id),
    event_seq INTEGER NOT NULL,
    event_type TEXT NOT NULL,
    event_json TEXT NOT NULL,
    created_at TEXT NOT NULL,
    UNIQUE(queue_id, event_seq)
);
CREATE INDEX ix_queue_event_cursor ON queue_events(queue_id, event_seq);

CREATE TABLE queue_approvals (
    id TEXT PRIMARY KEY,
    queue_id TEXT NOT NULL,
    task_id TEXT NOT NULL,
    action_digest TEXT NOT NULL,
    status TEXT NOT NULL,
    decided_by TEXT,
    decided_at TEXT,
    expires_at TEXT
);

CREATE TABLE queue_attachments (
    id TEXT PRIMARY KEY,
    queue_id TEXT NOT NULL,
    task_id TEXT,
    source TEXT NOT NULL,
    source_ref TEXT NOT NULL,
    metadata_json TEXT NOT NULL
);
```

`queue_dependencies` puede ser una tabla aparte con clave compuesta `(task_id, depends_on_id)` o vivir en `task_json` inicialmente **si** se valida transaccionalmente; para búsquedas/escala, tabla separada.

**Requisitos adicionales:** índices por usuario/chat, snapshot de modelo/skills/permisos al comenzar, estado por run distinto del borrador si una plantilla puede ejecutarse varias veces, retención configurable, borrado lógico de historial y migraciones reversibles.

### 10.1. Elegir almacenamiento sin sobreingeniería

- **MVP con una única instancia:** base SQL persistente ya usada por el proyecto y worker en el mismo servicio; verificar bloqueo/transacciones del volumen donde vive.
- **Varias réplicas / workers / necesidad estricta de alta disponibilidad:** PostgreSQL con reclamación transaccional y workers independientes; Redis/otra cola externa solo si hay razón medida.
- **No** escribir un archivo `queue.json` concurrentemente como mecanismo central.
- **No** usar SQLite directamente sobre un montaje de objetos sin verificar semántica POSIX, `fsync` y locking: puede romperse. Si el Space solo dispone de disco efímero, elegir una base realmente persistente externa.

---

## 11. Motor de ejecución duradero: comportamiento exacto

### 11.1. Ciclo de vida de una tarea

```text
PENDING
  -> comprobar dependencias y permisos
  -> READY
  -> CLAIMED (lease + worker_id + attempt_id)
  -> RUNNING
  -> CHECKPOINT (persistir antes/después de efectos externos)
  -> VERIFYING (V1/V2/V3)
  -> SUCCEEDED  /  FAILED / WAITING_APPROVAL / NEEDS_RECONCILIATION
```

**Regla:** el worker reclama la tarea con una transición **atómica**, no con `SELECT` seguido de `UPDATE` sueltos. `claim`, `lease`, `heartbeat` y `release` deben ser transaccionales.

### 11.2. Planificador (pseudocódigo de referencia)

```python
def schedule_tick(queue_id, worker_id, now):
    q = db.get_queue_for_update(queue_id)
    if q.status not in {"queued", "running"}:
        return
    if q.deadline_at and now >= q.deadline_at:
        db.expire_or_pause_with_event(q)
        return

    tasks = db.get_tasks_and_dependencies(queue_id)
    ensure_dag_valid(tasks)
    db.mark_blocked_or_skipped_by_failed_dependencies(tasks)

    free_slots = q.concurrency - db.running_slots(queue_id)
    for task in select_ready_tasks(tasks, free_slots):
        if not permissions_still_valid(task):
            db.block_task(task, "PERMISSION_REQUIRED")
            continue
        if not resource_locks_available(task):
            continue
        attempt = db.claim_task_atomically(task, worker_id, lease_seconds=120)
        if attempt:
            worker.dispatch(attempt)  # ejecución y logs fuera de transacción
```

```python
def execute_attempt(attempt):
    # Este ejemplo es CONTRATO de comportamiento, no código listo para copiar.
    assert belongs_to_authorized_run(attempt)
    renew_lease_periodically(attempt)
    assert_checkpoints_and_approvals(attempt)
    resolve_attachments_at_execution_time(attempt)
    tool = registry.resolve_allowed_tool(attempt)
    outcome = tool.call(
        input=render_typed_inputs(attempt),
        idempotency_key=attempt.idempotency_key,
        timeout=attempt.timeout_seconds,
    )
    persist_result_or_reconciliation_state(outcome)
    verify_v1_v2_v3_if_required(attempt)
    finalize_state_and_append_event_atomically(attempt)
```

No ejecutar código externo durante una transacción larga. Tiempos de red, rate limits y errores deben manejarse fuera del bloqueo de la DB.

### 11.3. PostgreSQL (cuando haya varios workers)

Ejemplo de patrón de reclamación transaccional:

```sql
WITH chosen AS (
  SELECT id FROM queue_tasks
  WHERE queue_id = :queue_id AND status = 'ready'
  ORDER BY position
  FOR UPDATE SKIP LOCKED
  LIMIT 1
)
UPDATE queue_tasks AS t
SET status = 'claimed', claimed_by = :worker_id,
    lease_until = :lease_until, updated_at = :now
FROM chosen
WHERE t.id = chosen.id
RETURNING t.id, t.task_json;
```

La creación del `attempt` y la reserva de recursos deben ocurrir en **la misma transacción**; la muestra no las implementa. En SQLite de instancia única, usar transacción `BEGIN IMMEDIATE` y actualizaciones condicionales; **no** copiar `FOR UPDATE SKIP LOCKED` a SQLite.

### 11.4. Lease, heartbeat y recuperación

- Worker publica `heartbeat` mientras la tarea está activa.
- Si el lease vence, pasar a `needs_reconciliation` cuando pudo haber efecto externo; **no** reintentar a ciegas.
- Reconciliar por `idempotency_key`, commit SHA, identificador remoto de operación o resultado consultable.
- Si operación es idempotente/solo lectura, podrá reintentarse tras verificar.
- Evitar prometer «exactly once» en integraciones externas que no ofrecen idempotencia. Objetivo: **at-least-once controlado + deduplicación/reconciliación**.
- Pausa y cancelación cooperativas entre pasos; una llamada de red en curso puede no poder detenerse físicamente.

### 11.5. Pasar outputs a la tarea siguiente

No evaluar expresiones arbitrarias. Construir un resolvedor de bindings tipado:

```json
{
  "input_bindings": [
    {"from_task_id": "T02", "output_key": "audit_report", "as": "previous_audit"},
    {"from_task_id": "T03", "output_key": "diff_artifact", "as": "approved_diff"}
  ]
}
```

Comprobar dependencia, tipo, existencia y permiso antes de resolver cada binding. Si falta una salida, bloquear con error claro. Al modelo se entrega un contexto acotado con referencias al resultado, no 50 transcripciones acumuladas sin límite.

### 11.6. Modo chat y salida

- **No publicar cada instrucción de la cola como si el usuario la hubiera enviado manualmente.** Mostrar en el chat un mensaje de control de ejecución y tarjetas de resultados, con enlaces a cada tarea.
- Permitir opcionalmente publicar el resumen final en el chat; conservar el transcript original y trazabilidad de respuestas del modelo.
- Si el chat tiene streaming, enlazar sus eventos al `task_id` y al `run_id`.
- Tool calls y respuestas no se mezclan entre tareas paralelas.
- Al acabar: informe con tareas realizadas, bloqueadas, errores, permisos pendientes, evidencia y próximos pasos.

---

## 12. Actualización en tiempo real y persistencia de UI

### SSE recomendado para notificaciones de cola

- Publicar `queue.created`, `task.added`, `task.started`, `task.progress`, `task.output`, `task.verification.completed`, `task.failed`, `queue.paused`, `queue.completed`, `approval.requested`.
- El frontend reconecta automáticamente y usa `event_id`/cursor (`Last-Event-ID` si la autenticación y la biblioteca lo permiten).
- Autenticación con sesión segura/cookie o streaming `fetch` que permita cabeceras; **no poner token privado en la URL del `EventSource`**.
- Si SSE falla: `GET .../events?after=N` con backoff y reconciliación de snapshot.
- Al recuperar tras cerrar la app: traer snapshot actual del backend; luego aplicar eventos desde cursor, ignorar duplicados.
- Estado local por cola, cache del chat, scroll y borradores separados.
- El usuario puede apagar/cerrar visualmente el panel sin afectar al worker; advertir si la infraestructura no está disponible.

**No inventar un servicio WebSocket adicional si el chat ya tiene una conexión suficiente** y admite eventos tipados; SSE es una opción simple, no un requisito de duplicación.

---

## 13. Watchdog de 10 minutos a 48 horas

### 13.1. Ventana de Watchdog

Dentro de `Configuración -> Watchdog`:

```text
[ ] Activar Watchdog
Duración: [10 min] -- [30 min] -- [1 h] -- [6 h] -- [12 h] -- [24 h] -- [48 h]
Heartbeat: [30 s ▼]         Sin progreso: [10 min ▼]
Acción ante estancamiento: [Pausar y avisar ▼]
Checkpoint: [Cada tarea ▼]  Reintentos: [Hasta 3 ▼]
Límite: [tokens] [llamadas] [coste] [duración]
Al vencer: [Pausar] [Finalizar tareas completadas] [Solicitar aprobación]
[Guardar perfil] [Probar vigilancia] [Activar]
```

- `10 min` y `48 h` son **parámetros**, no garantías de disponibilidad de ejecución.
- Mantener tiempos de inicio, deadline UTC, último progreso, worker activo, task_actual, heartbeat, lease e incidentes.
- Diferenciar `sin progreso` de `tarea larga pero saludable`.
- Distinguir watchdog de usuario (monitoreo) de TTL del worker (rescate de tareas colgadas).
- Nunca usar un LOOP de llamadas al LLM solo para esperar que pase el tiempo.

### 13.2. Hugging Face Spaces: limitación crucial

El **disco por defecto del Space es efímero** y su contenido puede desaparecer con reinicios/paradas; el sistema puede dormirse o reiniciarse según su configuración. Una promesa de `48 h continuas` **no es fiable** si el worker depende de un Space suspendido. Para hacerlo real, exigir:

1. Base de datos duradera, fuera de disco efímero (o volumen con semántica DB realmente adecuada).
2. Worker ejecutado en infraestructura disponible durante la ventana deseada; si el Space se suspende, runner siempre encendido o planificador externo que despierte/continúe de forma legítima.
3. Reconciliación tras reinicio y exposición en UI de `active`, `degraded`, `offline`, `recovering`.
4. Gestión de coste, cuotas del proveedor y límites de duración.

**Prohibido afirmar «funciona 48 h» con una prueba de cinco minutos.** Ejecutar prueba de persistencia y reportar el tiempo realmente ensayado.

### 13.3. Estrategia en dos niveles

- **Modo económico/simple:** 1 Space/servicio activo + DB duradera + worker con cola, sin alta disponibilidad; recuperar cuando vuelve.
- **Modo fiable 24–48h:** backend del chat + DB duradera + runner/worker que no dependa de pestañas ni suspenda inesperadamente, con supervisión. No implementar esta variante hasta que el usuario la solicite o se demuestre necesaria.

---

## 14. Seguridad y límites de autorización

### 14.1. Permisos

- Todas las rutas comprueban usuario, `chat_id`, `queue_id`, `project_id` y ownership del archivo.
- Auth del panel no equivale a permiso de escritura en GitHub, HF o infraestructura.
- Skills y tools requieren allowlist; nunca elegir automáticamente nuevas tools por texto del prompt.
- No permitir HTTP arbitrario (SSRF), paths fuera de workspace, inyección de `../`, lectura de secretos o ejecución por instrucciones contenidas en adjuntos.
- Tratar archivos/mensajes del chat como **datos no confiables**: no elevan permisos ni reemplazan instrucciones del usuario.
- Revisar límites de tasa, tamaño de prompt, número de adjuntos, uso de tokens y gasto total.
- `DELETE`, `rollback`, `push`, `deploy`, `secrets`, `permissions`: confirmación de acción concreta con resumen/diff; que se pueda rechazar.

### 14.2. Escritura quirúrgica y rollback

Para tareas de modificación de código:

1. Capturar repo/rama/commit SHA **real** y estado limpio o cambios existentes.
2. Identificar archivos/fragmentos autorizados antes de editar.
3. Preparar diff pequeño y verificable; no sobrescribir cambios ajenos.
4. Crear checkpoint con artefacto del diff y pruebas.
5. Aplicar solo tras permiso necesario.
6. Releer estado remoto antes de commit; detectar conflictos.
7. Ejecutar V1, V2, V3; persistir resultados.
8. Si falla: detener y proponer corrección; un rollback automático solo si existe autorización expresa y se demuestra que afecta exclusivamente a cambios propios.
9. `git revert` específico/PR compensatorio cuando proceda; **evitar `git reset --hard` y `force push` automáticos**.

### 14.3. Secretos y auditoría

- Secrets solo en vault/env seguro del backend; ni prompts, ni HTML, ni exportaciones, ni logs completos.
- Censurar tokens, credenciales, URLs firmadas y payloads sensibles.
- Auditoría de quién creó/ordenó/inició/aprobó/canceló.
- Logs estructurados con retención, permisos de lectura y correlación `run_id/task_id/trace_id`.
- Si se usan modelos externos, enviar solo datos autorizados para la tarea; explicar antes de compartir archivos confidenciales.

---

## 15. Frontend: componentes que Grok debe localizar o añadir

**Primero hacer inventario** de compositor, selector de archivos, messages, provider/store y componente de tools. Reutilizar estilos/tokens del chat.

Árbol ilustrativo **solo si el frontend es React**:

```text
Chat existente
├─ ChatComposer (reutilizado, añadir acciones cola)
├─ AttachmentPicker (reutilizado)
├─ SkillSelector (reutilizado/adaptado)
└─ TaskQueueControl [nuevo, componente pequeño]
   ├─ TaskQueueDrawer
   │  ├─ QueueHeader
   │  ├─ QueueTaskList / QueueTaskCard
   │  ├─ QueueDAGView
   │  ├─ QueueAttachmentsTab
   │  ├─ QueueSkillsToolsTab
   │  ├─ QueueActivityTab
   │  ├─ QueueSettingsTab
   │  └─ QueueActionBar
   ├─ TaskEditorDialog
   ├─ QueueApprovalDialog
   └─ TaskQueueStatusChip
```

Hooks/servicios ilustrativos: `useQueueDraft`, `useQueueEvents`, `useQueuePermissions`, `taskQueueApi`; **nunca duplicar** clientes de auth/chat existentes. API tipada y tests de contratos.

### Estándares de usabilidad

- Sin botón flotante que tape `Enviar`, `Adjuntar` o el teclado.
- Mínimo de 44 × 44 px de objetivo táctil; navegación con teclado, focus visible, labels y texto de estados.
- Reordenamiento usable sin arrastrar; soporte de lector de pantalla.
- Scroll independiente y restauración de posición.
- Confirmación para perder borrador, cancelar ejecución o borrar tareas con dependientes.
- Estado optimista solo para cambios recuperables; si backend rechaza una edición, revertir visualmente y explicar.
- Responsive 320 px a escritorio amplio; contrastes consistentes con tema blanco/azul y dark mode solo si ya existe.
- No montar múltiples listeners SSE por render ni crear fugas de memoria en tabs.

---

## 16. Backend: archivos propuestos, mínimos y condicionales

Grok **no debe crear archivos por inercia**. Si existen funciones equivalentes, ampliar las actuales.

| Responsabilidad | Opción mínima si no existe | Lo que debe conservar |
|---|---|---|
| Esquemas | `task_queue_models.py` | modelos actuales de chat/tool |
| Rutas API | `task_queue_routes.py` | auth, middlewares, endpoint chat |
| Repositorio DB | `task_queue_store.py` | DB/migraciones existentes |
| Motor | `task_queue_engine.py` | router/harness y sus contratos |
| Worker | `task_queue_worker.py` | ciclo de vida del servicio |
| API frontend | `taskQueueApi.ts` | cliente HTTP del chat |
| Drawer UI | `TaskQueueDrawer.tsx` | estilos y contextos existentes |
| Tests | `test_task_queue_*.py`, UI tests | suites de regresión |

**Objetivo MVP:** un módulo API, un módulo de persistencia, un motor/worker y unos pocos componentes UI. Evitar microservicios nuevos, Redis obligatorio, micro-kernel separado o múltiples stores si un solo servicio resuelve el caso.

### 16.1. Invariantes del backend

- `max_tasks=50` validado en servidor incluso ante peticiones simultáneas.
- Cola y revisiones se guardan con transacción atómica.
- Reintentos de `POST /start` con misma `Idempotency-Key` devuelven el **mismo run**, no dos.
- Prohibida ejecución si la cola está inválida o con permiso vencido.
- Prohibidos `PUT order` que produzcan referencias inconsistentes.
- Las skills se validan de nuevo inmediatamente antes de ser llamadas.
- El trabajador jamás depende de estado exclusivo del navegador.
- El usuario puede obtener diagnóstico si se desconecta el worker.

---

## 17. Ejecución segura frente a errores

| Situación | Comportamiento esperado |
|---|---|
| Límite 50 | rechazar 51, mantener las 50 |
| Pérdida de conexión móvil | cola continúa si worker activo; UI reconecta |
| Recarga navegador | recuperar snapshot/eventos sin duplicar tareas |
| Reinicio backend | estado duradero + conciliación de intentos abiertos |
| HF Space suspendido | marcar degradado; no fingir continuidad |
| Archivo eliminado/vencido | bloquear tarea y solicitar sustitución |
| Skill desactivada | bloquear antes de ejecutar; indicar razón |
| Dependencia falla | aplicar `on_failure`; no saltar silenciosamente |
| Ciclo en DAG | rechazar antes de iniciar |
| Modelo devuelve `finish_reason=length` | salida incompleta, continuación acotada o error |
| Timeout de llamada con efecto externo | reconciliar, no duplicar acción |
| Doble clic en Iniciar | una sola ejecución mediante idempotencia |
| Cancelar mientras llama un servicio | cancelación cooperativa + estado pendiente de conciliación |
| No pasan V1/V2/V3 | tarea FAIL/NO_VERIFICADO; no aprobar |
| Push en rama modificada por otra persona | detectar conflicto, parar, presentar diff actualizado |
| Presupuesto agotado | pausa y petición de autorización; no gastar más |

---

## 18. Panel de métricas y observabilidad

Mostrar por cola y por tarea:

- `Total 50`, pendientes, ejecutándose, verificando, aprobadas, fallidas, bloqueadas.
- Progreso **ponderado por tareas completadas** y opcionalmente por pasos; la ETA es una estimación, no garantía.
- Tiempo ejecutado, tiempo detenido, último progreso y deadline.
- Modelo/skill/tool usados realmente por intento.
- Tokens/coste real cuando lo informa el proveedor; «no disponible» si no hay datos. Presupuesto configurado.
- Retries, transiciones, verificaciones, hash/checkpoint, commit SHA, artefactos y alertas.
- Botones de exportar `bitacora.md`, `state.json`, `handoff.md`, `resultado_final.md` **solo si esos artefactos se generan de verdad**.
- Logs con filtrado por `task_id`, severidad, timestamp y correlación.

---

## 19. Plan de implementación para Grok — sin romper el chat

### Fase 0 — Auditoría de lectura obligatoria

1. Confirmar repositorio/rama/SHA y los commits recientes; leer instrucciones locales del proyecto.
2. Enumerar archivos de frontend/chat, componentes del compositor/adjuntos/skills, API chat/router y plugins.
3. Inspeccionar auth, contratos API, manejo de streaming, persistencia y dónde corren worker/Space.
4. Inventariar qué mecanismos ya existen: tareas, watchdog, eventos, habilidades, vault, historial, MCP, adjuntos y temas visuales.
5. Entregar tabla: `FUNCIONALIDAD | EXISTE/NO EXISTE | archivo:línea | se reutiliza/cambio mínimo`.
6. Crear una lista corta de gaps comprobados. **No implementar lo que ya existe**.

### Fase 1 — Contratos y datos

- Documentar tipos de cola/tarea y transiciones; elegir DB persistente según despliegue real.
- Añadir migración, validación de 50 tareas, DAG, permisos y test de colisiones.
- Tests de backend antes de wiring.

### Fase 2 — UI sin afectar flujo normal

- Añadir chip/botón Cola al compositor actual.
- Implementar drawer móvil/escritorio, lista, alta/edición/borrado/reordenamiento y contador.
- Conectar selector actual de archivos y selector real de skills.
- Comprobar tema blanco/azul, safe area, teclado y accesibilidad.

### Fase 3 — Cableado funcional de extremo a extremo

- Conectar UI -> endpoints autenticados -> DB -> motor -> router existente -> plugins solo por HTTP cuando corresponda -> respuesta al chat.
- Primero una tarea real **solo lectura**. Después dos tareas encadenadas con output binding.
- Añadir eventos/stream o reutilizar el canal actual de notificaciones.

### Fase 4 — DAG y ejecución de 50

- Añadir dependencias, scheduler, claim atómico, prioridad, reglas de fallo, locks y límites de concurrencia.
- Probar 50 tareas reales de bajo coste en entorno de test; no usar 50 llamadas costosas sin permiso.
- Añadir importación/exportación de colas.

### Fase 5 — Skills, validaciones y permisos

- Enlazar skill/tool catalog real, switches por cola/tarea y comprobación de permisos.
- Activar flujo de aprobación de acciones sensibles.
- Añadir verificaciones V1–V3 con evidencias.

### Fase 6 — LOOP + watchdog + recuperación

- Añadir checkpoints, leases, heartbeat, pausas/reanudaciones, límites de duración y contexto compacto.
- Ensayar reinicio real del worker y restauración sin doble efecto externo.
- Probar escenarios de suspensión del Space/infraestructura y mostrar limitación real.

### Fase 7 — Auditoría forense y regresión

- Verificar cambios línea por línea y diffs quirúrgicos; asegurar que ninguna ruta anterior del chat fue rota.
- Revisar rendimiento de móvil, cierres de ventana, tabs, teclado, SSE, auth y secretos.
- Ejecutar tests, pruebas de integración y E2E; repetir tres capas de verificación.
- Commit con SHA, registro de archivos tocados, evidencia y reporte PASS/FAIL/NO VERIFICADO.

**Regla de trabajo:** después de cada fase funcional, correr pruebas del chat normal y guardar un checkpoint. Si aparece una regresión, corregir el cambio mínimo; no reescribir toda la UI.

---

## 20. Matriz de pruebas de aceptación

| ID | Prueba | Esperado |
|---|---|---|
| Q01 | Abrir/cerrar Cola con chat vacío | no altera chat normal |
| Q02 | Crear tareas 1 a 50 | se guardan y numeran correctamente |
| Q03 | Intentar tarea 51 | 422 y ninguna pérdida de datos |
| Q04 | Reordenar por drag en Android | orden guardado tras reload |
| Q05 | Reordenar por botones accesibles | mismo resultado, sin drag |
| Q06 | Añadir mensaje actual como tarea | prompt intacto, no enviado aún |
| Q07 | Anclar archivo del chat a T02 | reutiliza mismo ID/permisos |
| Q08 | Anclar un archivo a todas | se hereda, sin copias binarias innecesarias |
| Q09 | Eliminar/invalidar archivo anclado | tarea bloqueada con mensaje claro |
| Q10 | Activar skill existente en T05 | invocación real + registro |
| Q11 | Skill inexistente/off | bloqueo, no simulación |
| Q12 | Ejecutar T01 -> T02 con output binding | T02 recibe solo output autorizado |
| Q13 | Crear ciclo T01 -> T02 -> T01 | `INVALID_DAG` |
| Q14 | Tarea paralela sobre el mismo recurso | lock impide doble escritura |
| Q15 | Doble clic Iniciar | un solo run/attempt |
| Q16 | Pausa/reanudación antes del siguiente paso | estado persistente coherente |
| Q17 | Cancelación durante llamada externa | conciliación, sin falso éxito |
| Q18 | Reload durante ejecución | rehidrata snapshot y cursor |
| Q19 | Desconexión y reconexión SSE | no duplica eventos |
| Q20 | Reiniciar servidor con tarea activa | recupera/reconcilia sin doble efecto |
| Q21 | `finish_reason=length` | incompleto, no PASS automático |
| Q22 | Fallar verificación V2 | FAIL/NO_VERIFICADO sin completar |
| Q23 | Intentar tool no permitida | denegación registrada |
| Q24 | Operación de escritura sin aprobación | espera, no escribe |
| Q25 | Conflicto de edición simultánea | 409 y UI permite resolver |
| Q26 | Presupuesto o deadline vencido | suspensión segura |
| Q27 | Exportar/importar JSON | misma estructura y validaciones |
| Q28 | Limpiar y cerrar panel durante run | run no se elimina |
| Q29 | Móvil, teclado y 320 px | no tapa controles ni rompe scroll |
| Q30 | Auditoría de secretos | ningún token en cliente/log/export |
| Q31 | Chat tradicional con Cola OFF | mismas funcionalidades previas |
| Q32 | Harness remoto no disponible | retry/backoff y estado correcto |
| Q33 | 50 tareas con dependencias mixtas | sin pérdidas ni duplicados |
| Q34 | Watchdog detecta sin progreso | alerta/pausa según política |
| Q35 | Duración 10m / 48h | configuración persistida; solo declarar verificadas las horas realmente probadas |

### 20.1. Tres pasadas mínimas de prueba

- **Pasada A — unitarias:** API/schema/DAG/50/idempotencia/permisos.
- **Pasada B — integración:** DB + cola + router/harness/skills + eventos + reinicio.
- **Pasada C — UI/E2E:** Android/escritorio, archivos del chat, cola de 50, uso normal del chat, accesibilidad.

No convertir 3 pasadas de tests en 3 ejecuciones costosas por tarea por defecto. Repetir específicamente las pruebas inestables para diagnosticar, no para ocultar flakiness.

### 20.2. Comandos guía, adaptar a la estructura real

```bash
# Ejemplos. Grok debe ubicar primero el gestor de dependencias y tests real.
python -m pytest -q
npm test -- --runInBand
npm run build
```

Si el proyecto no usa npm/Jest, estos comandos **no son obligatorios**. Reportar el comando ejecutado, exit code, evidencia y errores textuales sin secretos.

---

## 21. Criterios estrictos de entrega

**Para declarar PASS**, Grok debe poder demostrar todo lo siguiente:

- [ ] El botón Cola existe en el chat real, con modo OFF sin regresiones.
- [ ] Panel responsive, visual blanco/azul, adaptado al teclado móvil.
- [ ] Una cola persiste después de recargar; 50 tareas admitidas y 51 rechazada.
- [ ] Archivos se anclan usando el mecanismo real del chat.
- [ ] Skills reales aparecen, pueden habilitarse por tarea y se respetan sus permisos.
- [ ] Flujo secuencial y DAG funcionan con outputs reales.
- [ ] El backend ejecuta sin depender del navegador.
- [ ] Estados y eventos llegan al panel de manera auténtica.
- [ ] Pause/resume/cancel, retries, recuperación e idempotencia probados.
- [ ] LOOP/watchdog limitados por tiempo, progreso y presupuesto.
- [ ] V1, V2 y V3 tienen evidencia de pruebas reales.
- [ ] GitHub/HTTP/MCP/tool calling respetan permisos y arquitectura previa.
- [ ] No hay claves en frontend, commits, logs ni exportaciones.
- [ ] Se adjunta diff mínimo, SHA antes/después, pruebas ejecutadas y lista de pendientes.

**Si algún punto no pudo ensayarse, marcar `NO VERIFICADO` y explicar la limitación; no inventar éxito.**

---

## 22. Entrega y formato del informe de Grok

Grok debe terminar con:

```text
1. SHA BASE Y RAMA:
2. INVENTARIO REUTILIZADO (archivo:línea):
3. ARCHIVOS MODIFICADOS Y POR QUÉ:
4. ARCHIVOS CREADOS (justificación mínima):
5. CONTRATOS/ENDPOINTS REALES:
6. TABLA 50 TAREAS / ADJUNTOS / SKILLS:
7. RESULTADO PRUEBAS A, B, C (comandos, exit codes):
8. PRUEBAS MÓVIL Y REGRESIÓN CHAT:
9. SEGURIDAD Y APROBACIONES:
10. ESTADO WATCHDOG (duración REAL probada):
11. BUGS / GAPS QUE QUEDAN:
12. DIFF / COMMITS / SHA FINAL:
13. RESULTADO: PASS | FAIL | NO VERIFICADO
```

No declarar «conectado» por haber dibujado la ventana. Toda acción `Iniciar`, `Pausar`, `Adjuntar`, `Skill ON` y `Reanudar` debe llegar al backend funcional y verse reflejada en datos persistentes.

---

## 23. PROMPT EJECUTIVO — pegar en Grok junto a este archivo

> **ROL:** arquitecto y desarrollador senior de frontend/backend, auditor de regresión y responsable de pruebas.  
> **MISIÓN:** integrar en el chat existente la **CIT-50** definida en este Markdown. La imagen de referencia ilustra una bandeja de instrucciones, pero la solución debe superar ese comportamiento: hasta 50 tareas, dependencias DAG, anclajes usando archivos del chat, skills por tarea, panel avanzado, monitorización, LOOP, watchdog, verificaciones y recuperación real.  
> **RESTRICCIÓN 1 — NO REESCRIBIR:** audita primero el repositorio, rama y SHA; localiza el compositor, selector de adjuntos, selector de skills, backend, router, harness/plugins, vault, auth y tests. **Reutiliza todo lo que ya funcione.** Nada de cambiar la arquitectura ni crear un segundo chat.  
> **RESTRICCIÓN 2 — EDICIÓN QUIRÚRGICA:** modifica únicamente las rutas, componentes y fragmentos imprescindibles. Preserva el tema blanco minimalista con azul activo y la compatibilidad móvil. No alteres silenciosamente funciones existentes.  
> **RESTRICCIÓN 3 — RUTAS REALES:** los nombres de API y archivos de este documento son propuestas; contrástalos con código real antes de editarlos. Entre router y plugins usa solo HTTP si el proyecto conserva esa separación.  
> **RESTRICCIÓN 4 — SEGURIDAD:** tokens secretos exclusivamente en backend/vault; permisos por tarea y aprobación antes de escritura/despliegue/rollback. No repetir efectos remotos sin conciliación.  
> **RESTRICCIÓN 5 — PERSISTENCIA:** no simules una cola larga con `setTimeout` en el navegador. Usa BD durable, worker, checkpoints, idempotencia, reconexión y recuperación. Aclara la limitación si HF Spaces se suspende.  
> **RESTRICCIÓN 6 — TESTS:** aplica las tres capas V1/V2/V3, pruebas de cola de 50, crash/reload, adjuntos, skills, DAG, regresiones y móvil. Aporta evidencia real; si falta infraestructura, marca NO VERIFICADO.  
> **FLUJO DE TRABAJO:** Fase 0 auditoría, Fase 1 contratos, Fase 2 UI, Fase 3 cableado, Fase 4 DAG/50, Fase 5 skills y seguridad, Fase 6 LOOP/watchdog, Fase 7 pruebas. Guarda checkpoints por fase.  
> **ENTREGA:** código funcional y commit(s) verificables, resumen por archivo:línea, diagrama real del flujo, demostración de anclaje del chat y de 50 tareas, resultados de pruebas, limitaciones, SHA final y estado PASS/FAIL/NO VERIFICADO. **No detenerte en un mockup ni declarar éxito por simulación.**

---

## 24. Referencias técnicas que Grok debe verificar contra el entorno real

- **Hugging Face — persistencia de almacenamiento en Spaces:** https://huggingface.co/docs/hub/spaces-storage
- **FastAPI — BackgroundTasks y su limitación para trabajo pesado/distribuido:** https://fastapi.tiangolo.com/tutorial/background-tasks/
- **MDN — eventos SSE / EventSource y reconexión:** https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events/Using_server-sent_events
- **MCP — especificación versionada de transportes:** https://modelcontextprotocol.io/specification/
- **Especificación MCP (2025-11-25) — Streamable HTTP:** https://github.com/modelcontextprotocol/modelcontextprotocol/blob/main/docs/specification/2025-11-25/basic/transports.mdx
- **MCP draft (en evolución) — cambios a HTTP; negociar versión, no asumir:** https://modelcontextprotocol.io/specification/draft/changelog

Las referencias son guías para implementación. El repositorio existente y su versión instalada **mandan sobre cualquier ejemplo ilustrativo** de este archivo.

---

## 25. Resumen de la arquitectura mínima

```text
                       ┌────────────────────────────────────┐
                       │              CHAT UI               │
                       │ Compositor + Adjuntos + Skills     │
                       │ Botón COLA -> Panel CIT-50         │
                       └────────────────┬───────────────────┘
                                        │ API autenticada
                                        v
                       ┌────────────────────────────────────┐
                       │       API COLA + AUTH              │
                       │ CRUD / orden / DAG / eventos       │
                       └──────┬────────────────┬────────────┘
                              │                │
                              v                v
                     ┌────────────────┐  ┌─────────────────┐
                     │ DB PERSISTENTE │  │ WORKER / LOOP   │
                     │ runs/tasks/log │  │ watchdog/lease  │
                     │ refs/approvals │  │ checkpoints     │
                     └────────────────┘  └────────┬────────┘
                                                   │
                                                   v
                              ┌─────────────────────────────────────┐
                              │ ROUTER EXISTENTE / FICHAS/MODELOS  │
                              └─────────────────┬───────────────────┘
                                                │ HTTP autenticado
                                                v
                              ┌─────────────────────────────────────┐
                              │ PLUGINS / HARNESS / SKILLS / MCP    │
                              └─────────────────────────────────────┘
```

**Resultado correcto:** una sola experiencia de chat que puede preparar, visualizar, ejecutar y controlar 50 tareas enlazadas, con adjuntos del propio chat, selección real de skills y pruebas verificables; sin destruir ni duplicar los componentes existentes.
