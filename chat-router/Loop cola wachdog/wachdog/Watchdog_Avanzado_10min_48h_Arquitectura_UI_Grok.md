# WATCHDOG AVANZADO 10 MINUTOS–48 HORAS

**Especificación funcional, técnica y visual · guía de implementación para Grok**  
**Versión propuesta:** 1.0 · **Fecha:** 25 de octubre de 2026  
**Destino:** chat con router multimodelo, backend FastAPI en Hugging Face y frontend web/móvil, incluido Vercel.  
**Diseño visual:** blanco minimalista, líneas discretas, controles que cambian a azul cuando están activos; sin emojis ni iconografía de teclado.

> **Naturaleza del documento.** Esto es un diseño de implementación y un conjunto de contratos y ejemplos de programación; **no** afirma que estas funciones ya existan en el repositorio. Antes de modificar código, Grok debe inspeccionar el repositorio, identificar componentes reutilizables y documentar las rutas reales. No crear edificios nuevos ni reescribir componentes existentes por comodidad.

---

## 0. Resumen ejecutivo: qué construir exactamente

Crear un **Watchdog Studio**: ventana de control para lanzar, supervisar, pausar, reanudar, corregir y cerrar flujos de trabajo supervisados durante **10 minutos como mínimo y 48 horas como máximo**. La interfaz no ejecuta tareas: se limita a configurarlas y mostrar su estado. El backend conserva el estado y las ejecuta mediante pasos cortos, verificables y recuperables.

Cada watchdog tiene un **LOOP propio** (plan → ejecutar → observar → verificar → decidir → registrar → repetir/cerrar), tareas separadas, skills autorizadas, presupuesto, reloj, reglas, punto de control (`checkpoint`), bitácora e historial. Puede coordinar varias tareas en secuencia o en paralelo sin mezclar sus memorias, credenciales ni resultados.

**Tres modos distintos, no confundirlos:**

1. **Supervisión periódica:** observar cada X segundos/minutos durante una ventana máxima de 10 min a 48 h. No implica consumir tokens constantemente.
2. **Ejecución por pasos:** desarrollar un plan largo con pausas y `checkpoints`; cada paso tiene un límite breve y se reanuda desde el último estado durable.
3. **Vigilancia de condición:** verificar si cambió algo y actuar **solo cuando se cumpla una condición** previamente definida, con confirmación cuando implique efectos externos sensibles.

**Definición crucial:** «continuo durante 48 horas» significa que el **servicio de supervisión mantiene la responsabilidad durante toda la ventana**, no una única petición HTTP, ni una llamada LLM de 48 horas, ni un temporizador dentro del navegador. La continuidad real requiere infraestructura siempre activa o reanudación tras fallos, además de un almacén durable.

### Decisión recomendada

- **Vercel:** renderizar la UI web/móvil y, si ya existe, ofrecer su proxy de API; **no** ejecutar una llamada de 48 horas.
- **Edificio 1 — Router/Fichas (FastAPI):** autenticar, validar, ofrecer API y enrutar los trabajos al ejecutor. Conserva la arquitectura existente.
- **Edificio 2 — Plugins/Harness:** ejecutar acciones ya registradas mediante la frontera HTTP existente (`POST /plugins/{plugin}/call/{accion}`, autenticada). No importar plugins directamente desde el router.
- **Worker watchdog:** proceso/servicio liviano que recoge vencimientos de una base transaccional y ejecuta pasos pequeños. Puede compartir despliegue al principio, pero debe tener su ciclo de vida independiente de las solicitudes HTTP.
- **PostgreSQL:** estado operativo, colas de vencimientos, locks, eventos, checkpoints y versiones. **GitHub:** commits de código, configuración y snapshots finales, no un commit por latido. **HF Bucket:** opción para artefactos y bitácoras extensas, no sustituto directo de una base de datos transaccional.

---

## 1. Contrato de funcionamiento

### 1.1 Requisitos obligatorios

| ID | Comportamiento verificable |
|---|---|
| W01 | Duración editable de **10 a 2.880 minutos** (48 horas). |
| W02 | Inicio inmediato o programado; fin por fecha límite, condición, éxito, error irreversible o cancelación. |
| W03 | Ciclo configurable: frecuencia, tiempo máximo por paso, reintentos y backoff. |
| W04 | Cada watchdog contiene N tareas; cada tarea tiene estado, responsable lógico, skill, entrada, salida y checkpoint independientes. |
| W05 | Dependencias entre tareas declaradas en un DAG; ninguna tarea inicia hasta que sus prerequisitos terminen correctamente. |
| W06 | Permitir paralelismo solo entre tareas sin dependencias conflictivas y dentro de cuotas definidas. |
| W07 | Skills y herramientas **apagadas por defecto**; activación explícita por tarea, no acceso global implícito del modelo. |
| W08 | Todo cambio de estado es persistente; sobrevive cierre de ventana, reconexión y reinicio del worker. |
| W09 | Pausar, reanudar, detener y cancelar de forma verificable; cancelar evita nuevas acciones y las tareas cooperan con esa cancelación. |
| W10 | Historial de quién/qué/cuándo/por qué: eventos, versiones, decisiones, errores, artefactos y coste estimado. |
| W11 | Reintentos y duplicados controlados; no duplicar commits, publicaciones ni llamadas con efectos externos. |
| W12 | Pantalla responsive, usable táctilmente y accesible, con actualización sin recargar. |
| W13 | Perfiles de aprobación: lectura automática; escritura y acciones de impacto requieren reglas y autorización definida. |
| W14 | Protección contra gasto incontrolado: límite de llamadas, tokens, coste y tareas simultáneas. |
| W15 | Diagnóstico de pérdida de latido, worker inactivo, reloj vencido y tareas estancadas. |
| W16 | No exponer tokens en UI, modelos, prompts, logs, base de datos de eventos o GitHub. |
| W17 | Permitir editar borradores; en trabajos activos aplicar cambios mediante **revisión versionada**, nunca mutar silenciosamente un plan a mitad de un paso. |
| W18 | Evitar ciclos de dependencias; validar el grafo antes de activar. |
| W19 | Mostrar si se ejecuta realmente, si está esperando el próximo chequeo, o si el servidor está desconectado. |
| W20 | Registrar condición de cierre y resultado final verificable antes de marcar `COMPLETED`. |

### 1.2 Relojes: cuatro conceptos separados

- `window_duration_minutes`: duración total deseada: **10–2880 min**.
- `poll_interval_seconds`: intervalo entre inspecciones del scheduler (ejemplo: **5–30 s**). Este pequeño tick no invoca necesariamente ninguna IA.
- `task_interval_seconds`: frecuencia de comprobación de una tarea periódica (ejemplo: **60–3600 s**, editable según carga y límites del proveedor).
- `step_timeout_seconds`: tiempo máximo de un paso individual (ejemplo: **15–90 s**); nunca 48 horas.

**Ejemplo correcto:** watchdog de 36 horas + comprobación cada 10 min + paso HTTP máximo 45 s. La tarea duerme lógicamente entre comprobaciones; no mantiene conexión con el navegador ni con el modelo.

### 1.3 Estados

**Watchdog:** `DRAFT → SCHEDULED → ACTIVE ↔ PAUSED → COMPLETED | EXPIRED | FAILED | CANCELLED`.  
**Tarea:** `BLOCKED → QUEUED → RUNNING → WAITING → SUCCEEDED | FAILED | CANCELLED | TIMED_OUT`; `RUNNING → WAITING` si el paso detecta que aún no se cumple la condición.  
**Paso/attempt:** `PENDING → CLAIMED → SUCCEEDED | FAILED | ABANDONED`.

No igualar `PAUSED` con `CANCELLED`, ni `EXPIRED` con `COMPLETED`. No anunciar éxito por haber terminado el reloj.

---

## 2. Modelo LOOP y campos editables

El LOOP no es un prompt infinito. Es una **máquina de estados** gobernada por código. La LLM propone decisiones estructuradas que el backend valida antes de ejecutar.

### 2.1 Formulario de creación/edición

| Sección | Campo | Tipo | Regla / uso |
|---|---|---|---|
| General | Nombre | texto | 3–100 caracteres, obligatorio. |
| General | Objetivo | texto largo | Resultado deseado comprobable. |
| General | Descripción/contexto | Markdown | Contexto compartido, con tamaño máximo. |
| General | Plantilla | selector | Manual, supervisar, programar, resolver incidencias, GitHub, QA. |
| General | Prioridad | selector | Baja, media, alta; no habilita saltarse controles. |
| Tiempo | Duración total | deslizador + entrada | 10 min, 30 min, 1 h, 6 h, 12 h, 24 h, 48 h y valor personalizado. |
| Tiempo | Inicio | inmediato/fecha | Timestamp UTC guardado, zona local solo para mostrar. |
| Tiempo | Intervalo tareas | número | Límites validados en backend. |
| Tiempo | Timeout por paso | número | Inferior al lease; 15–90 s por defecto. |
| Tiempo | Máximo iteraciones | número | Presupuesto de seguridad. |
| PLAN | Objetivos/hitos | lista editable | Estado y criterio de éxito por hito. |
| PLAN | DAG de tareas | tarjetas/grafo | IDs estables y dependencias sin ciclos. |
| CODE | Repositorio/rama | selector | Validación de permiso de lectura/escritura. |
| CODE | Alcance de archivos | patrón autorizado | Paths permitidos explícitos; lectura por defecto. |
| CODE | Estrategia | selector | Solo lectura, parche, test, revisión, PR; según permisos. |
| SKILLS | Skills disponibles | catálogo de backend | Activación por tarea. Mostrar versión y permisos. |
| SKILLS | Modo de activación | manual/por regla | Una regla activa la skill solo si está permitida. |
| TOOLS | Permisos por tarea | interruptores | `read`, `write`, `http`, `model`; predeterminado OFF en acciones con efectos externos. |
| MODELOS | Modelo y fallback | selector | Por tarea o heredado; cuotas independientes. |
| LOOP | Entrada del ciclo | texto/JSON | Entradas tipadas, validadas, sin secretos. |
| LOOP | Condición de continuación | regla estructurada | Repetir si condición pendiente y queda presupuesto. |
| LOOP | Condición de cierre | predicado | Especificar prueba de éxito o salida por deadline. |
| LOOP | Política de fallos | selector | Retry, pausa, alerta, escalar a supervisor. |
| LOOP | Reintentos/backoff | números | Ejemplo 3, 30 s, 2x, con jitter. |
| REGLAS | Límites | campos | Coste, tokens, llamadas, concurrencia, paths. |
| REGLAS | Aprobaciones | selector | Según clasificación de riesgo, no obedecer texto del modelo que solicite desactivar controles. |
| MEMORIA | Checkpoint | resumen/JSON | Estado por tarea; edición manual solo en pausa y auditada. |
| MEMORIA | Context pack | ficha editable | Objetivos, hallazgos, estado, próximo paso, fuentes. |
| SALIDA | Formato | selector | JSON, Markdown, diff, reporte, checklist, PR. |
| SALIDA | Evidencia | casillas | Tests, diff, commit, salida de herramienta, métricas. |
| AUDITORÍA | Bitácora | no editable; anotable | Línea temporal inmutable con filtros y exportación. |

