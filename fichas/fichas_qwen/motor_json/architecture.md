<!-- VERBATIM: INPUT_BLOCK_MAESTRO_PATRON_RICARDO.md seccion 8 (Director 2026-10-19). Implementacion real: yaiwes_motor.py + herramientas ejecutar_plan_json/verificar_recibos + motor_objetivo.clasificar_vuelta + capa 'ej'. -->

## 8. ARCHIVO `architecture.md` — SISTEMA HORIZONTAL DE EJECUCIÓN + TRABAJO CONTINUO

### Arquitectura original comprobada

`COMANDOS JSON → PUENTE PYTHON → CATÁLOGO OPS → API REAL → ARCHIVO REAL → VERIFICACIÓN → INFORME`.

### Traslado a YAIWES (propuesta, sin sustituir su arquitectura existente)

`USUARIO → ROUTER INTACTO → FICHA AUTORIZADA → SYSTEM_CORE EXISTENTE + DELTA CONTINUIDAD → QWEN → JSON OBJETIVO → VALIDACIÓN DE CONTRATO → DSL-DAG EXISTENTE → COLA/CLAIM EXISTENTE → OP EJECUTABLE → RESULTADO INSTRUMENTAL → RECIBO/CHECKPOINT → FICHA → [SIGUE | HECHO | BLOQUEADO] → AUDITOR EXISTENTE → UNA RESPUESTA FINAL`.

### Responsabilidad por componente

| Componente | Responsabilidad | Prohibido |
|---|---|---|
| Router/Harness | ruteo, transporte, presupuesto, truncado y herramientas expuestas | cambio de código por este parche |
| Ficha Qwen 1/2/3 | identidad, prompt incremental, formato JSON, llamada al motor existente | ejecutar shell desde texto libre |
| `system_core.md` | reglas globales ya presentes | reemplazar o duplicar |
| `motor_objetivo.py` | vuelta actual, checkpoints, progreso, estatus, límites | tratar continuación legítima como fallo |
| DSL-DAG/scheduler actual | dependencias, claim, cola, reintentos y transiciones | segundo DAG paralelo |
| Operaciones tipadas | ejecutar con herramientas aprobadas | acceso libre por `exec` |
| Auditor | validar efecto real y evidencia antes de cerrar | creer `"estado":"hecho"` sin prueba |

### Máquina de estados aconsejada

`PENDIENTE → EJECUTANDO → SIGUE_CON_PROGRESO → CHECKPOINT → EJECUTANDO → HECHO_VERIFICABLE → AUDITORÍA → CERRADO`.

Desvíos: `ERROR_REAL → DIAGNOSTICAR → CORREGIR → RETRY_CON_PRESUPUESTO`; `SIN_PROGRESO → GUARDIA/ESCALAMIENTO`; `BLOQUEO_DE_PERMISOS → ESPERAR_AUTORIZACIÓN`; `SALIDA_TRUNCADA → RECUPERAR_PARCIAL → SIGUE`, siempre que el contrato del provider aporte parcial íntegro/validable y el presupuesto lo permita.

**Una continuación normal no consume contador de fallos.** Si el modelo dice `sigue` pero no hay cambio comprobable en recibo, tarea, archivo o checkpoint, no contarla automáticamente como progreso: comparar fingerprint/huella de progreso. Nunca permitir vueltas infinitas. Respetar el presupuesto actual; verificar antes de adoptar 50 vueltas por defecto que el límite global del proyecto lo admite. `n-predict=-1` en un servidor no significa ejecución infinita sin control.

### Estructura de salida para la vuelta de una ficha (propuesta)

```json
{
  "tarea_id": "T03",
  "estado": "sigue",
  "nota_siguiente": "Archivo creado; falta leer y comprobar el test X",
  "operaciones_realizadas": ["op-T03-001"],
  "receipt_ids": ["receipt-T03-001"],
  "fallos": 0,
  "continuaciones": 1,
  "evidencia": [],
  "requiere_auditoria": true
}
```

**No aceptar estos campos como prueba por sí mismos.** `receipt_ids` se deben contrastar con los recibos emitidos por el ejecutor real, con ID y hash ligados a una operación concreta. `fallos` y `continuaciones` deben calcularlos los componentes deterministas, no confiar en valores escritos por Qwen.

### Delta corto del SYSTEM existente — NO segundo system prompt

```text
[CONTINUIDAD DE EJECUCIÓN — ANEXO A LA FICHA]
Ejecuta la tarea actual usando las herramientas autorizadas.
Para cada acción, espera resultado instrumental y confirma evidencia.
Si no está terminada y hubo progreso verificable, estado="sigue".
En nota_siguiente indica el siguiente paso exacto, el último recibo y la validación pendiente.
No repitas mutaciones ya confirmadas; consulta el checkpoint antes de reintentar.
Si falla algo: error real → causa → cambio concreto → reintento → verificación.
Solo estado="hecho" cuando la tarea está cumplida y el auditor dispone de evidencia.
Usa estado="bloqueado" únicamente ante un impedimento real no resoluble autónomamente.
No emitas respuesta final del chat durante vueltas internas.
```

**Diferencia crucial:** las publicaciones de Ricardo acreditan trabajo por fases y verificación, pero **este texto del delta no es un prompt literal publicado por Ricardo**; está redactado para tu formato de ficha. Tampoco atribuir a Ricardo la implementación de `motor_objetivo.py`.

### Manejo de salidas truncadas

El informe de investigación profunda que aportó el usuario describe un `GAP_OUTPUT_TRUNCATED`, `salidas_parciales`, `loop_salida_privada` y manejo de `finish_reason=length` en su Router. **No he inspeccionado aquí el estado actual de esos archivos privados**: Claude debe comprobar estos nombres y semánticas en la rama vigente antes de editar. No confundir dos tipos de continuación:

- `continuación del provider` = reconstruir una respuesta técnica cortada, dentro del presupuesto del Harness.
- `continuación de objetivo` = nueva vuelta de trabajo con estado/tarea/recibos, gestionada por `motor_objetivo.py`.

Mantener ambas capas desacopladas. No cerrar por el simple hecho de alcanzar un límite de tokens. Nunca ejecutar JSON incompleto truncado o parcialmente parseado.

---