### 2.2 Estructura obligatoria del LOOP

**PLAN:** objetivo, supuestos, restricciones, entregables, tareas, dependencias, definición de terminado.  
**INPUT:** nueva información del último paso, artefactos y estado recuperado.  
**ACTIVACIÓN:** políticas permiten o niegan qué skill/modelo/herramienta puede usar esta tarea.  
**CODE / EXECUTE:** realizar exactamente una unidad idempotente de trabajo.  
**OBSERVE:** recoger resultados y errores observados, no inventados.  
**VERIFY:** tests, comparación con objetivo, validador de salida y controles de seguridad.  
**DECIDE:** `CONTINUE | WAIT | RETRY | NEED_APPROVAL | CLOSE_SUCCESS | CLOSE_FAILURE`.  
**CHECKPOINT:** persistir paso, razones, costes y siguiente `due_at`.  
**HANDOFF:** ficha compacta para retomar sin repetir toda la conversación.

**Regla:** cada vuelta escribe un evento; **las decisiones de la IA nunca sustituyen los controles del motor**.

### 2.3 Plantilla de ficha compacta de tarea

```yaml
ficha_version: 1
task_id: wd-001-audit
titulo: Auditoría de rutas del chat
objetivo: Detectar llamadas HTTP rotas sin modificar archivos
restricciones:
  - solo_lectura
  - no_secretos
  - sin_escrituras_git
skills_permitidas: [systematic-debugging, verification-before-completion]
modelo_preferido: qwen-configurado-en-router
input_ref: artifact://input/audit-v1
hallazgos_ref: artifact://output/audit-partial-v3
checkpoint:
  ultimo_paso_confirmado: 3
  siguiente_paso: revisar_headers_HTTP
  intentos: 1
criterio_exito: 'entregar evidencia archivo:línea por cada hallazgo'
criterio_fallo: 'superar limite de presupuesto o permiso denegado'
estado: WAITING
```

La ficha no debe incluir PATs, cookies, credenciales, texto entero de logs ni datos sensibles.

---

## 3. Separar tipos de watchdog y sus tareas

### 3.1 Catálogo de supervisores (todos usan el mismo motor)

| Tipo | Detecta/realiza | Entrada | Reacción permitida |
|---|---|---|---|
| **Tiempo** | vencimientos y ausencia de progreso | deadline/intervalo | aviso, pausa o cierre. |
| **Estado** | salud de una API o servicio autorizado | endpoint previamente autorizado | registrar/alertar/escalar. |
| **GitHub** | nuevos commits, SHA, PR, checks | repo/branch/commit ref | observar, auditar; escribir solo con aprobación. |
| **HF Space** | estado del servicio y latidos | identificador permitido | observar; reiniciar/cambiar recursos solo bajo política explícita. |
| **Code QA** | plan de pruebas, diff y regresiones | repositorio y paths | verificar, crear reporte, opcional PR autorizado. |
| **LLM/Tokens** | fin prematuro, presupuesto, `finish_reason` | trazas del router | reintentar con reglas, pedir intervención. |
| **Dependencias** | espera de respuesta, job previo o artefacto | ID o señal | desbloquear siguiente tarea. |
| **Coste** | tokens, llamadas, tiempo y cuotas | registros de uso | frenar al llegar al tope. |
| **Integridad** | ausencia de heartbeat, duplicados, estados imposibles | eventos del motor | recuperación/alerta. |
| **Reporte** | consolidación de evidencias | artefactos validados | Markdown o ficha final, sin alterar fuentes. |

### 3.2 Independencia y coordinación

- **`watchdog_id`** identifica un proceso supervisado completo.
- **`task_id`** identifica una tarea concreta, sus permisos y memoria.
- **`run_id`** identifica una ejecución total de watchdog.
- **`attempt_id`** identifica cada intento corto de una tarea.
- **`skill_id`** identifica una capacidad registrada y versionada.
- **`correlation_id`** relaciona eventos que cruzan Router ↔ Harness ↔ respuesta.

Permitir `task B depends_on [A]`, `task C depends_on [A]` y `task D depends_on [B,C]`. B y C pueden ejecutarse en paralelo si las cuotas y conflictos de recursos lo permiten. Detectar ciclo A→B→A y **rechazar la activación**.

**Aislamiento:** `checkpoints`, presupuestos, archivos temporales, autorizaciones y resultado final por tarea. No crear «memoria global» de todos los watchdogs que mezcle resultados o permisos.

### 3.3 Ejemplo: flujo de programación sin sobrescrituras

```text
WD: Verificación de chat y router — ventana máxima 24 h
  T1: Leer estado de main/SHA              [read-only]
   ├─> T2: Auditar frontend                 [read-only]
   └─> T3: Auditar cableado backend         [read-only]
          T2 + T3 ─> T4: Comparar inconsistencias [analysis]
                          └─> T5: Proponer parche [draft]
                                      └─> T6: Esperar autorización [approval]
                                                  └─> T7: Cambios mínimos [write]
                                                              └─> T8: Tests y cierre [verify]
```

Si T6 no se aprueba, T7/T8 quedan bloqueadas. Si el usuario cancela o vence el reloj, se detienen las nuevas escrituras. El watchdog puede informar en qué quedó y preparar `handoff`.

---

## 4. Ventana Watchdog Studio: diseño exacto

### 4.1 Composición de escritorio

```text
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  WATCHDOG STUDIO           [Nuevo] [Plantillas] [Importar]     API●  Worker●        │
├───────────────────┬───────────────────────────────────┬─────────────────────────────┤
│  MIS WATCHDOGS    │  WD · Auditoría Router            │  INSPECTOR                  │
│  Buscar...        │  ACTIVO · 09:42:00 / 24:00:00    │  [General] [Reglas]         │
│  [Todos] [Activos]│  [Pausar] [Cancelar] [Editar]     │  Nombre                     │
│  [Pausados]       │  progreso 5 de 8 tareas          │  Duración   [24 h ▾]        │
│                   │  ┌─PLAN / DAG───────────────┐   │  Intervalo  [10 min]       │
│  WD Router   ACT  │  │ T1 ✓ ─┬─ T2 ✓          │   │  Skills     [+ Añadir]     │
│  WD HF      ESP   │  │       └─ T3 RUN ─ T4   │   │  Condición de cierre       │
│  WD QA      PAU   │  │                ↓         │   │  Presupuesto               │
│                   │  │           T5 → T6 → T7   │   │  [Guardar revisión]        │
│  [+ Nuevo]        │  └──────────────────────────┘   │                             │
│                   │ [Plan] [Tareas] [LOOP] [Logs]    │  ESTADO Y CONTROL           │
│                   │ [Skills] [Costes] [Handoff]     │  Heartbeat: hace 12 s       │
│                   │  Lista de tareas y evidencias   │  Próxima inspección: 10:00  │
├───────────────────┴───────────────────────────────────┴─────────────────────────────┤
│ Historial: 09:28 T3 started | 09:27 T2 verified | 09:26 T1 succeeded              │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

### 4.2 Composición en móvil

- **Cabecera fija:** nombre del watchdog, estado real, cuenta regresiva, menú de acciones.
- **Una columna:** resumen → tareas → pestañas; **sin** columnas minúsculas ni tabla desbordada.
- **Inspector** en panel inferior (`bottom sheet`) accesible con botón **Configurar**; se desliza y se cierra de forma explícita.
- **Barra inferior fija:** `Pausar/Reanudar`, `Ver LOOP`, `Tareas`, `Más`.
- **DAG**: en móvil sustituir grafo ancho por **lista jerárquica** de dependencias; la vista grafo es opcional.
- **Actualización:** reconectar al volver a la pantalla. Nunca asumir que sigue activo por una animación del cliente.
- **Tacto/accesibilidad:** objetivos táctiles ≥44×44 px como criterio de diseño; etiquetas de texto; indicadores por color **y** palabra; foco visible, `aria-live` para cambios relevantes.

### 4.3 Pestañas y contenido

**Resumen:** objetivo, fase, reloj, porcentaje de hitos verificados, próximos vencimientos, última actividad, cuotas y problemas.  
**Plan:** objetivos, dependencias, hitos, condiciones; editor con control de versiones.  
**Tareas:** tabla/tarjetas individuales: estado, progreso, prioridad, skill activa, próximo paso, consumo y acciones.  
**LOOP:** panel de «última vuelta»: `input → acción → salida → validación → decisión → checkpoint`.  
**Skills:** catálogo filtrable, permisos requeridos, versión, riesgo y activación por tarea.  
**Logs:** eventos paginados, filtros por `task_id`, severidad, tipo y periodo; sanitizados.  
**Costes:** uso medido y estimado; límites por watchdog y modelo.  
**Handoff:** resumen compacto estructurado, referencias de pruebas, tareas pendientes y motivo de cierre.  
**Configuración:** tiempos, política de errores, límites, aprobaciones, condiciones y exportación.

### 4.4 Botones y reglas de interacción

| Control | Acción backend | Deshabilitar cuando |
|---|---|---|
| **Nuevo** | crear borrador | sin permiso. |
| **Validar plan** | comprobar esquema, DAG, permisos y recursos | formulario inválido. |
| **Activar** | pasar a `ACTIVE` transaccionalmente | no validado/no autorizado. |
| **Pausar** | bloquear nuevas reclamaciones y solicitar cancelación cooperativa de trabajo en curso | terminal. |
| **Reanudar** | recomputar vencimientos y continuar checkpoints | vencido o recursos ausentes. |
| **Detener al acabar paso** | marcar `stop_requested`; no reclamar siguiente paso | terminal. |
| **Cancelar ya** | señal de cancelación; no iniciar nuevas acciones | terminal. |
| **Editar** | abrir borrador de nueva revisión | sin permiso. |
| **Guardar revisión** | CAS/version; aplicar solo entre pasos o tras pausa | conflicto de versión. |
| **Reintentar** | registrar nuevo intento del paso permitido | presupuesto/permiso agotado. |
| **Aprobar paso** | registrar actor + alcance + vigencia | falta autenticación. |
| **Exportar** | descargar resumen/versiones/bitácora redactada | datos sin permisos. |

**Confirmación fuerte** para acciones sensibles; no instalar un interruptor «autonomía total» que eluda aprobación, límite o permiso.

### 4.5 Paleta y sistema visual

| Elemento | Regla de diseño |
|---|---|
| Fondo | `#FFFFFF` / `#F8FAFC`. |
| Texto | `#0F172A`; secundario `#64748B`. |
| Bordes | `#E2E8F0`, radio 10–14 px. |
| Estado activo / switches | azul `#2563EB`; OFF gris; nunca depender solo del color. |
| Estado de riesgo | acento ámbar/rojo con etiqueta legible. |
| Tipografía | sistema (`system-ui`), pesos 400/600. |
| Elementos | márgenes generosos, divisores finos, sombras tenues; sin emojis. |
| Modo móvil | evitar modales que tapen pantalla; panel lateral pasa a hoja inferior. |
| Contraste | WCAG AA como meta; comprobar realmente con auditoría. |

### 4.6 Ejemplo de estructura React (con componentes existentes)

```tsx
// Contrato visual: no incluye autenticación ni cliente HTTP; reutilizar los existentes.
type WDStatus = 'DRAFT'|'SCHEDULED'|'ACTIVE'|'PAUSED'|
  'COMPLETED'|'EXPIRED'|'FAILED'|'CANCELLED';

type WatchdogSummary = {
  id: string; name: string; status: WDStatus;
  started_at?: string; deadline_at?: string;
  heartbeat_at?: string; tasks_done: number; tasks_total: number;
};

type Props = {
  items: WatchdogSummary[];
  selected?: WatchdogSummary;
  onSelect: (id: string) => void;
  onAction: (id: string, action: 'pause'|'resume'|'cancel') => Promise<void>;
};

export function WatchdogPanel({ items, selected, onSelect, onAction }: Props) {
  return (
    <section className="watchdog" aria-label="Gestión de Watchdogs">
      <aside className="watchdog__sidebar" aria-label="Mis Watchdogs">
        <h2>Watchdog Studio</h2>
        <nav aria-label="Seleccionar Watchdog">
          {items.map(w => (
            <button type="button" key={w.id} onClick={() => onSelect(w.id)}
              aria-current={selected?.id === w.id ? 'page' : undefined}>
              <span>{w.name}</span><span className="wd-state">{w.status}</span>
            </button>
          ))}
        </nav>
      </aside>
      <main className="watchdog__main">
        {!selected ? <p>Selecciona o crea un Watchdog.</p> : <>
          <header className="watchdog__heading">
            <div><h2>{selected.name}</h2><p role="status">{selected.status}</p></div>
            <div className="watchdog__actions">
              {selected.status === 'ACTIVE' &&
                <button type="button" onClick={() => void onAction(selected.id, 'pause')}>Pausar</button>}
              {selected.status === 'PAUSED' &&
                <button type="button" onClick={() => void onAction(selected.id, 'resume')}>Reanudar</button>}
              {['ACTIVE','PAUSED','SCHEDULED'].includes(selected.status) &&
                <button type="button" onClick={() => void onAction(selected.id, 'cancel')}>Cancelar</button>}
            </div>
          </header>
          <p>Hitos verificados: {selected.tasks_done} de {selected.tasks_total}</p>
          <p>Último latido: {selected.heartbeat_at ?? 'Sin datos'}</p>
          {/* Reutilizar tabs, forms, task cards y drawers del frontend actual. */}
        </>}
      </main>
    </section>
  );
}
```

```css
.watchdog { display:grid; grid-template-columns:minmax(220px,260px) minmax(0,1fr); min-height:60vh; background:#fff; color:#0f172a; }
.watchdog__sidebar { padding:20px; border-right:1px solid #e2e8f0; }
.watchdog__main { min-width:0; padding:20px; }
.watchdog__sidebar nav { display:grid; gap:8px; }
.watchdog button { min-height:44px; cursor:pointer; background:#fff; border:1px solid #e2e8f0; border-radius:10px; padding:8px 12px; color:inherit; }
.watchdog button:hover, .watchdog button[aria-current="page"] { background:#eff6ff; border-color:#2563eb; }
.watchdog button:focus-visible { outline:3px solid #2563eb; outline-offset:2px; }
.watchdog__heading { display:flex; justify-content:space-between; flex-wrap:wrap; gap:12px; }
.watchdog__actions { display:flex; gap:8px; flex-wrap:wrap; }
.wd-state { margin-left:8px; color:#2563eb; font-size:12px; font-weight:600; }
@media(max-width:720px) { .watchdog { display:block; } .watchdog__sidebar { border-right:0; border-bottom:1px solid #e2e8f0; padding:12px; } .watchdog__main { padding:14px; } }
```

Este es un **armazón visual ilustrativo**, no un reemplazo del frontend ya existente. Grok debe conectar la API autenticada y la vista real de tareas, LOOP y aprobaciones usando los componentes presentes.

---

## 5. Diez mejoras de nivel superior para la VENTANA

1. **Diseñador de flujos con dos vistas:** DAG arrastrable en escritorio y lista de dependencias en móvil; edición versionada, validación de ciclos en tiempo real.
2. **Línea del tiempo dual:** una barra para las 48 h máximas y otra para los pasos/latidos; mostrar pausas, esperas, errores y reanudaciones.
3. **Inspector contextual por tarea:** al seleccionar T3, ver solo su plan, skills, archivos permitidos, checkpoint, presupuesto y resultados, sin mezclar T1/T2.
4. **Simulador “antes de ejecutar”:** previsualizar orden de tareas, coste máximo, permisos solicitados, conflictos de dependencias y estimaciones **orientativas**.
5. **Panel de permisos transparente:** interruptores independientes por skill y por tarea; mostrar por qué una acción está bloqueada y qué autorización falta.
6. **Monitor de salud verdadero:** tres señales independientes `API`, `worker`, `persistencia`; diferenciar “sin datos”, “desconectado”, “en espera” y “ejecutando”.
7. **Centro de incidentes:** errores agrupados por causa raíz, paso, proveedor; reintento selectivo, sin multiplicar acciones de escritura.
8. **Historial reproducible:** seleccionar un evento y ver input saneado, plan versión N, diff, evidencia y decisión; exportación PDF/Markdown opcional.
9. **Editor experto/progresivo:** modo básico con 6 campos y pestaña avanzada con las políticas completas; JSON/YAML validado de ida y vuelta.
10. **Comparador de revisiones/handoff:** diferencias entre planes v1/v2, justificación del cambio, estado recuperable y checklist de lo que falta.

**Extras UX recomendados:** atajos de teclado documentados; filtros guardados; búsqueda en tareas y bitácora; guardado de borrador; duplicación de plantillas; confirmación de cancelación; indicador de datos obsoletos; configuración por paneles; vista oscura solo si el producto ya la soporta; configuración exportable/importable sin secretos.

---

## 6. Diez mejoras de nivel superior para la PROGRAMACIÓN

1. **Orquestación durable y reanudable:** la operación de 48 h es un conjunto de pasos cortos registrados, no un proceso monolítico.
2. **Leases + fencing tokens:** un worker reclama una tarea por tiempo definido y cada adquisición incrementa una generación; respuestas tardías de workers viejos no pueden sobrescribir la nueva.
3. **Máquina de estados formal:** transiciones válidas comprobadas en código y base de datos; todos los botones invocan la misma lógica de dominio.
4. **Idempotencia para efectos externos:** clave idempotente por paso, `operation_id` durable y reconciliación al reiniciar; nunca confiar en “exactly once” para HTTP/Git.
5. **Plan DAG con colas por prioridad y límites:** fairness por watchdog, `max_concurrent_tasks`, presupuesto y permisos; evitar que una tarea ruidosa ocupe todos los recursos.
6. **Skills como capacidades registradas:** nombre, versión, entradas tipadas, permisos, timeout, riesgo, endpoint fijo; cero ejecución de código arbitrario a partir del prompt.
7. **Context pack incremental:** checkpoint estructurado de cada tarea más referencias de artefactos; resumir solamente cuando cruza un umbral, evitando volver a enviar el chat entero.
8. **Observabilidad por correlación:** eventos estructurados y `trace_id` cruzan UI → router → harness → herramientas; métricas de backlog, error, latidos, p95 y coste.
9. **Política automática de recuperación:** backoff exponencial con jitter, `Retry-After`, circuit breaker por proveedor, dead-letter, escalación y corte por presupuesto.
10. **Cambios controlados mientras está activo:** control de versiones y CAS (`If-Match`/`version`), migración entre pasos, compatibilidad de esquema, rollback seguro de configuración.

**Opcionales si se justifica con carga real:** Temporal como motor durable; cola Redis + workers; event sourcing completo; webhooks firmados; trazas OpenTelemetry; aislamiento más estricto de ejecutores; segundo worker redundante. No instalar todo desde el primer día.

---

## 7. Arquitectura de producción mínima, compatible con dos edificios

```text
  WEB / MÓVIL (Vercel o frontend actual)
   ├─ Watchdog Studio: formulario, DAG, monitor, bitácora
   └─ HTTPS autenticado
                 │
                 ▼
  EDIFICIO 1 — FASTAPI ROUTER EXISTENTE
   ├─ /watchdogs (CRUD / activar / pausar / cancelar / estado)
   ├─ validador de DAG, permisos y cuotas
   ├─ catálogo de skills (referencias, NO ejecución)
   └─ Postgres: workspaces, tasks, attempts, events, checkpoints
                 ▲
                 │ transacciones y polling ligero
                 ▼
  WATCHDOG WORKER / SCHEDULER (sin dependencias de navegador)
   ├─ claim con lock + lease + fence
   ├─ prepara ficha/entrada mínima
   ├─ llama acción permitida por HTTP
   ├─ valida resultado + checkpoint + presupuesto
   └─ persiste resultado y programa próximo due_at
                 │ HTTPS autenticado
                 ▼
  EDIFICIO 2 — PLUGIN HOST / HARNESS EXISTENTE
   └─ POST /plugins/{plugin}/call/{accion}
       ├─ tools/skills ya instaladas y autorizadas
       └─ respuesta estructurada con evidencia

  GitHub: código y entregables versionados / HF Bucket: logs largos/artefactos
```

### 7.1 Restricciones de infraestructura verificadas

**Hugging Face Spaces:** el disco efímero se pierde con reinicios; la documentación recomienda volúmenes tipo **Storage Bucket** para archivos persistentes. Un Space gratuito puede entrar en reposo tras inactividad; **no garantizar 48 h continuas** si la instancia duerme o se reconstruye. Usa alojamiento de worker siempre activo si necesitas continuidad estricta y recupera trabajos desde la base después de un reinicio. Documentación: [Spaces Storage](https://huggingface.co/docs/hub/spaces-storage), [Spaces Overview](https://huggingface.co/docs/hub/spaces-overview), [GPU Spaces/sleep](https://huggingface.co/docs/hub/spaces-gpus).

**Vercel:** sus cron jobs disparan Functions; no sostienen un proceso durante 48 h. En el plan Hobby, la frecuencia cron permitida es **una vez al día**; en Pro/Enterprise, **hasta una vez por minuto** según documentación de 2026. Su frecuencia y duración están sujetas a límites de Functions y precisión temporal. No usar un cron de Vercel Hobby cada 10 minutos como único scheduler. Documentación: [Cron Usage & Pricing](https://vercel.com/docs/cron-jobs/usage-and-pricing), [Managing Cron Jobs](https://vercel.com/docs/cron-jobs/manage-cron-jobs).

**Navegador móvil:** pestañas en segundo plano pueden reducir o suspender temporizadores; `setInterval` y WebSocket de la UI no son reloj autoritativo. Documentación: [MDN Page Visibility API](https://developer.mozilla.org/en-US/docs/Web/API/Page_Visibility_API).

**GitHub:** respetar límites principales y secundarios, gestionar `403/429`, `Retry-After` y encabezados de rate limit. Documentación: [GitHub REST rate limits](https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api).

### 7.2 Cómo desplegar sin alterar la arquitectura actual

1. **Inspeccionar primero** las rutas HTTP y autenticación existentes en `mvp/`, `plugins/`, frontend y configuración del Space; confirmar rama/SHA, sin editar.
2. Colocar **API/controlador del watchdog** dentro del Router, sin romper `/chat` ni las rutas existentes.
3. Colocar **worker independiente** como comando del mismo proyecto (ej. `python -m mvp.watchdog_worker`) si el host permite un proceso adicional; en producción más fiable, separar host de worker siempre activo.
4. Llamar **únicamente por HTTP** al plugin host, sin imports cruzados prohibidos.
5. Usar Postgres duradero para el estado. Para desarrollo local, SQLite es admisible con un único worker, pero no como solución concurrente/48h sobre un montaje remoto de objetos.
6. Conectar componentes visuales existentes de la UI. Añadir la entrada **Watchdogs** a navegación, no otro chat duplicado.
7. Si existe polling `git pull` cada 60 s o reinicios por despliegue, reanudar por estado, no confiar en memoria de proceso.
8. Verificar cada cambio en rama de trabajo, con tests, commit focalizado y SHA; no tocar permisos ni credenciales del usuario.

---

## 8. Estructura de datos: objeto editable y versionado

> JSON de **ejemplo contractual**: el modelo/router puede proponerlo, pero el backend debe validarlo. Los IDs de skills y modelos son nombres lógicos; sustituir por el catálogo **real** del proyecto, sin inventar componentes desplegados.

```json
{
  "schema_version": 1,
  "id": "wd_router_audit_01",
  "version": 4,
  "name": "Auditoría de Chat y Router",
  "description": "Supervisar auditoría read-only con evidencia",
  "objective": "Registrar defectos comprobables sin modificar main",
  "status": "DRAFT",
  "run_mode": "stepwise",
  "schedule": {
    "start": "now",
    "duration_minutes": 1440,
    "task_interval_seconds": 600,
    "scheduler_poll_seconds": 10,
    "step_timeout_seconds": 45,
    "timezone_display": "America/Bogota"
  },
  "budgets": {
    "max_steps": 100,
    "max_model_calls": 80,
    "max_tokens_total": 150000,
    "max_cost_usd": 5.0,
    "max_concurrent_tasks": 2,
    "max_attempts_per_task": 3
  },
  "policy": {
    "default_read_only": true,
    "allow_write": false,
    "required_approval_for": ["git_write", "deployment", "external_side_effect"],
    "stop_on_budget_exceeded": true,
    "stop_on_deadline": true,
    "credential_scope": "server_side_only"
  },
  "plan": {
    "acceptance_criteria": ["reporte con archivo:linea", "cero cambios en main"],
    "close_condition": {"kind": "all_required_tasks_succeeded"},
    "tasks": [
      {
        "id": "t1", "title": "Ver SHA", "kind": "once",
        "depends_on": [], "plugin_id": "github_readonly", "action": "get_head",
        "skills": ["verification-before-completion"],
        "inputs": {"branch": "main"}, "permissions": ["read"],
        "required": true
      },
      {
        "id": "t2", "title": "Auditar frontend", "kind": "once",
        "depends_on": ["t1"], "plugin_id": "audit_readonly", "action": "frontend",
        "skills": ["systematic-debugging"],
        "inputs": {"scope": "chat"}, "permissions": ["read"],
        "required": true
      },
      {
        "id": "t3", "title": "Revisión periódica del estado", "kind": "monitor",
        "depends_on": ["t1"], "plugin_id": "health_readonly", "action": "check",
        "skills": [], "inputs": {}, "permissions": ["read"],
        "required": false, "interval_seconds": 600
      }
    ]
  },
  "handoff": {"summary": "", "next_action": "", "evidence_refs": []},
  "labels": ["router", "audit", "read-only"]
}
```

### 8.1 Validaciones duras del backend

- `duration_minutes` entero en `[10, 2880]`, sin conversiones ambiguas.
- `task_interval_seconds` en `[60, 3600]` para ejecución periódica por defecto; el scheduler puede revisar más seguido sin llamar al modelo.
- `step_timeout_seconds` en `[15, 90]` y siempre menor que `lease_seconds` con margen.
- `0 < max_concurrent_tasks <= límite del servidor`, presupuestos estrictamente positivos.
- IDs de tareas únicos, dependencias existentes, prohibir autoreferencia y ciclos.
- `plugin_id + action + skills` deben existir en **registro confiable**, y los permisos solicitados deben ser subconjunto de los permitidos al usuario y al workflow.
- Máximo tamaño de inputs/salidas; no persistir cuerpos enormes en DB ni permitir que un output se vuelva una instrucción del sistema.
- Transiciones de estado y revisiones condicionadas al `version` esperado.
- Para `monitor`, definir condición de éxito/alerta explícita; si no se cumple, reprogramar hasta deadline.
- No conceder nuevas autorizaciones al editar el JSON directamente.

---

## 9. Persistencia y concurrencia (PostgreSQL)

### 9.1 Esquema SQL inicial propuesto

```sql
-- Migración de ejemplo; adaptar a convenciones y modelo de usuarios existentes.
CREATE TABLE watchdogs (
  id UUID PRIMARY KEY,
  owner_id TEXT NOT NULL,
  name TEXT NOT NULL,
  status TEXT NOT NULL CHECK (status IN
   ('DRAFT','SCHEDULED','ACTIVE','PAUSED','COMPLETED','EXPIRED','FAILED','CANCELLED')),
  revision INTEGER NOT NULL DEFAULT 1,
  config JSONB NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  started_at TIMESTAMPTZ,
  deadline_at TIMESTAMPTZ,
  heartbeat_at TIMESTAMPTZ,
  stop_requested BOOLEAN NOT NULL DEFAULT FALSE,
  closed_at TIMESTAMPTZ
);

CREATE TABLE watchdog_tasks (
  id UUID PRIMARY KEY,
  watchdog_id UUID NOT NULL REFERENCES watchdogs(id) ON DELETE CASCADE,
  task_key TEXT NOT NULL,
  title TEXT NOT NULL,
  kind TEXT NOT NULL CHECK (kind IN ('once','monitor')),
  state TEXT NOT NULL CHECK (state IN
   ('BLOCKED','QUEUED','RUNNING','WAITING','SUCCEEDED','FAILED','CANCELLED','TIMED_OUT')),
  depends_on TEXT[] NOT NULL DEFAULT '{}',
  descriptor JSONB NOT NULL,
  checkpoint JSONB NOT NULL DEFAULT '{}',
  next_due_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  last_started_at TIMESTAMPTZ,
  attempts INTEGER NOT NULL DEFAULT 0,
  lease_owner TEXT,
  lease_until TIMESTAMPTZ,
  fence BIGINT NOT NULL DEFAULT 0,
  last_error TEXT,
  last_result JSONB,
  UNIQUE (watchdog_id, task_key)
);

CREATE TABLE watchdog_attempts (
  id UUID PRIMARY KEY,
  task_id UUID NOT NULL REFERENCES watchdog_tasks(id) ON DELETE CASCADE,
  fence BIGINT NOT NULL,
  idempotency_key TEXT NOT NULL UNIQUE,
  started_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  finished_at TIMESTAMPTZ,
  status TEXT NOT NULL,
  output_ref TEXT,
  error_code TEXT
);

CREATE TABLE watchdog_events (
  seq BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  watchdog_id UUID NOT NULL REFERENCES watchdogs(id) ON DELETE CASCADE,
  task_id UUID,
  happened_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  event_type TEXT NOT NULL,
  actor_type TEXT NOT NULL,
  actor_id TEXT,
  correlation_id TEXT,
  payload JSONB NOT NULL DEFAULT '{}'
);

CREATE TABLE watchdog_approvals (
  id UUID PRIMARY KEY,
  watchdog_id UUID NOT NULL REFERENCES watchdogs(id) ON DELETE CASCADE,
  task_id UUID NOT NULL REFERENCES watchdog_tasks(id) ON DELETE CASCADE,
  operation_id TEXT NOT NULL,
  requested_by TEXT NOT NULL,
  decision TEXT NOT NULL CHECK (decision IN ('PENDING','APPROVED','DENIED','EXPIRED')),
  decided_by TEXT,
  decided_at TIMESTAMPTZ,
  valid_until TIMESTAMPTZ,
  UNIQUE (watchdog_id, operation_id)
);

CREATE INDEX wd_due_idx ON watchdog_tasks(state, next_due_at);
CREATE INDEX wd_lease_idx ON watchdog_tasks(state, lease_until);
CREATE INDEX wd_events_idx ON watchdog_events(watchdog_id, seq DESC);
CREATE INDEX wd_owner_idx ON watchdogs(owner_id, status);
```

### 9.2 Regla transaccional del scheduler

**Reclamación (claim):** tomar una sola tarea vencida y elegible con `FOR UPDATE SKIP LOCKED`; actualizar `state`, `lease_owner`, `lease_until` y `fence` en **una transacción**. Considerar elegibles los jobs cuyo watchdog esté `ACTIVE`, sin `stop_requested`, no vencido, con dependencias satisfechas y presupuesto disponible.

```sql
-- Ejemplo ilustrativo: se ejecuta en UNA transacción de PostgreSQL.
-- $1: worker_id, $2: timeout de lease en segundos.
WITH candidate AS (
 SELECT t.id
 FROM watchdog_tasks t
 JOIN watchdogs w ON w.id = t.watchdog_id
 WHERE w.status = 'ACTIVE'
   AND w.stop_requested = FALSE
   AND w.deadline_at > now()
   AND (
      (t.state IN ('QUEUED','WAITING','BLOCKED') AND t.next_due_at <= now())
      OR (t.state = 'RUNNING' AND t.lease_until < now())
   )
   AND NOT EXISTS (
      SELECT 1 FROM unnest(t.depends_on) d(task_key)
      LEFT JOIN watchdog_tasks p
        ON p.watchdog_id = t.watchdog_id AND p.task_key = d.task_key
      WHERE p.id IS NULL OR p.state <> 'SUCCEEDED'
   )
 ORDER BY t.next_due_at, t.id
 FOR UPDATE OF t SKIP LOCKED
 LIMIT 1
)
UPDATE watchdog_tasks t
SET state = 'RUNNING', lease_owner = $1,
    lease_until = now() + ($2 * interval '1 second'),
    fence = t.fence + 1, attempts = t.attempts + 1,
    last_started_at = now()
FROM candidate c
WHERE t.id = c.id
RETURNING t.*;
```

**Advertencia de implementación:** si se recupera una tarea cuyo lease anterior venció, **no ejecutar de nuevo una escritura externa hasta reconciliar su `operation_id`**. La condición de estado `RUNNING + lease vencido` habilita *recuperación*, no permiso para duplicar efectos.

**Finalización:** `UPDATE ... WHERE id = :id AND fence = :fence AND lease_owner = :worker AND state='RUNNING'` y, además, verificar que el watchdog continúa habilitado y no vencido. Si `rowcount=0`, descartar resultado obsoleto y crear un evento de diagnóstico. El commit del evento y del nuevo estado se hace en la misma transacción.

**Sobre la carrera de cancelación:** confirmar estado y autorización **justo antes de cualquier efecto externo**. Si una acción está ya en curso, usar cancelación cooperativa y conciliación posterior; no prometer que una petición HTTP ya enviada puede deshacerse.

### 9.3 Recuperación automática

- El watchdog y sus pasos se leen de DB al arrancar; **no** dependen de listas Python en memoria.
- Los leases vencidos se investigan y reclaman; mantener `fence` para rechazar workers antiguos.
- Si un proveedor devolvió resultado antes de morir el worker, consultar el `operation_id`/commit/artefacto antes de reintentar.
- Persistir los tokens consumidos, duración y cuota en la misma transacción que cierra el paso, o con ledger idempotente separado.
- Una tarea `BLOCKED` por dependencia fallida debe aparecer como bloqueada, no como «en progreso» para siempre.
- Detectar watchdog `ACTIVE` con `heartbeat_at` viejo y generar alerta `WORKER_STALE`.
- Si se perdió el servicio durante varias horas, no ejecutar miles de comprobaciones antiguas: **coalescer** ticks periódicos y ejecutar la próxima inspección actual.

---

## 10. Pseudocódigo de worker de calidad de producción

Este pseudocódigo es deliberadamente específico y separa responsabilidades. **No pegarlo como si fuera un script completo:** implementarlo sobre la infraestructura y librerías existentes, con transacciones, autenticación y tests.

```python
# watchdog_worker.py — diseño operacional
async def worker_forever(worker_id: str):
    while not shutting_down():
        # El claim debe ser atómico y aplicar TODOS los filtros de estado,
        # dependencias, permisos y cuota antes de entregar trabajo.
        claim = await repository.claim_due_task(worker_id, lease_seconds=180)
        if claim is None:
            await asyncio.sleep(5)
            continue

        try:
            watchdog = await repository.load_watchdog(claim.watchdog_id)
            await policy.assert_still_active_authorized(watchdog, claim)
            await policy.assert_budget_available(watchdog, claim)

            # En recovery, revisar si el operation_id ya produjo efectos.
            op_id = f"{claim.watchdog_id}/{claim.task_key}/{claim.logical_step}"
            known = await effects.reconcile_if_already_completed(op_id)
            if known is not None:
                result = known
            else:
                skill = registry.require_registered(
                    claim.plugin_id, claim.action, claim.skills
                )
                await policy.check_skill_scope(skill, claim.permissions)
                envelope = context_builder.from_checkpoint(claim)
                # HTTP de duración breve, timeout < lease. Nunca URLs arbitrarias.
                result = await harness.call(
                    skill=skill,
                    payload=envelope,
                    operation_id=op_id,
                    timeout_seconds=claim.step_timeout_seconds,
                    correlation_id=claim.correlation_id,
                )

            await result_schema.validate(result)
            await verification.verify_if_required(claim, result)
            await repository.commit_result_if_fence_current(
                claim=claim,
                result=result,
                next_due_at=calculate_next_due_or_close(claim, result),
                meter=result.usage,
            )
        except TransientProviderError as exc:
            await repository.retry_with_backoff_if_fence_current(claim, exc)
        except (PolicyError, BudgetError) as exc:
            await repository.block_or_pause_if_fence_current(claim, exc)
        except Exception as exc:
            await repository.record_failure_if_fence_current(claim, safe_error(exc))
```

### 10.1 Contrato de respuesta del plugin/harness

```json
{
  "schema_version": 1,
  "operation_id": "wd-123/t3/step-0004",
  "status": "ok",
  "condition_met": false,
  "decision_hint": "WAIT",
  "checkpoint": {"cursor": "sha-of-last-observation", "completed_items": 15},
  "output_ref": "artifact://wd-123/t3/step-0004",
  "evidence_refs": ["artifact://wd-123/t3/check-4"],
  "usage": {"model_calls": 1, "input_tokens": 1000, "output_tokens": 250, "estimated_cost_usd": 0.002},
  "finish_reason": "stop",
  "retry_after_seconds": null
}
```

- El **backend** decide si repetir, esperar, aprobar o cerrar. `decision_hint` es solo sugerencia.
- Para `finish_reason='length'`, registrar truncamiento y aplicar política explícita de continuación segura; no dar salida incompleta por válida.
- El `operation_id` debe corresponder al paso lógico, incluso a través de retries. El identificador de **attempt** es diferente.
- `checkpoint` se valida por tamaño, estructura, permisos y versión.
- Para `condition_met=true`, exigir evidencia y validación; no creerlo automáticamente por la afirmación de una LLM.

### 10.2 Política de reintentos

```text
HTTP 429/503 o error transitorio -> esperar Retry-After si está presente;
                                    si no, backoff (30s, 60s, 120s...) + jitter.
Timeout de lectura             -> reconciliar operación antes de repetir.
HTTP 400/401/403 permanente    -> NO reintentar sin corregir permisos/configuración.
Error de esquema               -> FAIL del paso y evento con evidencia.
Repetición de error 3 veces    -> circuito abierto por proveedor / alerta.
Deadline agotado               -> EXPIRED; no seguir reclamando tareas.
Presupuesto agotado            -> PAUSED o FAILED según política.
```

---

## 11. API HTTP propuesta (Router)

| Método | Ruta | Uso |
|---|---|---|
| `GET` | `/watchdogs` | listar watchdogs del usuario con filtros/paginación. |
| `POST` | `/watchdogs` | crear borrador validado. |
| `GET` | `/watchdogs/{id}` | estado + config + revisión + resumen. |
| `PATCH` | `/watchdogs/{id}` | guardar revisión si `version` coincide (optimistic lock). |
| `POST` | `/watchdogs/{id}/validate` | validar DAG, permisos, presupuestos, skills y cierres. |
| `POST` | `/watchdogs/{id}/start` | activar con inicio/deadline transaccional. |
| `POST` | `/watchdogs/{id}/pause` | detener nuevos claims y señalizar en curso. |
| `POST` | `/watchdogs/{id}/resume` | retomar desde checkpoints, respetando deadline. |
| `POST` | `/watchdogs/{id}/stop-after-step` | cierre ordenado, no ejecutar siguiente paso. |
| `POST` | `/watchdogs/{id}/cancel` | cancelación, sin acciones futuras. |
| `GET` | `/watchdogs/{id}/tasks` | tareas, dependencias, resultados y siguientes `due_at`. |
| `GET` | `/watchdogs/{id}/events?after_seq=N` | bitácora incremental paginada. |
| `GET` | `/watchdogs/{id}/health` | liveness/readiness/últimos heartbeats. |
| `POST` | `/watchdogs/{id}/approvals/{approval_id}` | autorizar/denegar operación concreta. |
| `GET` | `/watchdogs/skills` | catálogo de skills disponibles al usuario. |
| `GET` | `/watchdogs/{id}/export` | Markdown/JSON saneado y adjuntos autorizados. |

**Respuesta estándar:** `{request_id, data, error: {code, message} | null, version}`; todas las rutas aplican autenticación, propiedad del watchdog, autorización por acción, límites de tráfico y saneamiento de errores.

### 11.1 Ejemplo realista de validación FastAPI/Pydantic

```python
from typing import Literal
from pydantic import BaseModel, Field, model_validator

class WDTaskCreate(BaseModel):
    id: str = Field(pattern=r"^[a-zA-Z0-9_-]{1,64}$")
    title: str = Field(min_length=3, max_length=160)
    kind: Literal["once", "monitor"]
    depends_on: list[str] = Field(default_factory=list, max_length=32)
    plugin_id: str
    action: str
    skills: list[str] = Field(default_factory=list)
    inputs: dict = Field(default_factory=dict)
    permissions: list[Literal["read", "write", "http", "model"]] = Field(default_factory=list)
    required: bool = True

class WDCreate(BaseModel):
    name: str = Field(min_length=3, max_length=100)
    objective: str = Field(min_length=5, max_length=5000)
    duration_minutes: int = Field(ge=10, le=2880)
    task_interval_seconds: int = Field(default=600, ge=60, le=3600)
    step_timeout_seconds: int = Field(default=45, ge=15, le=90)
    max_concurrent_tasks: int = Field(default=2, ge=1, le=8)
    tasks: list[WDTaskCreate] = Field(min_length=1, max_length=40)

    @model_validator(mode="after")
    def check_dag(self):
        ids = [t.id for t in self.tasks]
        if len(ids) != len(set(ids)):
            raise ValueError("IDs duplicados")
        deps = {t.id: t.depends_on for t in self.tasks}
        color = {}  # 1 = visitando; 2 = resuelto
        def visit(node):
            if color.get(node) == 1:
                raise ValueError("Dependencia circular")
            if color.get(node) == 2:
                return
            color[node] = 1
            for parent in deps[node]:
                if parent not in deps:
                    raise ValueError(f"Dependencia inexistente: {parent}")
                visit(parent)
            color[node] = 2
        for node in deps:
            visit(node)
        return self

# Falta intencionalmente la validación de permisos/skills del catálogo real.
# No activar ningún watchdog sin esa segunda validación y auth del Router.
```

### 11.2 Actualizaciones para el cliente móvil

- Preferido: **SSE** (`GET /watchdogs/{id}/stream`) con IDs crecientes y recuperación desde `last_event_id`; si el stack actual ya tiene WebSocket sólido, reutilizarlo.
- Respaldo universal: polling cada 5–15 s **solo cuando el usuario está mirando**; lectura incremental `after_seq`.
- Tras reconectar: `GET /watchdogs/{id}` autoritativo, luego eventos que falten. No inferir progreso a partir de relojes locales.
- Para evitar conexiones excesivas, combinar varios watchdogs en un stream por usuario o hacer polling con `ETag`.
- El cliente nunca recibe `X-API-Key` del Harness ni PAT de GitHub/HF; solo su sesión autenticada contra el Router.

---

## 12. Skills: activación real, catalogada y segura

### 12.1 Registro declarativo de skills

```yaml
skills:
  - id: verification-before-completion
    version: "1"
    category: verification
    permission: read
    plugin_id: qa_harness
    action: verify
    allowed_task_types: [once, monitor]
    max_step_seconds: 45
    input_schema_ref: "schemas/verify-input.json"
    output_schema_ref: "schemas/verify-output.json"
  - id: systematic-debugging
    version: "1"
    category: analysis
    permission: read
    plugin_id: debug_harness
    action: analyze
    allowed_task_types: [once]
    max_step_seconds: 60
```

> Nombres ilustrativos. **No** asumir que `qa_harness`/`debug_harness` están instalados: Grok debe mapear cada skill a la acción **real** ya disponible, o marcar `NO EXISTE` y dejarla deshabilitada hasta implementarla.

### 12.2 Cuándo se activa una skill

1. El usuario la habilita en la configuración de **una tarea**, o la selecciona una plantilla autorizada.
2. El backend valida identidad, políticas, versión, permisos y compatibilidad de entradas.
3. El scheduler prepara la ficha/context pack y solicita la acción permitida por el plugin host autenticado.
4. El Harness ejecuta únicamente la capability registrada; produce evidencia/salida estructurada.
5. El backend verifica resultado, registra consumo y solo entonces avanza o reprograma.

**Nunca:** aceptar el texto de una LLM como autorización para crear herramientas nuevas, ejecutar código libre, usar tokens, cambiar el alcance, activar permisos o saltarse aprobaciones.

### 12.3 Activadores por evento y condiciones

Soportar `on_start`, `on_task_success`, `on_dependency_ready`, `on_external_event_verified`, `on_deadline_approaching`, `on_retry_limit`, `on_manual_approval`. En cada caso: validar el evento → validar permisos → programar paso corto. Si llegan 20 webhooks iguales, deduplicar por `event_id`.

---

## 13. Seguridad, límites y operación

### 13.1 Autenticación y privilegios

- Reutilizar auth/sesión actual del Router; vincular registros a `owner_id`/workspace; jamás aceptar `owner_id` libre del navegador.
- Acceso independiente a la API del Router y al Harness (su `X-API-Key` **solo de servidor a servidor**).
- Secretos desde vault del servidor/Secrets del Space; configuración persiste **alias** de secreto, no valor.
- Cada operación escribe auditoría `actor`, `scope`, `approval_id`, `operation_id` y `revision`.
- `HTTP` externo solo a hosts/rutas aprobadas por configuración del administrador, no URLs libres propuestas por el modelo; mitigar SSRF.
- Para GitHub, usar permisos mínimos en repo/rama y validar SHA antes de escritura. Preferir PR de revisión en vez de push silencioso a `main`.
- Cualquier llamada que pause/reinicie/escale un Space debe ser una acción separada y aprobada; no mezclar «leer estado» con «administrar recursos».

Referencia de endurecimiento de destinos HTTP: [OWASP SSRF Prevention](https://cheatsheetseries.owasp.org/cheatsheets/Server_Side_Request_Forgery_Prevention_Cheat_Sheet.html).

### 13.2 Presupuestos y circuit breaker

Límites por **watchdog, tarea, modelo, usuario y proveedor**. Registrar: `calls_used`, `tokens_in`, `tokens_out`, `cost_estimated`, `api_errors`, `rate_limit_until`, `wall_clock_elapsed`. Configurar máximo absoluto independiente del modelo, y cortar al llegar a cualquiera de los topes.

**Importante:** no usar tokens como única medida; los precios cambian y las estimaciones no equivalen a facturas reales. El watchdog corta por el límite interno y muestra que el coste es aproximado.

### 13.3 Ciclo de vida y fallos

| Incidente | Detección | Resultado obligatorio |
|---|---|---|
| Se cierra móvil | no afecta worker | tareas siguen; UI recupera estado. |
| Vercel redeploy | la UI puede reconectar | ningún estado del watchdog se pierde. |
| Worker crash | heartbeat/lease vence | recuperar tras lease y reconciliar efectos. |
| Reinicio HF Space | instancia cae | reanudar **solo** si vuelve el servicio; no garantizar ejecución mientras duerme. |
| Postgres desconectado | health/readiness falla | no ejecutar nuevas operaciones sin persistencia; alertar. |
| Harness desconectado | timeout/probes | backoff/circuit breaker; no marcar éxito. |
| Modelo truncó salida | `finish_reason=length` | estado parcial, continuación bajo límites. |
| Commit duplicado | misma `operation_id` | localizar SHA/artefacto y no repetir escritura. |
| Usuario pausa | control API persistido | no reclamar más pasos; curso actual se detiene cooperativamente. |
| Plazo 48 h vence | reloj de servidor en UTC | `EXPIRED` con handoff, salvo éxito previo confirmado. |

### 13.4 Observabilidad concreta

**Métricas:** watchdogs activos, tareas en cola, tareas bloqueadas por dependencia, p95 de tiempo de paso, ratio de reintento, segundos desde último heartbeat, número de leases vencidos, salidas truncadas, presupuesto usado y tiempo de recuperación tras caída.

**Eventos:** `WD_CREATED`, `PLAN_VALIDATED`, `WD_STARTED`, `TASK_ELIGIBLE`, `TASK_CLAIMED`, `SKILL_ACTIVATED`, `STEP_FINISHED`, `TASK_WAITING`, `RETRY_SCHEDULED`, `APPROVAL_REQUIRED`, `PAUSED`, `RESUMED`, `BUDGET_REACHED`, `DEADLINE_REACHED`, `WD_COMPLETED`, `WD_EXPIRED`, `WD_FAILED`, `WD_CANCELLED`.

**Logs:** IDs y metadatos seguros, sin claves, sin prompts secretos, sin bodies completos; `request_id` en todos los saltos. Mantener un `healthz` técnico separado de la experiencia del usuario.

---

## 14. Algoritmo de cierre: evitar flujos eternos

```text
¿cancel_requested?                 -> CANCELLED
¿stop_requested?                   -> detener tras paso actual; PARTIAL/STOPPED (mapear a CANCELLED + razón)
¿now >= deadline_at?              -> EXPIRED
¿se agotó presupuesto absoluto?    -> PAUSED o FAILED según política
¿hay error permanente?            -> FAILED (con evidencia)
¿todas las tareas requeridas OK?
  └─ ¿se verificaron todos los criterios de aceptación?
      ├─ sí  -> COMPLETED + artefacto final + handoff
      └─ no  -> WAIT/FAIL según error y tiempo restante
¿se requiere aprobación?          -> PAUSED + aprobación pendiente
¿hay tareas programables?         -> ACTIVE, scheduler continúa
¿solo quedan dependencias fallidas? -> FAILED/BLOCKED con diagnóstico, nunca en espera infinita
```

**Nota de modelado:** si se quiere estado `STOPPED` independiente, añadirlo formalmente a máquina de estados y SQL; no registrar un nombre de estado no permitido. El ejemplo usa `CANCELLED` con razón `graceful_stop` como implementación mínima.

### 14.1 Condición de éxito para monitores de larga duración

Distinguir `close_condition = on_condition_met` (termina apenas encuentre el evento), `run_full_window` (supervisa hasta deadline y completa solo si cumplió objetivos de cobertura; un plazo agotado por sí solo no significa éxito) y `all_required_tasks_succeeded`. Para `run_full_window`, registrar final `COMPLETED` únicamente si se satisfizo su condición explícita de vigilancia; de lo contrario, `EXPIRED`.

---

## 15. Pruebas obligatorias: criterios de aceptación

| ID | Prueba | Resultado PASS |
|---|---|---|
| T01 | crear `duration=9`, `duration=2881` | HTTP 422 y cero registros activos. |
| T02 | crear `duration=10`, `duration=2880` | validación correcta. |
| T03 | DAG circular y dependencia inexistente | denegado antes de activar. |
| T04 | dos workers reclaman misma tarea | solo un fence vigente por turno. |
| T05 | matar worker en medio del paso | lease vence y se recupera checkpoint. |
| T06 | worker viejo entrega resultado tras nuevo claim | actualización del viejo rechazada. |
| T07 | reintentar llamada GitHub después de timeout | no duplica commit ni PR. |
| T08 | pausa con paso activo | no inicia pasos nuevos; estado honesto. |
| T09 | cancelar durante red/LLM | no se inician nuevas acciones; curso en progreso se concilia. |
| T10 | reinicio de Router y cierre del navegador | al reabrir coincide el estado DB. |
| T11 | perder conexión a DB | fail-closed: sin nuevas acciones externas. |
| T12 | error HTTP 429 con `Retry-After` | reprograma respetando espera. |
| T13 | `finish_reason=length` | no trata respuesta incompleta como verificada. |
| T14 | usuario sin permiso solicita activar skill write | HTTP 403 y evento de denegación. |
| T15 | editar revisión v4 desde pantalla obsoleta v3 | 409/conflict, sin perder cambio. |
| T16 | fecha límite transcurrida con tarea pendiente | EXPIRED + handoff. |
| T17 | todas las obligatorias completadas y validadas | COMPLETED + evidencia. |
| T18 | reconectar móvil tras 30 minutos | sincroniza eventos y estado correcto. |
| T19 | entrada contiene token/cadena sensible | no aparece en logs/exportaciones. |
| T20 | cron/worker inactivo en HF gratuito | interfaz avisa «sin ejecución» y no afirma continuidad. |
| T21 | dos tareas paralelas con mismo archivo de escritura | lock de recurso o ejecución serializada. |
| T22 | evento webhook repetido 5 veces | un único paso lógico, varios intentos auditados si procede. |
| T23 | agotamiento del presupuesto | ninguna llamada adicional a proveedor. |
| T24 | servicio activo 48h sobre worker always-on | inspecciones/checkpoints conforme a las políticas y sin pérdida de estado. |

**Verificación:** pruebas unitarias (schema, DAG, políticas), integración (Postgres/Router/Harness), fallo inyectado (crash, timeout, 429), seguridad (auth/SSRF/secrets), pruebas UI responsive y end-to-end. Cada PASS debe enlazar a salida real, no marcarse por intuición.

---

## 16. Plan de construcción quirúrgico para Grok

> Objetivo: **reciclar primero** lo que exista; añadir solo el motor y la ventana que falten. Prohibida la reescritura general del chat/router.

### Fase 0 — Auditoría y mapa de cableado (solo lectura)

1. Listar rama/SHA, estructura de backend/frontend, rutas, tablas, autenticación, registries de plugins, mecanismos de eventos y tests actuales.
2. Localizar qué ya sirve para jobs, tasks, scheduler, tools/skills, bitácora, fichas, context pack, checkpoints y modal/panel UI.
3. Identificar si hay Postgres/Redis/bucket ya disponible. Si no, escoger una sola persistencia transaccional.
4. Confirmar cómo corre el proceso en HF, si puede alojar worker persistente y si el Space puede dormir.
5. Entregar tabla **EXISTE / NO EXISTE / REUTILIZAR / MODIFICAR** con archivo:línea; sin inventar rutas.

### Fase 1 — Contrato de datos

1. Esquemas tipados, DAG, permisos, tiempos, presupuestos, estado y versión.
2. Migración de tablas + índices y test de validación.
3. Definición de resultado del Harness y `operation_id` estable.
4. Sin UI ni ejecución automática hasta que las reglas sean verificables.

### Fase 2 — Motor mínimo

1. CRUD de borradores con auth.
2. Start/pause/resume/cancel con transiciones atómicas.
3. Worker con claim + lease + fence, una tarea `once` de solo lectura.
4. Checkpoint, evento, `due_at` y recuperación ante caída.
5. Tests de doble claim, timeout y cancelación.

### Fase 3 — LOOP + Skills

1. Vincular registro real de skills a acciones del Harness por HTTP.
2. Añadir plan DAG, condiciones, `monitor` y verificador.
3. Encapsular ficha/handoff para consumir contexto mínimo.
4. Añadir aprobaciones y presupuestos antes de habilitar `write`.

### Fase 4 — Ventana Watchdog Studio

1. Integrar entrada `Watchdogs` en navegación existente.
2. Listado, pantalla de detalle, formulario, editor de plan, inspector, LOOP y eventos.
3. Responsive con panel inferior en móvil.
4. Señales reales de salud y reconexión; sin timers de trabajo en la UI.
5. Mantener diseño blanco/azul existente.

### Fase 5 — Robustez avanzada

1. Leases caducados, concurrencia, rate limits, reintentos seguros.
2. Revisions/CAS, handoff, reportes y exportación.
3. Prueba de continuidad de 48 horas en entorno always-on, fallos inyectados y auditoría de permisos.
4. Despliegue gradual mediante flag OFF → solo lectura → beta → producción.

### 16.1 Archivos mínimos *orientativos* (no crear si existe equivalente)

```text
mvp/watchdog.py                 # API y validaciones, reutilizar app/router existente
mvp/watchdog_worker.py          # trabajo en background (proceso separado)
mvp/watchdog_store.py           # consultas transaccionales y eventos
mvp/watchdog_policy.py          # permisos, budgets, revisión, catálogo
migrations/XXX_watchdogs.sql    # solo si no hay sistema de migraciones
frontend/.../WatchdogPanel.tsx # ventana integrada en UI existente
frontend/.../watchdog.css      # solo si falta estilo equivalente
tests/test_watchdog_*.py        # tests sin secretos ni dependencias reales
```

**Si `watchdog.py` queda excesivamente grande**, dividir por responsabilidades justificadas; si la aplicación ya tiene store/policies/migrations, reutilizarlos. No crear 20 microservicios ni un segundo router.

### 16.2 Orden de entrega y puntos de control

- **Salida A:** auditoría de hechos y gaps, sin editar; revisión humana.
- **Salida B:** contratos + migración + pruebas, sin UI.
- **Salida C:** worker + API read-only + pruebas de crash.
- **Salida D:** LOOP/skills + autorizaciones.
- **Salida E:** UI responsive, auditoría X-Ray y test de 48h.

En cada salida entregar: diff, archivos tocados, pruebas ejecutadas, salida cruda, fallos, límites, commit/SHA real (si se autorizó escritura) y pasos de rollback. **No declarar PASS sin ejecución comprobada.**

---

## 17. Instrucciones listas para entregar a GROK

Copiar el siguiente bloque en Grok junto con el enlace/archivo de esta especificación. Es una orden de **implementación controlada**, no una autorización implícita para tocar el repositorio.

```text
ROL: Arquitecto y programador senior de sistema Watchdog/LOOP.
OBJETIVO: Integrar un Watchdog Studio supervisado de 10 minutos a 48 horas,
con tareas separadas, LOOP editable, Skills autorizadas por tarea, plan DAG,
bitácora, checkpoints, handoff, control de tiempos y ventana web/móvil.

FUENTE OBLIGATORIA:
- Leer íntegra la especificación Watchdog_Avanzado_10min_48h_Arquitectura_UI_Grok.md.
- Tomar los nombres de componentes del documento como PROPUESTAS, no evidencia
  de archivos que existan.

ARQUITECTURA QUE DEBES RESPETAR:
- Router/Fichas = Edificio 1.
- Plugins/Harness = Edificio 2.
- Toda llamada entre edificios se hace SOLO por HTTP autenticado y acciones
  registradas; no importar módulos entre edificios.
- Reutilizar app FastAPI, chat, router, fichas, vault, navegación y controles
  existentes. No alterar endpoints ajenos al Watchdog.
- UI web/móvil minimalista BLANCO/GRIS con estados AZULES; sin emojis.
- No ejecutar 48 h en Vercel Function, browser timer ni una llamada LLM.

PRIMERA PASADA OBLIGATORIA: SOLO LECTURA.
1. Inspecciona rama/SHA, últimos cambios, estructura, endpoints, autorizaciones,
   sistemas de jobs/bitácora/skills y componentes de frontend.
2. Entrega matriz de hallazgos: requisito | EXISTE/NO EXISTE | archivo:línea |
   estado | modificación mínima.
3. Detecta posibles problemas de despliegue HF, reposo y persistencia.
4. Propón una implementación mínima que reutilice el máximo de componentes.
5. No escribas, hagas push ni despliegues hasta aprobación expresa de la fase.

AL PROGRAMAR CADA FASE AUTORIZADA:
- Diff quirúrgico y versionado.
- Validación tipada, auth, límites y idempotencia.
- Máquina de estados, persistencia, leases, fencing y manejo de fallos.
- LOOP = PLAN→EXECUTE→OBSERVE→VERIFY→DECIDE→CHECKPOINT→HANDOFF.
- Dependencias DAG sin ciclos. Task/skill/state/budget independientes.
- Resultado de las tools por HTTP, con operación y correlación.
- Pruebas reales: funcionales, concurrencia, seguridad, desconexión y móvil.
- No imprimir ni guardar secretos. No inventar archivos, rutas ni resultados.
- Si encuentras un gap en una zona no autorizada, reporta y DETENTE.

ROLES DE VERIFICACIÓN:
SHERIFF: prohíbe tareas/acciones sin permiso o fuera del alcance.
CENTINELA: valida que cada transición, skill y ejecución respete el LOOP.
GUARDIÁN: comprueba que no falten contratos, tests, handoff ni cierre.

FORMATO DE CADA ENTREGA:
1. Estado y SHA verificado.
2. Hallazgos con archivo:línea.
3. Riesgos y dependencias.
4. Archivos editados (solo si autorizados) + diff focalizado.
5. Evidencias de tests / NO VERIFICADO.
6. Pendientes, condiciones de cierre y siguiente paso.
7. Parar al terminar la fase pedida y permitir revisión.
```

---

## 18. Recomendación de alcance: avanzado sin sobreingeniería

### Nivel A — suficiente para una primera versión útil

Un backend FastAPI ya existente, **una base Postgres**, **un worker**, **el Harness ya montado**, **una ventana React**, **una tabla de eventos** y **un contrato LOOP**. Ejecuta tareas read-only, admite DAG y checkpoints, dura hasta 48h si el worker está vivo y recupera estado ante reinicio.

### Nivel B — endurecimiento para uso real

Aprobaciones, autorización por tarea, scheduler multiworker con fencing e idempotencia, cuota por proveedor, reconexión, exportación, métricas y alertas. **Este es el objetivo recomendado antes de permitir escrituras automáticas.**

### Nivel C — solo cuando crezca la carga

Temporal o equivalente con workflows durables, workers redundantes, colas especializadas, tracing distribuido completo y panel de administración. Temporal tiene timers, tareas, historia durable y recuperación; no es requisito para un único proyecto. Documentación: [Temporal Tasks](https://docs.temporal.io/tasks), [Python SDK](https://docs.temporal.io/develop/python), [Worker best practices](https://docs.temporal.io/best-practices/worker).

**No crear** un nuevo kernel de LLM solo para organizar fichas si el backend puede llenar una plantilla JSON y el modelo actual puede generar el plan. Activar un micro-kernel **opcional** únicamente cuando haya complejidad justificable: planificación de DAG de muchos pasos, resolución de conflictos, replanificación significativa o compresión de contextos excesivos. Este micro-kernel **no** controla permisos, transacciones, scheduler ni resultados verificados: esas funciones deben seguir siendo deterministas en código.

---

## 19. Decisiones explícitas y límites que Grok debe reportar

1. **Continuidad absoluta** no existe sobre un servicio que pueda suspenderse. Si el cliente exige 48h sin interrupción, se requiere worker en infraestructura apropiada, redundancia si se necesita alta disponibilidad y DB durable.
2. **At-least-once** es una expectativa realista de entrega a un worker; los efectos deben ser idempotentes o reconciliados. Una promesa genérica de “exactly once” sería engañosa.
3. **`deadline_at`** debe estar en UTC y ser autoritativo en backend; pausas **no** alargan el deadline por defecto. Permitir «pausa congela reloj» solo como política explícita con nuevo deadline validado y máximo 48h desde el inicio original, si se mantiene esa restricción de producto.
4. **Las ediciones de un plan en curso** deben esperar límite de paso o pausa y registrarse como nueva revisión; no reescribir retroactivamente el historial.
5. **GitHub no es una base de eventos de alta frecuencia**. Para los logs y estados, Postgres; para código, Git; para adjuntos grandes, bucket.
6. **El contexto de la IA no es memoria durable.** Fichas y checkpoints tienen que existir en almacenamiento; cada petición recupera solo lo necesario.
7. **Los monitores periódicos** deben funcionar aun cuando el modelo no esté disponible; si la comprobación es determinista (HTTP health, SHA), hacerla por código sin LLM.
8. **No autoescalar ni despertar HF Spaces** a través de tools salvo consentimiento explícito: coste, disponibilidad y restricciones deben estar visibles.
9. **No modificar el chat existente** solo para mostrar watchdogs; separar ventana/panel y añadir la navegación mínima.
10. **La configuración editable no equivale a permisos editables:** el usuario puede cambiar la definición, pero el backend debe volver a autorizar cada acción.

---

## 20. Referencias oficiales y puntos verificados (consultados octubre de 2026)

1. Hugging Face, persistencia de Spaces: <https://huggingface.co/docs/hub/spaces-storage>
2. Hugging Face, lifecycle de Spaces: <https://huggingface.co/docs/hub/spaces-overview>
3. Hugging Face, suspensión en hardware gratuito: <https://huggingface.co/docs/hub/spaces-gpus>
4. Hugging Face, Storage Buckets: <https://huggingface.co/docs/hub/storage-buckets>
5. Vercel, cron límites y frecuencia: <https://vercel.com/docs/cron-jobs/usage-and-pricing>
6. Vercel, cron seguridad, duración y recuperación: <https://vercel.com/docs/cron-jobs/manage-cron-jobs>
7. MDN, limitaciones de pestañas en background: <https://developer.mozilla.org/en-US/docs/Web/API/Page_Visibility_API>
8. PostgreSQL, `SKIP LOCKED` en colas: <https://www.postgresql.org/docs/current/sql-select.html>
9. GitHub, límites REST y control de 429: <https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api>
10. OWASP, prevención SSRF: <https://cheatsheetseries.owasp.org/cheatsheets/Server_Side_Request_Forgery_Prevention_Cheat_Sheet.html>
11. Temporal, ejecución durable: <https://docs.temporal.io/tasks>
12. Temporal, SDK Python: <https://docs.temporal.io/develop/python>
13. Temporal, recomendaciones para workers: <https://docs.temporal.io/best-practices/worker>

**Resumen final para Grok:** construir **un motor supervisado, durable, seguro y editable**, con la **ventana Watchdog Studio** integrada y una barrera clara entre **el plan que propone la IA** y **las operaciones que autoriza el backend**. Mantener pequeñas las piezas, preservar el código actual y demostrar recuperación y trazabilidad antes de hablar de 48 horas continuas.

---

## 21. Integración opcional con CHAT y ROOM CONFERENCIAS

Si el producto ya dispone de un chat principal y de una sala de conferencias multiagente, incorporar el Watchdog como **herramienta visible**, no como una segunda interfaz de chat ni como un nuevo router. La ventana Watchdog Studio mantiene su propia navegación y puede abrirse desde ambos lugares.

### 21.1 Controles en el chat

- Botón **Watchdog** en el selector de herramientas. En OFF, el modelo no tiene permiso para lanzar ni modificar watchdogs. En ON, muestra acciones específicas autorizadas: `list`, `get`, `prepare_draft`, `request_start`, `request_pause`, `request_resume`, `request_cancel`.
- `prepare_draft` genera un borrador de plan pero **nunca lo activa** por sí mismo.
- `request_start`, `request_cancel` y cualquier acción sensible pasan por política del backend y por el control de aprobación que se haya definido.
- Después de responder, el chat puede mostrar una tarjeta: nombre, estado, tareas completadas, próximo paso y enlace a **Abrir Watchdog Studio**.
- El chat consume la API del Router; no se conecta directamente al worker ni recibe la clave del Harness.

### 21.2 Controles en ROOM CONFERENCIAS

- Añadir el Watchdog como **tool del ROOM**, disponible solo a los participantes/roles con permiso.
- Cada participante puede proponer tareas, pero el **orquestador** reúne las propuestas en un DAG validado y crea una revisión del plan.
- **Sheriff** bloquea acciones fuera de alcance; **Centinela** verifica que cada paso cumple el LOOP; **Guardián** comprueba que no falten evidencias, handoff y condición de cierre.
- Los roles no tienen privilegios mágicos: la autorización definitiva es del backend, y las decisiones de los agentes se registran como propuestas o verificaciones.
- Una conferencia puede consultar muchos watchdogs, pero cada watchdog mantiene **IDs, checkpoints, presupuesto y permisos propios**.
- Vincular eventos con `room_id`, `message_id` y `watchdog_id` como identificadores de correlación **sin copiar la transcripción íntegra** a cada ciclo.

### 21.3 Ejemplo de herramienta del modelo (contrato, no despliegue afirmado)

```json
{
  "name": "watchdog_prepare_draft",
  "description": "Propone un Watchdog para revisión humana; no lo activa",
  "parameters": {
    "type": "object",
    "properties": {
      "name": {"type": "string"},
      "objective": {"type": "string"},
      "duration_minutes": {"type": "integer", "minimum": 10, "maximum": 2880},
      "task_drafts": {"type": "array", "items": {"type": "object"}}
    },
    "required": ["name", "objective", "duration_minutes", "task_drafts"]
  }
}
```

**Recomendación:** primero integrar la ventana autónoma. Después exponer únicamente `list/get/prepare_draft` al chat y a ROOM. Habilitar acciones de control tras validar permisos, auditoría y pruebas de cancelación. Esto evita que la complejidad multiagente haga más frágil al watchdog base.
